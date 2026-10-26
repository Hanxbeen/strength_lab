"""Database-backed research programmes. Explicit source selection, never automatic enrollment."""
import json
from typing import Optional
import os
import urllib.request
import urllib.error
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from .repository import CatalogUnavailable
from .workout_api import owner, store, execute
from . import coaching_store
from .programme_access import availability, authorize, apply_to_readiness

def internal_access(user):
    return user in {x.strip() for x in os.environ.get('COACHING_PREVIEW_OWNER_IDS','').split(',') if x.strip()}
from research_engine.programme_dispatch import validate_source, make_instance, prepare, exercises, max_exercises
from research_engine.core import digest, InvalidProgramme
from research_engine.workout import require

router=APIRouter(prefix='/v3')

def catalog():
    base=os.environ.get('SUPABASE_URL','').rstrip('/')
    key=os.environ.get('SUPABASE_PUBLISHABLE_KEY','')
    if not base.startswith('https://') or not key:raise CatalogUnavailable('Database not configured')
    req=urllib.request.Request(base+'/rest/v1/rpc/coaching_programme_catalog_v5',data=b'{}',method='POST',
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
        definition=source['definition']
        result=preview(definition,request.dict(),db.maxes(user),availability(definition,user in allowed)['can_request_start'])
        return apply_to_readiness(result,definition,request.profile,user in allowed)
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
    load_choices:dict[str,dict]=Field(default_factory=dict)

@router.get('/research-programmes')
def programmes(user=Depends(owner)):
    def action():
        from .programme_options import options
        result = catalog()
        allowed = {x.strip() for x in os.environ.get('COACHING_PREVIEW_OWNER_IDS','').split(',') if x.strip()}
        for item in result['items']:
            decision=availability(item['definition'],user in allowed)
            item['routine_options'] = options(item, decision['can_request_start'])
            for row in item['routine_options']:
                row['access']=decision['access']
                row['availability']=decision
        return result
    return execute(action)

@router.post('/programme-instances')
def create(request:InstanceInput,user=Depends(owner),db=Depends(store)):
    def action():
        source=next((x for x in catalog()['items'] if x['source_id']==request.source_id and x['version']==request.source_version),None)
        if source is None:raise InvalidProgramme('SOURCE_VERSION_UNAVAILABLE')
        require(source['status']=='research_preview','SOURCE_SUSPENDED')
        access_decision=authorize(source['definition'],request.profile,internal_access(user))
        expected=set(max_exercises(source['definition']))
        require(set(request.max_record_ids)<=expected if source['definition'].get('adapter_version') in ('novice-sbd-choice-v1','petrizzo-2018-v1')
                else set(request.max_record_ids)==expected,'MAX_REFERENCES_REQUIRED')
        records=db.maxes(user);selected=[]
        for eid,rid in request.max_record_ids.items():
            record=next((r for r in records if r['id']==rid and r['exercise_id']==eid),None)
            require(record is not None,'MAX_RECORD_NOT_FOUND');selected.append(record)
        snapshot=make_instance(source['definition'],request.arm,request.profile,selected,request.setup,request.created_at)
        snapshot['access_decision']=access_decision
        return {'instance_id':request.id,'instance':coaching_store.save_instance(db,user,request.id,snapshot)}
    return execute(action)

@router.get('/programme-instances')
def list_programmes(limit:int=Query(default=20,ge=1,le=100),after:Optional[str]=Query(default=None,max_length=100),
                    user=Depends(owner),db=Depends(store)):
    return execute(lambda:coaching_store.list_instances(db,user,limit,after))

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
        novice=value['source'].get('adapter_version') in ('novice-sbd-choice-v1','petrizzo-2018-v1')
        require(not request.initial_rpe_loads_kg if novice else not request.initial_loads_kg,'UNEXPECTED_LOAD_INPUT')
        require(novice or not request.load_choices,'UNEXPECTED_LOAD_CHOICE')
        loads=request.initial_loads_kg if novice else request.initial_rpe_loads_kg
        # Retry an existing request without re-reading a mutable current catalogue.
        prior=next((h for h in history if h['week']==request.week and h['day']==request.day),None)
        if prior:
            require(prior['workout_id']==request.workout_id,'SESSION_ALREADY_STARTED')
            require(prior['snapshot']['started_at']==request.started_at,'START_REQUEST_CONFLICT')
            if novice:
                require(prior['snapshot']['coaching']['initial_loads_kg']==loads,'START_REQUEST_CONFLICT')
                require(prior['snapshot']['coaching'].get('load_choices',{})==request.load_choices,'START_REQUEST_CONFLICT')
            elif value['source'].get('adapter_version')=='metd-2021-v1':
                require(prior['snapshot']['coaching']['initial_rpe_loads_kg']==request.initial_rpe_loads_kg,'START_REQUEST_CONFLICT')
            elif value['arm']=='RPEG':
                initial={r['exercise_id']:r['weight_kg'] for r in prior['snapshot']['session']['sets']}
                require(initial==request.initial_rpe_loads_kg,'START_REQUEST_CONFLICT')
            else:
                require(not request.initial_rpe_loads_kg,'START_REQUEST_CONFLICT')
            return db.get(user,request.workout_id)
        matching=next((x for x in catalog()['items'] if x['source_id']==value['source']['id']
                       and x['version']==digest(value['source'])),None)
        require(matching is not None and matching['status']=='research_preview','SOURCE_UNAVAILABLE_OR_SUSPENDED')
        decision=authorize(value['source'],value['profile'],internal_access(user))
        snapshot=prepare(value,request.week,request.day,request.started_at,history,loads)
        snapshot['access_decision']=decision
        if novice:
            from research_engine.novice import record_load_choices
            snapshot=record_load_choices(snapshot,request.load_choices,history)
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

# User-facing catalogue and non-persisting first-session preview.
class RoutinePreviewInput(ReadinessInput):
    initial_loads_kg:dict[str,float]=Field(default_factory=dict)
    initial_rpe_loads_kg:dict[str,float]=Field(default_factory=dict)

@router.get('/routines')
def routines(experience:Optional[str]=Query(default=None,pattern='^(entry|foundation|trained|experienced)$'),
             user=Depends(owner)):
    def action():
        from .programme_options import options
        from .programme_readiness import required_fields
        from .programme_access import extra_fields
        current=catalog();result=[];all_rows=[];unavailable=[]
        counts=dict(entry=0,foundation=0,trained=0,experienced=0)
        for item in current['items']:
            source=item['definition'];decision=availability(source,internal_access(user))
            if not decision['public_selection'] or item['status']!='research_preview':
                unavailable.append(dict(source_id=item['source_id'],reason=decision['reason'] or 'INTERNAL_ADAPTATION'))
                continue
            rows=options(item,True)
            counts[decision['experience_context']]+=len(rows)
            for row in rows:
                row['access']=decision['access'];row['availability']=decision
                row['definition']=source
                row['input_contract']={
                    'required_fields':[group+'.'+field for group,field in required_fields(source,row['arm'])]
                                      +['profile.'+field for field in extra_fields(source)],
                    'max_record_ids_required':source['adapter_version'] not in ('novice-sbd-choice-v1','petrizzo-2018-v1'),
                    'max_record_exercise_ids':list(max_exercises(source)),
                    'preview_endpoint':'/v3/routines/preview',
                    'create_endpoint':'/v3/programme-instances',
                    'selection':{'source_id':item['source_id'],'source_version':item['version'],'arm':row['arm']}}
                all_rows.append(row)
                if not experience or experience==decision['experience_context']:result.append(row)
        from .routine_coverage import report
        return {'schema_version':'routine-selection-v1','routines':result,'unavailable_adaptations':unavailable,
            'supply_audit':report(all_rows),
            'coverage':{level:{'state':'explicit_selection' if count else 'not_ready','option_count':count,
                'reason':('TECHNIQUE_AND_FIRST_LOAD_PATH_INCOMPLETE' if level=='entry' else 'NO_RELEASED_CATALOGUE_DATA') if not count else None}
                for level,count in counts.items()},
            'recommendation_status':'not_assessed','scientific_approval':False}
    return execute(action)

@router.post('/routines/preview')
def routine_preview(request:RoutinePreviewInput,user=Depends(owner),db=Depends(store)):
    def action():
        from .programme_readiness import preview
        item=next((x for x in catalog()['items'] if x['source_id']==request.source_id
                   and x['version']==request.source_version),None)
        require(item is not None and item['status']=='research_preview','SOURCE_VERSION_UNAVAILABLE')
        source=item['definition'];records=db.maxes(user);internal=internal_access(user)
        result=apply_to_readiness(preview(source,request.model_dump(),records,
            availability(source,internal)['can_request_start']),source,request.profile,internal)
        result.update(persisted=False,session_preview=None,session_status='blocked',session_blocking_code=None)
        if not result['can_create_instance']:return result
        selected=[r for r in records if request.max_record_ids.get(r['exercise_id'])==r['id']]
        instance=make_instance(source,request.arm,request.profile,selected,request.setup,request.created_at)
        manual=source['adapter_version'] in ('novice-sbd-choice-v1','petrizzo-2018-v1')
        require(not request.initial_rpe_loads_kg if manual else not request.initial_loads_kg,'UNEXPECTED_LOAD_INPUT')
        loads=request.initial_loads_kg if manual else request.initial_rpe_loads_kg
        try:
            snapshot=prepare(instance,1,1,request.created_at,[],loads)
        except InvalidProgramme as error:
            result.update(session_status='needs_session_input',session_blocking_code=str(error))
            return result
        result.update(session_status='ready',session_preview=snapshot,
            start_request={'week':1,'day':1,'started_at':request.created_at,
                'initial_loads_kg':request.initial_loads_kg,'initial_rpe_loads_kg':request.initial_rpe_loads_kg},
            revalidation_required_at_start=True)
        return result
    return execute(action)
