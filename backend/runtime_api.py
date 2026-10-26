"""Authenticated readiness: dependency reads, never synthetic user writes."""
import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from .workout_api import owner, store
from .workout_store import StorageUnavailable

router = APIRouter(prefix='/v3')

@router.get('/runtime-readiness')
def readiness(user=Depends(owner), db=Depends(store)):
    from .coaching_api import routines
    checks = {'authentication': 'verified', 'catalogue': 'unavailable', 'ledger': 'unavailable'}
    coverage = {}
    try:
        data = routines(user=user, experience=None)
        coverage = data['coverage']
        checks['catalogue'] = ('ready' if data['supply_audit']['all_levels_data_ready']
                               else 'incomplete')
    except HTTPException as error:
        if error.status_code != 503:
            raise
    try:
        # Exercise every runtime table under the authenticated owner's role, without reading payloads.
        with db.connect() as connection:
            for table in ('execution_maxes', 'execution_workouts', 'coaching_instances',
                          'coaching_sessions', 'coaching_evaluations'):
                connection.execute('SELECT 1 FROM '+table+' WHERE owner=? LIMIT 0', (user,))
        checks['ledger'] = 'readable'
    except (StorageUnavailable, sqlite3.Error):
        pass
    ready = checks['catalogue'] == 'ready' and checks['ledger'] == 'readable'
    return JSONResponse(status_code=200 if ready else 503, content={
        'schema_version': 'runtime-readiness-v1', 'ready': ready, 'checks': checks,
        'storage': 'postgres' if getattr(db, 'schema_managed', False) else 'local_sqlite',
        'coverage': coverage,
        'write_verified': False, 'client_execution_verified': False,
    })
