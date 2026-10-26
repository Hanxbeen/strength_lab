"""Authenticated v2 execution API; source catalog and personal records stay separate."""
import json
import os
import sqlite3
import urllib.request
import urllib.error
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from .source_repository import source_catalog
from .repository import CatalogUnavailable
from .workout_store import WorkoutStore, Conflict, StorageUnavailable
from .workout_result import project
from research_engine.core import compile_programme, InvalidProgramme
from research_engine.workout import create_workout

router = APIRouter(prefix='/v2')

def owner(authorization: str = Header(default='')):
    if not authorization.startswith('Bearer ') or len(authorization) > 8192:
        raise HTTPException(401, detail='로그인이 필요해요.')
    base = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_PUBLISHABLE_KEY', '')
    if not base.startswith('https://') or not key: raise HTTPException(503, detail='인증 서버 설정이 필요해요.')
    request = urllib.request.Request(base + '/auth/v1/user', headers={'apikey': key, 'Authorization': authorization})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            value = json.loads(response.read())
            if not isinstance(value, dict) or not isinstance(value.get('id'), str):
                raise ValueError('Invalid authentication response')
            return str(UUID(value['id']))
    except urllib.error.HTTPError as error:
        raise HTTPException(401 if error.code in (401,403) else 503, detail='로그인 상태를 확인하지 못했어요.')
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
        raise HTTPException(503, detail='로그인 상태를 확인하지 못했어요.')

def store(user=Depends(owner)):
    dsn = os.environ.get('WORKOUT_POSTGRES_DSN')
    if dsn:
        from .postgres_store import PostgresWorkoutStore
        return PostgresWorkoutStore(dsn,user,os.environ.get('WORKOUT_DB_SSLROOTCERT','system'))
    if os.environ.get('VERCEL') or os.environ.get('MUGEMUGE_ENV', '').lower() in ('production', 'staging'):
        raise HTTPException(503, detail='운영 운동 기록 저장소가 설정되지 않았어요.')
    path = os.environ.get('WORKOUT_DATABASE_PATH')
    if not path or not os.path.isabs(path): raise HTTPException(503, detail='운동 기록 저장소가 설정되지 않았어요.')
    try: return WorkoutStore(path)
    except (OSError, sqlite3.Error): raise HTTPException(503, detail='운동 기록 저장소에 연결하지 못했어요.')

def execute(operation):
    try: return operation()
    except Conflict as error: raise HTTPException(409, detail=str(error))
    except KeyError: raise HTTPException(404, detail='기록을 찾지 못했어요.')
    except InvalidProgramme as error: raise HTTPException(422, detail={'code': str(error), 'action': 'check_input'})
    except (TypeError, ValueError, AttributeError): raise HTTPException(422, detail={'code': 'INVALID_INPUT', 'action': 'check_input'})
    except (sqlite3.Error, StorageUnavailable): raise HTTPException(503, detail='기록을 저장하지 못했어요. 같은 요청 ID로 다시 시도해 주세요.')
    except CatalogUnavailable: raise HTTPException(503, detail='원문 운동 구성을 불러오지 못했어요.')

