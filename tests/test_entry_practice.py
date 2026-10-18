import copy,tempfile,unittest
from pathlib import Path
from datetime import datetime,timezone
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner,store
from backend.workout_store import WorkoutStore
from research_engine.entry_practice import catalogue,create,replay
from research_engine.core import InvalidProgramme

AT='2026-10-18T09:00:00Z'
class EntryPracticeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'ledger.sqlite'
        self.db=WorkoutStore(self.path);self.user='owner'
        app.dependency_overrides[owner]=lambda:self.user
        app.dependency_overrides[store]=lambda:self.db
        self.client=TestClient(app)
        self.req=dict(id='entry1',lesson_id='squat-pattern',version=catalogue()['version'],
            started_at=AT,profile=dict(age=25,current_pain=False),
            setup=dict(in_person_instructor=True,equipment_checked=True))
    def tearDown(self):
        app.dependency_overrides.clear();self.tmp.cleanup()
    def post(self,path,value,status=200):
        res=self.client.post(path,json=value)
        self.assertEqual(res.status_code,status,res.text);return res.json()
    def test_three_lessons_no_training_dose_or_claim(self):
        result=self.client.get('/v3/entry/pathway').json()
        self.assertEqual(len(result['lessons']),3)
        self.assertFalse(result['automatic_training_unlock'])
        self.assertTrue(all(x is None for x in result['dose'].values()))
    def test_each_lesson_persists_rests_finish_and_owner(self):
        for idx,lesson in enumerate(catalogue()['lessons']):
            req=dict(self.req,id=str(idx),lesson_id=lesson['id'])
            self.post('/v3/entry/practices',req)
            events=[
                dict(id='o',type='practice_observation',at=AT,outcome='tried',reps=2),
                dict(id='r',type='rest_start',at=AT),
                dict(id='e',type='rest_end',at='2026-10-18T09:02:00Z'),
                dict(id='f',type='finish',at='2026-10-18T09:02:00Z',outcome='completed')]
            for rev,event in enumerate(events):
                result=self.post('/v3/entry/practices/'+str(idx)+'/events',
                    dict(expected_revision=rev,event=event))
            self.assertEqual(result['execution']['rests'][0]['elapsed_seconds'],120)
            self.assertFalse(result['execution']['training_unlocked'])
            self.assertFalse(result['execution']['technique_verified'])
            self.db=WorkoutStore(self.path)
            self.assertEqual(self.client.get('/v3/entry/practices/'+str(idx)).json()['execution']['state'],'completed')
            self.assertIsNone(self.client.get('/v2/workouts/'+str(idx)+'/result').json()['charts'])
            self.user='other'
            self.assertEqual(self.client.get('/v3/entry/practices/'+str(idx)).status_code,404)
            self.user='owner'
        self.assertEqual(len(self.client.get('/v3/entry/practices').json()['items']),3)
    def test_missing_instructor_pain_equipment_minor_and_version(self):
        variants=[]
        for key,value in [('in_person_instructor',False),('equipment_checked',False)]:
            v=copy.deepcopy(self.req);v['setup'][key]=value;variants.append(v)
        for key,value in [('age',17),('current_pain',True),('current_pain',None)]:
            v=copy.deepcopy(self.req);v['profile'][key]=value;variants.append(v)
        variants.append(dict(self.req,version='changed'))
        for v in variants:self.post('/v3/entry/practices',v,422)
    def test_pain_and_help_stop_without_training_unlock(self):
        for outcome in ('pain','needs_help'):
            req=dict(self.req,id=outcome);self.post('/v3/entry/practices',req)
            event=dict(id='p',type='practice_observation',at=AT,outcome=outcome)
            result=self.post('/v3/entry/practices/'+outcome+'/events',dict(expected_revision=0,event=event))
            self.assertEqual(result['execution']['state'],'stopped')
            self.assertEqual(result['execution']['next_actions'],['ask_instructor_for_help'])
            self.post('/v3/entry/practices/'+outcome+'/events',dict(expected_revision=1,
                event=dict(id='later',type='practice_observation',at=AT,outcome='tried')),422)
    def test_retries_conflict_and_unknown_not_zero(self):
        self.post('/v3/entry/practices',self.req)
        event=dict(id='o',type='practice_observation',at=AT,outcome='tried')
        path='/v3/entry/practices/entry1/events'
        first=self.post(path,dict(expected_revision=0,event=event))
        self.assertIsNone(first['execution']['observations'][0]['reps'])
        self.assertEqual(first,self.post(path,dict(expected_revision=0,event=event)))
        self.post(path,dict(expected_revision=1,event=dict(event,reps=3)),409)
        self.post(path,dict(expected_revision=0,event=dict(event,id='new')),409)
    def test_no_load_prescription_or_completion_without_observation(self):
        self.post('/v3/entry/practices',self.req)
        for event in [dict(id='f',type='finish',at=AT,outcome='completed'),
                      dict(id='w',type='practice_observation',at=AT,outcome='tried',weight_kg=20),
                      dict(id='z',type='practice_observation',at=AT,outcome='not_tried',reps=0)]:
            self.post('/v3/entry/practices/entry1/events',dict(expected_revision=0,event=event),422)
    def test_idle_rest_unknown_and_no_resume(self):
        self.post('/v3/entry/practices',self.req)
        self.post('/v3/entry/practices/entry1/events',dict(expected_revision=0,
            event=dict(id='r',type='rest_start',at=AT)))
        value=self.db.reconcile_inactivity('owner','entry1',datetime(2026,10,18,10,tzinfo=timezone.utc))
        self.assertEqual(value['execution']['state'],'stopped')
        self.assertIsNone(value['execution']['rests'][0]['elapsed_seconds'])
    def test_auth_required(self):
        app.dependency_overrides.pop(owner)
        self.assertEqual(self.client.get('/v3/entry/pathway').status_code,401)
