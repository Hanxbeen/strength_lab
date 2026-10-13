import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner,store
from backend.workout_store import WorkoutStore
from research_engine.core import digest,InvalidProgramme
from research_engine.coaching import make_instance,prepare,adjustment
from scripts.extract_helms2018 import extract

ROOT=Path(__file__).resolve().parents[1]
class CoachingTests(unittest.TestCase):
    def setUp(self):
        self.source=json.loads((ROOT/'data/research/coaching/helms2018.json').read_text())
        self.records=[dict(id=e,exercise_id=e,value=v,unit='kg',kind='measured',measured_at='2026-10-01T10:00:00Z')
                      for e,v in [('barbell_back_squat',160),('barbell_bench_press',120)]]
        self.profile=dict(sex='male',age=25,training_months=36,body_mass_kg=80,healthy=True,lifts_weekly_last_6_months=True)
        self.setup=dict(mode='user_selected_source',accept_scope_limits=True,rest_seconds=300,equipment_step_kg=2.5,warmup='user-defined')
    def instance(self,arm='1RMG'):
        return make_instance(self.source,arm,self.profile,self.records,self.setup,'2026-10-12T09:00:00Z')
    def test_source_reextract_matches_saved_manifest(self):
        self.assertEqual(extract((ROOT/'data/research/coaching/sources/PMC5877330.xml').read_bytes()),self.source)
        self.assertEqual(self.source['protocol']['weeks'][7]['days'][2],{'kind':'post_test'})
        self.assertEqual(self.source['protocol']['weeks'][2]['days'][0]['percent_1rm'],72.5)
    def test_baseline_specific_and_snapshot_frozen(self):
        i=self.instance(); self.records[0]['value']=200
        s=prepare(i,1,1,'2026-10-12T09:00:00Z',[])
        self.assertEqual(s['session']['sets'][0]['weight_kg'],105)
        self.assertEqual(s['session']['sets'][0]['unrounded_weight_kg'],104)
        self.assertEqual(i['max_records'][0]['weight_kg'],160)
    def test_source_examples_and_missing_effort(self):
        a=dict(reps=4,weight_kg=100,rpe=10,reason='fatigue',failure='momentary_concentric')
        self.assertAlmostEqual(adjustment('RPEG',a,5,[7,9])['factor'],.92)
        self.assertAlmostEqual(adjustment('1RMG',a,5,[7,9])['factor'],.96)
        a.update(reps=5,rpe=8.5)
        self.assertAlmostEqual(adjustment('RPEG',a,5,[6,8])['factor'],.98)
        a['rpe']=None
        self.assertEqual(adjustment('RPEG',a,5,[6,8])['status'],'needs_rpe')
        a.update(reps=4,reason='time')
        self.assertIsNone(adjustment('RPEG',a,5,[6,8])['factor'])
        a.update(reason='fatigue',failure='technical')
        self.assertIsNone(adjustment('RPEG',a,5,[6,8])['factor'])
    def test_missing_history_and_lowered_load_prevent_weekly_increase(self):
        i=self.instance()
        with self.assertRaises(InvalidProgramme):prepare(i,3,1,'2026-10-26T09:00:00Z',[])
        rows=[]
        for eid in ('barbell_back_squat','barbell_bench_press'):
            for n in range(3):
                rows.append(dict(exercise_id=eid,status='recorded',reps={'min':8},weight_kg=100,actual={'reps':8,'weight_kg':90}))
        history=[{'week':2,'day':1,'workout_id':'old','execution':{'sets':rows}}]
        s=prepare(i,3,1,'2026-10-26T09:00:00Z',history)
        self.assertEqual(s['session']['sets'][0]['load']['percent'],70)
        for r in rows:r['actual']['weight_kg']=100
        s=prepare(i,3,1,'2026-10-26T09:00:00Z',history)
        self.assertEqual(s['session']['sets'][0]['load']['percent'],72.5)
    def test_scope_and_testing_not_guessed(self):
        self.profile['training_months']=1
        with self.assertRaises(InvalidProgramme):self.instance()
        self.profile['training_months']=36
        with self.assertRaises(InvalidProgramme):prepare(self.instance(),8,3,'2026-12-04T09:00:00Z',[])
        with self.assertRaises(InvalidProgramme):prepare(self.instance('RPEG'),1,1,'2026-10-12T09:00:00Z',[])