class MaxInput(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    exercise_id: str = Field(min_length=1, max_length=100)
    value: float
    unit: str
    kind: str
    measured_at: str

class StartInput(BaseModel):
    workout_id: str = Field(min_length=1, max_length=100)
    programme_id: str
    programme_version: str
    session_id: str
    started_at: str
    profile: dict
    setup: dict

class EventInput(BaseModel):
    expected_revision: int = Field(ge=0)
    event: dict

@router.post('/workout-readiness')
def readiness(request: StartInput, user=Depends(owner), db=Depends(store)):
    """Structured setup checklist, followed by the same authoritative start validation."""
    def action():
        item = next((p for p in source_catalog()['items'] if p['programme_id'] == request.programme_id
                     and p['programme_version'] == request.programme_version), None)
        if item is None: raise Conflict('PROGRAMME_VERSION_UNAVAILABLE')
        definition = item['definition']; choices = request.setup; issues = []
        bundle = compile_programme(definition)
        session = next((s for s in bundle['sessions'] if s['id'] == request.session_id), None)
        if session is None: raise InvalidProgramme('UNKNOWN_SESSION')
        first = session['week'] == 1 and session['ordinal'] == 1
        records = db.maxes(user)
        for exercise in definition['exercises']:
            eid = exercise['id']; load = exercise['load']
            if first and load['kind'] == 'initial_percent_1rm':
                rid = choices.get('max_record_ids', {}).get(eid)
                if not any(r['id'] == rid and r['exercise_id'] == eid and r['kind'] == 'measured' for r in records):
                    issues.append({'code':'MEASURED_MAX_REQUIRED','exercise_id':eid,'action':'register_or_select_max',
                                   'text':'이 동작의 측정 1RM을 선택해 주세요. 다른 동작의 기록은 대신 쓰지 않아요.'})
            else:
                if eid not in choices.get('working_loads_kg', {}):
                    issues.append({'code':'WORKING_LOAD_REQUIRED','exercise_id':eid,'action':'choose_load',
                                   'text':'이 동작에 사용할 중량을 입력해 주세요.','effort_target':load})
                if first and load['kind'] == 'repetition_maximum' and choices.get('measured_rm_reps', {}).get(eid) != load['initial_rm_test_reps']:
                    issues.append({'code':'RM_RECORD_REQUIRED','exercise_id':eid,'action':'enter_rm_record',
                                   'text':'원 연구에서 사용한 반복 최대 중량 기록이 필요해요.','reps':load['initial_rm_test_reps']})
        for key, text in [('warmup','준비운동을 어떻게 할지 정해 주세요.'),('exercise_order','운동 순서를 확인해 주세요.'),
                          ('between_exercise_rest_seconds','동작 사이 휴식 시간을 정해 주세요.')]:
            if not choices.get(key): issues.append({'code':'SETUP_REQUIRED','field':key,'action':'complete_setup','text':text})
        if issues: return {'ready':False,'issues':issues,'policy_version':'execution-ledger-v1'}
        try:
            create_workout(bundle,request.session_id,request.profile,choices,records,request.started_at)
        except InvalidProgramme as error:
            return {'ready':False,'issues':[{'code':str(error),'action':'review_setup','text':'연구 대상 조건과 입력값을 다시 확인해 주세요.'}]}
        return {'ready':True,'issues':[],'next_action':'start_workout'}
    return execute(action)

@router.post('/max-records')
def register_max(request: MaxInput, user=Depends(owner), db=Depends(store)):
    return execute(lambda: db.register_max(user, request.model_dump()))

@router.get('/max-records')
def list_maxes(user=Depends(owner), db=Depends(store)):
    return execute(lambda: {'items': db.maxes(user)})

@router.post('/workouts')
def start(request: StartInput, user=Depends(owner), db=Depends(store)):
    def action():
        items = source_catalog()['items']
        item = next((p for p in items if p['programme_id'] == request.programme_id and p['programme_version'] == request.programme_version), None)
        if item is None: raise Conflict('PROGRAMME_VERSION_UNAVAILABLE')
        snapshot = create_workout(compile_programme(item['definition']), request.session_id, request.profile,
                                  request.setup, db.maxes(user), request.started_at)
        return db.create(user, request.workout_id, snapshot)
    return execute(action)

@router.get('/workouts/{workout_id}')
def get(workout_id: str, user=Depends(owner), db=Depends(store)):
    return execute(lambda: db.get(user, workout_id))

@router.post('/workouts/{workout_id}/events')
def append(workout_id: str, request: EventInput, user=Depends(owner), db=Depends(store)):
    return execute(lambda: db.append(user, workout_id, request.expected_revision, request.event))

@router.post('/workouts/{workout_id}/reconcile')
def reconcile(workout_id: str, user=Depends(owner), db=Depends(store)):
    """Call after pending local events sync, on foreground or a lifecycle check."""
    return execute(lambda: project(db.reconcile_inactivity(user, workout_id)))

@router.get('/workouts/{workout_id}/result')
def result(workout_id: str, user=Depends(owner), db=Depends(store)):
    return execute(lambda: project(db.get(user, workout_id)))
