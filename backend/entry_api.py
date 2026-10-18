"""Authenticated guided learning API; separate from strength routine supply counts."""
from fastapi import APIRouter,Depends,Query
from pydantic import BaseModel,Field
from .workout_api import owner,store,execute,EventInput
from .workout_store import replay
from research_engine import entry_practice
from research_engine.workout import require
import json

router=APIRouter(prefix='/v3/entry')

class PracticeInput(BaseModel):
    id:str=Field(min_length=1,max_length=100)
    lesson_id:str
    version:str
    started_at:str
    profile:dict=Field(default_factory=dict)
    setup:dict=Field(default_factory=dict)

@router.get('/pathway')
def pathway(user=Depends(owner)):
    return entry_practice.catalogue()

@router.post('/practices')
def start(request:PracticeInput,user=Depends(owner),db=Depends(store)):
    return execute(lambda:db.create(user,request.id,entry_practice.create(
        request.lesson_id,request.version,request.profile,request.setup,request.started_at)))

def checked(db,user,id):
    record=db.get(user,id)
    require(record['execution']['policy_version']==entry_practice.POLICY,'NOT_ENTRY_PRACTICE')
    return record

@router.get('/practices')
def list_practices(limit:int=Query(20,ge=1,le=100),after:str=Query('',max_length=100),
                   user=Depends(owner),db=Depends(store)):
    def action():
        # Bound query and portable SQL; all rows are owner-scoped under the existing RLS.
        with db.connect() as c:
            rows=c.execute('SELECT id,snapshot,events FROM execution_workouts WHERE owner=? AND id>? ORDER BY id LIMIT ?',
                           (user,after,limit+1)).fetchall()
        items=[]
        for id,snapshot,events in rows[:limit]:
            snapshot=json.loads(snapshot)
            if snapshot.get('policy_version')==entry_practice.POLICY:
                items.append({'id':id,'execution':replay(snapshot,json.loads(events))})
        return {'items':items,'next_cursor':rows[limit-1][0] if len(rows)>limit else None}
    return execute(action)

@router.get('/practices/{id}')
def get(id:str,user=Depends(owner),db=Depends(store)):
    return execute(lambda:checked(db,user,id))

@router.post('/practices/{id}/events')
def event(id:str,request:EventInput,user=Depends(owner),db=Depends(store)):
    def action():
        checked(db,user,id)
        return db.append(user,id,request.expected_revision,request.event)
    return execute(action)

@router.post('/practices/{id}/reconcile')
def reconcile(id:str,user=Depends(owner),db=Depends(store)):
    def action():
        checked(db,user,id)
        return db.reconcile_inactivity(user,id)
    return execute(action)