class CoachingAPITests(unittest.TestCase):
    def setUp(self):
        CoachingTests.setUp(self)
        self.tmp=tempfile.TemporaryDirectory();self.db=WorkoutStore(Path(self.tmp.name)/'test.sqlite')
        self.user='owner-a'
        app.dependency_overrides[owner]=lambda:self.user
        app.dependency_overrides[store]=lambda:self.db
        self.client=TestClient(app)
        self.mock=patch('backend.coaching_api.catalog',return_value={'schema_version':3,'items':[
            {'source_id':self.source['id'],'version':digest(self.source),'status':'research_preview','definition':self.source}]})
        self.catalog_mock=self.mock.start()
        for r in self.records:self.db.register_max(self.user,r)
    def tearDown(self):
        self.mock.stop();app.dependency_overrides.clear();self.tmp.cleanup()
    def start(self,arm='1RMG'):
        response=self.client.post('/v3/programme-instances',json={
          'id':'i1','source_id':self.source['id'],'source_version':digest(self.source),'arm':arm,
          'created_at':'2026-10-12T09:00:00Z','profile':self.profile,
          'max_record_ids':{r['exercise_id']:r['id'] for r in self.records},'setup':self.setup})
        self.assertEqual(response.status_code,200,response.text)
        self.request={'workout_id':'w1','week':1,'day':1,'started_at':'2026-10-12T09:00:00Z',
          'initial_rpe_loads_kg':{'barbell_back_squat':100,'barbell_bench_press':80} if arm=='RPEG' else {}}
        response=self.client.post('/v3/programme-instances/i1/workouts',json=self.request)
        self.assertEqual(response.status_code,200,response.text)
        return response.json()
    def test_record_rest_adjustment_reload_and_owner_isolation(self):
        result=self.start('RPEG');sid=result['execution']['sets'][0]['id']
        event={'id':'e1','type':'set_result','at':'2026-10-12T09:01:00Z','set_id':sid,
               'reps':7,'rpe':10,'reason':'fatigue','failure':'momentary_concentric'}
        response=self.client.post('/v2/workouts/w1/events',json={'expected_revision':0,'event':event})
        self.assertEqual(response.status_code,200,response.text)
        e=response.json()['execution']
        self.assertEqual(e['coaching']['next_set_decision']['proposed_weight_kg'],85)
        self.assertEqual(e['sets'][1]['selected_weight_kg'],100) # suggestion does not overwrite prescription
        self.assertEqual(e['active_rest']['target_seconds'],300)
        response=self.client.post('/v2/workouts/w1/events',json={'expected_revision':1,'event':
            {'id':'e2','type':'rest_end','at':'2026-10-12T09:03:00Z','outcome':'skipped'}})
        self.assertEqual(response.json()['execution']['rests'][0]['elapsed_seconds'],120)
        self.assertEqual(response.json()['execution']['summary']['rest_shortfall_seconds'],180)
        self.assertEqual(self.client.get('/v2/workouts/w1').json()['execution']['sets'][0]['actual']['rpe'],10)
        self.user='owner-b'
        self.assertEqual(self.client.get('/v3/programme-instances/i1').status_code,404)
        self.assertEqual(self.client.get('/v2/workouts/w1').status_code,404)
    def test_retries_do_not_depend_on_current_catalog(self):
        self.start()
        self.catalog_mock.side_effect=RuntimeError('unavailable')
        self.assertEqual(self.client.post('/v3/programme-instances/i1/workouts',json=self.request).status_code,200)
    def test_no_jumping_and_invalid_rpe(self):
        result=self.start()
        request={**self.request,'workout_id':'w3','week':3}
        self.assertEqual(self.client.post('/v3/programme-instances/i1/workouts',json=request).status_code,422)
        event={'id':'bad','type':'set_result','at':'2026-10-12T09:01:00Z','set_id':result['execution']['sets'][0]['id'],'reps':8,'rpe':float('inf')}
        event['rpe']=10.5
        self.assertEqual(self.client.post('/v2/workouts/w1/events',json={'expected_revision':0,'event':event}).status_code,422)
        self.assertEqual(self.client.get('/v2/workouts/w1').json()['execution']['revision'],0)

    def test_full_eight_week_programme_preserves_23_training_sessions(self):
        from datetime import datetime,timedelta,timezone
        self.start()
        start=datetime(2026,10,12,9,tzinfo=timezone.utc)
        recorded=0
        for week in range(1,9):
            for day in range(1,4):
                if (week,day)==(8,3):continue
                wid='w1' if (week,day)==(1,1) else f'w{week}d{day}'
                at=start+timedelta(days=(week-1)*7+(day-1)*2)
                if (week,day)!=(1,1):
                    response=self.client.post('/v3/programme-instances/i1/workouts',json={
                        'workout_id':wid,'week':week,'day':day,'started_at':at.isoformat()})
                    self.assertEqual(response.status_code,200,response.text)
                execution=self.client.get('/v2/workouts/'+wid).json()['execution']
                for row in execution['sets']:
                    at+=timedelta(seconds=60)
                    event={'id':row['id'],'type':'set_result','at':at.isoformat(),
                           'set_id':row['id'],'reps':row['reps']['min'],'rpe':7}
                    response=self.client.post('/v2/workouts/'+wid+'/events',json={
                        'expected_revision':execution['revision'],'event':event})
                    self.assertEqual(response.status_code,200,response.text)
                    execution=response.json()['execution'];recorded+=1
                    if execution['active_rest']:
                        at+=timedelta(seconds=execution['active_rest']['target_seconds'])
                        response=self.client.post('/v2/workouts/'+wid+'/events',json={
                            'expected_revision':execution['revision'],'event':
                            {'id':'rest-'+row['id'],'type':'rest_end','at':at.isoformat(),'outcome':'completed'}})
                        self.assertEqual(response.status_code,200,response.text)
                        execution=response.json()['execution']
                response=self.client.post('/v2/workouts/'+wid+'/events',json={
                    'expected_revision':execution['revision'],'event':
                    {'id':'finish','type':'finish','at':at.isoformat()}})
                self.assertEqual(response.json()['execution']['state'],'completed')
        self.assertEqual(recorded,128)
        result=self.client.get('/v3/programme-instances/i1').json()
        self.assertEqual(len(result['history']),23)
        self.assertEqual(result['history'][-1]['execution']['summary']['minimum_reps_completion_percent'],100)

    def test_early_finish_allows_later_session_but_not_compressed_schedule(self):
        self.start()
        self.client.post('/v2/workouts/w1/events',json={'expected_revision':0,'event':
            {'id':'end','type':'finish','at':'2026-10-12T09:05:00Z','reason':'time'}})
        body={'workout_id':'w2','week':1,'day':2,'started_at':'2026-10-13T09:00:00Z'}
        self.assertEqual(self.client.post('/v3/programme-instances/i1/workouts',json=body).status_code,422)
        body['started_at']='2026-10-14T09:00:00Z'
        self.assertEqual(self.client.post('/v3/programme-instances/i1/workouts',json=body).status_code,200)

    def test_anonymous_and_suspended_source(self):
        app.dependency_overrides.pop(owner)
        self.assertEqual(self.client.get('/v3/research-programmes').status_code,401)
        app.dependency_overrides[owner]=lambda:self.user
        self.start()
        self.catalog_mock.return_value['items'][0]['status']='suspended'
        # Existing ledger remains available, but new starts stop.
        self.assertEqual(self.client.get('/v2/workouts/w1').status_code,200)
        self.assertEqual(self.client.post('/v3/programme-instances/i1/workouts',json={
            'workout_id':'w2','week':1,'day':2,'started_at':'2026-10-14T09:00:00Z'}).status_code,422)

if __name__=='__main__':unittest.main()
