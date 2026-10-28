"""DB-backed entry definitions; frozen owner-scoped learning observations."""
import json,os,urllib.request,urllib.error
from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from .workout_api import owner,store,execute,EventInput
from .repository import CatalogUnavailable
from research_engine import entry_learning as learning
from research_engine.core import digest
from research_engine.workout import require
from .workout_store import replay
VERSION='a3ef347812b78e8577a740a8883a1f32bf9532062229d49462b94050a00ce593'
router=APIRouter(prefix='/v3/entry')
def catalogue():
    base=os.environ.get('SUPABASE_URL','').rstrip('/');key=os.environ.get('SUPABASE_PUBLISHABLE_KEY','')
    if not base.startswith('https://') or not key:raise CatalogUnavailable('Database not configured')
    req=urllib.request.Request(base+'/rest/v1/rpc/coaching_learning_catalog_v1',data=b'{}',method='POST',
        headers={'apikey':key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=10) as response:data=json.load(response)
        result=[]
        for item in data['items']:
            if item['status']!='research_preview':continue
            if item['source_id']!=learning.ID or item['version']!=VERSION:continue
            if digest(item['definition'])!=VERSION:raise ValueError('Version')
            learning.validate_source(item['definition']);result.append(item)
        return dict(schema_version='entry-catalog-v2',items=result)
    except (urllib.error.URLError,ValueError,KeyError,TypeError,TimeoutError) as e:
        raise CatalogUnavailable('Entry catalogue unavailable') from e
class LearningInput(BaseModel):
    id:str=Field(min_length=1,max_length=100)
    source_id:str
    source_version:str
    started_at:str
    profile:dict=Field(default_factory=dict)
    setup:dict=Field(default_factory=dict)
@router.get('/learning-paths')
def paths(user=Depends(owner)):
    def action():
        from copy import deepcopy
        from .experience_content import entry_content
        data=deepcopy(catalogue())
        for item in data['items']:item['experience']=entry_content(item['definition'])
        return data
    return execute(action)
@router.post('/learning-sessions')
def start(request:LearningInput,user=Depends(owner),db=Depends(store)):
    def action():
        item=next((x for x in catalogue()['items'] if x['source_id']==request.source_id and x['version']==request.source_version),None)
        require(item is not None,'ENTRY_VERSION_UNAVAILABLE')
        return db.create(user,request.id,learning.create(item['definition'],request.source_version,request.profile,request.setup,request.started_at))
    return execute(action)
def checked(db,user,id):
    result=db.get(user,id);require(result['execution']['policy_version']==learning.POLICY,'NOT_ENTRY_LEARNING')
    return result
@router.get('/learning-sessions')
def listing(limit:int=Query(20,ge=1,le=100),after:str=Query('',max_length=100),user=Depends(owner),db=Depends(store)):
    def action():
        with db.connect() as c:
            rows=c.execute('SELECT id,snapshot,events FROM execution_workouts WHERE owner=? AND id>? ORDER BY id LIMIT ?',(user,after,limit+1)).fetchall()
        items=[]
        for id,snapshot,events in rows[:limit]:
            snap=json.loads(snapshot)
            if snap.get('policy_version')==learning.POLICY:items.append(dict(id=id,execution=replay(snap,json.loads(events))))
        return dict(items=items,next_cursor=rows[limit-1][0] if len(rows)>limit else None)
    return execute(action)
@router.get('/learning-sessions/{id}')
def get(id:str,user=Depends(owner),db=Depends(store)):return execute(lambda:checked(db,user,id))
@router.post('/learning-sessions/{id}/events')
def event(id:str,request:EventInput,user=Depends(owner),db=Depends(store)):
    def action():
        checked(db,user,id)
        return db.append(user,id,request.expected_revision,request.event)
    return execute(action)
@router.post('/learning-sessions/{id}/reconcile')
def reconcile(id:str,user=Depends(owner),db=Depends(store)):
    def action():
        checked(db,user,id);return db.reconcile_inactivity(user,id)
    return execute(action)
