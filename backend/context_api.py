"""Authenticated, explicitly version-selected evidence explanations; never changes a workout."""
import json
import os
import urllib.request
from typing import Literal
from fastapi import APIRouter, Depends
from .repository import CatalogUnavailable
from .workout_api import owner, store, execute
from research_engine.core import digest, InvalidProgramme
from research_engine.context_guidance import validate_packet, explain

router = APIRouter(prefix='/v3')

def context_catalog():
    base = os.environ.get('SUPABASE_URL','').rstrip('/')
    key = os.environ.get('SUPABASE_PUBLISHABLE_KEY','')
    if not base.startswith('https://') or not key:
        raise CatalogUnavailable('Database not configured')
    request = urllib.request.Request(base+'/rest/v1/rpc/coaching_context_catalog',
        data=b'{}', method='POST', headers={'apikey':key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.load(response)
        if result['schema_version'] != 1 or not isinstance(result['items'],list):
            raise ValueError('Schema')
        for item in result['items']:
            validate_packet(item['definition'])
            if (item['version'] != digest(item['definition']) or item['id'] != item['definition']['id']
                    or item['status'] not in ('research_preview','suspended')):
                raise ValueError('Version or status')
        return result
    except (OSError, ValueError, KeyError, TypeError, AttributeError, InvalidProgramme) as error:
        raise CatalogUnavailable('Context evidence unavailable') from error

@router.get('/context-evidence')
def evidence(user=Depends(owner)):
    return execute(context_catalog)

@router.get('/workouts/{workout_id}/evidence')
def workout_evidence(workout_id: str, evidence_version: str,
                     topic: Literal['auto','rest','volume','deload']='auto',
                     user=Depends(owner), db=Depends(store)):
    def action():
        # Check ownership before querying research, including when research is unavailable.
        record = db.get(user, workout_id)
        item = next((x for x in context_catalog()['items'] if x['version'] == evidence_version
                     and x['status'] == 'research_preview'), None)
        if item is None: raise CatalogUnavailable('Evidence version unavailable or suspended')
        return {'workout_id':workout_id, **explain(record['execution'], item['definition'], topic)}
    return execute(action)
