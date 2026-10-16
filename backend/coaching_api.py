"""Database-backed research programmes. Explicit source selection, never automatic enrollment."""
import json
from typing import Optional
import os
import urllib.request
import urllib.error
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from .repository import CatalogUnavailable
from .workout_api import owner, store, execute
from . import coaching_store
from research_engine.programme_dispatch import validate_source, make_instance, prepare, exercises
from research_engine.core import digest, InvalidProgramme
from research_engine.workout import require

router=APIRouter(prefix='/v3')

def catalog():
    base=os.environ.get('SUPABASE_URL','').rstrip('/')
    key=os.environ.get('SUPABASE_PUBLISHABLE_KEY','')
    if not base.startswith('https://') or not key:raise CatalogUnavailable('Database not configured')
    req=urllib.request.Request(base+'/rest/v1/rpc/coaching_programme_catalog_v2',data=b'{}',method='POST',
        headers={'apikey':key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=10) as response:result=json.load(response)
        if result.get('schema_version')!=3 or not isinstance(result.get('items'),list):raise ValueError('Schema')
        result['items']=[item for item in result['items'] if item.get('status')=='research_preview']
        for item in result['items']:
            if item['version']!=digest(item['definition']):raise ValueError('Version')
            validate_source(item['definition'])
        return result
    except (OSError,ValueError,KeyError,TypeError) as e:raise CatalogUnavailable('Evidence catalog unavailable') from e

def require_internal_preview(user):
    # Server-owned allowlist; request acknowledgement is not release authorization.
    allowed = {x.strip() for x in os.environ.get('COACHING_PREVIEW_OWNER_IDS','').split(',') if x.strip()}
    if user not in allowed:
        raise HTTPException(403, detail='RESEARCH_PREVIEW_NOT_RELEASED')

class ReadinessInput(BaseModel):
    source_id:str
    source_version:str
    arm:str
    created_at:str
    profile:dict=Field(default_factory=dict)
    setup:dict=Field(default_factory=dict)
    max_record_ids:dict[str,str]=Field(default_factory=dict)

@router.post('/programme-readiness')
def readiness(request:ReadinessInput,user=Depends(owner),db=Depends(store)):
    from .programme_readiness import preview
    def action():
        source=next((x for x in catalog()['items'] if x['source_id']==request.source_id and x['version']==request.source_version),None)
        if source is None:raise InvalidProgramme('SOURCE_VERSION_UNAVAILABLE')
        require(source['status']=='research_preview','SOURCE_SUSPENDED')
        allowed={x.strip() for x in os.environ.get('COACHING_PREVIEW_OWNER_IDS','').split(',') if x.strip()}
        return preview(source['definition'],request.dict(),db.maxes(user),user in allowed)
    return execute(action)

@router.get('/programme-instances/{instance_id}/next-session')
def next_programme_session(instance_id:str,at:str,user=Depends(owner),db=Depends(store)):
    from .programme_readiness import next_session
    from .programme_evaluation import list_evaluations
    def action():
        instance=coaching_store.instance(db,user,instance_id)
        return next_session(instance,coaching_store.history(db,user,instance_id),list_evaluations(db,user,instance_id),at)
    return execute(action)

class InstanceInput(BaseModel):
    id:str=Field(min_length=1,max_length=100)
    source_id:str
    source_version:str
    arm:str
    created_at:str
    profile:dict
    max_record_ids:dict[str,str]
    setup:dict

class SessionInput(BaseModel):
    workout_id:str=Field(min_length=1,max_length=100)
    week:int=Field(ge=1,le=12)
    day:int=Field(ge=1,le=3)
    started_at:str
    initial_rpe_loads_kg:dict[str,float]=Field(default_factory=dict)
    initial_loads_kg:dict[str,float]=Field(default_factory=dict)

@router.get('/research-programmes')
def programmes(user=Depends(owner)):
    return execute(catalog)

@router.post('/programme-instances')
def create(request:InstanceInput,user=Depends(owner),db=Depends(store)):
    require_internal_preview(user)
    def action():
        source=next((x for x in catalog()['items'] if x['source_id']==request.source_id and x['version']==request.source_version),None)
        if source is None:raise InvalidProgramme('SOURCE_VERSION_UNAVAILABLE')
        require(source['status']=='research_preview','SOURCE_SUSPENDED')
        expected=set(exercises(source['definition']))
        require(set(request.max_record_ids)<=expected if source['definition'].get('adapter_version')=='novice-sbd-choice-v1'
                else set(request.max_record_ids)==expected,'MAX_REFERENCES_REQUIRED')
        records=db.maxes(user);selected=[]
        for eid,rid in request.max_record_ids.items():
            record=next((r for r in records if r['id']==rid and r['exercise_id']==eid),None)
            require(record is not None,'MAX_RECORD_NOT_FOUND');selected.append(record)
        snapshot=make_instance(source['definition'],request.arm,request.profile,selected,request.setup,request.created_at)
        return {'instance_id':request.id,'instance':coaching_store.save_instance(db,user,request.id,snapshot)}
    return execute(action)

@router.get('/programme-instances/{instance_id}')
def get(instance_id:str,user=Depends(owner),db=Depends(store)):
    from .programme_evaluation import list_evaluations
    return execute(lambda:{'instance_id':instance_id,'instance':coaching_store.instance(db,user,instance_id),
                           'evaluations':list_evaluations(db,user,instance_id),
                           'history':[{k:v for k,v in h.items() if k not in ('snapshot','events')}
                                      for h in coaching_store.history(db,user,instance_id)]})

@router.post('/programme-instances/{instance_id}/workouts')
def start(instance_id:str,request:SessionInput,user=Depends(owner),db=Depends(store)):
    def action():
        value=coaching_store.instance(db,user,instance_id)
        history=coaching_store.history(db,user,instance_id)
        novice=value['source'].get('adapter_version')=='novice-sbd-choice-v1'
        require(not request.initial_rpe_loads_kg if novice else not request.initial_loads_kg,'UNEXPECTED_LOAD_INPUT')
        loads=request.initial_loads_kg if novice else request.initial_rpe_loads_kg
        # Retry an existing request without re-reading a mutable current catalogue.
        prior=next((h for h in history if h['week']==request.week and h['day']==request.day),None)
        if prior:
            require(prior['workout_id']==request.workout_id,'SESSION_ALREADY_STARTED')
            require(prior['snapshot']['started_at']==request.started_at,'START_REQUEST_CONFLICT')
            if novice:
                require(prior['snapshot']['coaching']['initial_loads_kg']==loads,'START_REQUEST_CONFLICT')
            elif value['source'].get('adapter_version')=='metd-2021-v1':
                require(prior['snapshot']['coaching']['initial_rpe_loads_kg']==request.initial_rpe_loads_kg,'START_REQUEST_CONFLICT')
            elif value['arm']=='RPEG':
                initial={r['exercise_id']:r['weight_kg'] for r in prior['snapshot']['session']['sets']}
                require(initial==request.initial_rpe_loads_kg,'START_REQUEST_CONFLICT')
            else:
                require(not request.initial_rpe_loads_kg,'START_REQUEST_CONFLICT')
            return db.get(user,request.workout_id)
        require_internal_preview(user)
        matching=next((x for x in catalog()['items'] if x['source_id']==value['source']['id']
                       and x['version']==digest(value['source'])),None)
        require(matching is not None and matching['status']=='research_preview','SOURCE_UNAVAILABLE_OR_SUSPENDED')
        snapshot=prepare(value,request.week,request.day,request.started_at,history,loads)
        return coaching_store.start(db,user,instance_id,request.workout_id,request.week,request.day,snapshot)
    return execute(action)

class EvaluationInput(BaseModel):
    id:str=Field(min_length=1,max_length=100)
    at:str
    outcome:str
    supersedes_id:Optional[str]=None
    post_max_record_ids:dict[str,str]=Field(default_factory=dict)
    comparison_conditions:dict[str,str]=Field(default_factory=dict)

@router.post('/programme-instances/{instance_id}/evaluations')
def evaluate(instance_id:str,request:EvaluationInput,user=Depends(owner),db=Depends(store)):
    from .programme_evaluation import evaluate as operation
    return execute(lambda:operation(db,user,instance_id,request.model_dump()))
