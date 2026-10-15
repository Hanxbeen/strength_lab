import copy,json,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner,store
from backend.workout_store import WorkoutStore
from backend.programme_readiness import preview,next_session
from research_engine.core import digest,InvalidProgramme
from research_engine.programme_dispatch import make_instance,prepare
from research_engine.programme_schedule import policy,index
from tests import test_metd as fixtures

class ProgrammeReadinessTests(unittest.TestCase):
    def setUp(self):fixtures.METDTests.setUp(self)
    def request(self):return dict(source_id=self.source['id'],source_version=digest(self.source),arm='AMRAP',
        created_at=self.at,profile=self.profile,setup=self.setup,max_record_ids={r['exercise_id']:r['id'] for r in self.records})
    def test_missing_and_release_are_separate(self):
        request=self.request();request.update(profile={},setup={},max_record_ids={})
        r=preview(self.source,request,[],False)
        self.assertEqual(r['input_status'],'needs_input');self.assertGreater(len(r['missing_inputs']),10)
        r=preview(self.source,self.request(),self.records,False)
        self.assertEqual(r['input_status'],'ready');self.assertFalse(r['can_create_instance'])
        self.assertEqual(r['recommendation_status'],'not_assessed')
        self.assertTrue(preview(self.source,self.request(),self.records,True)['can_create_instance'])
        self.profile['rpe_training_years']=0
        r=preview(self.source,self.request(),self.records,True)
        self.assertEqual(r['input_status'],'outside_supported_scope');self.assertFalse(r['can_create_instance'])
    def test_policy_is_frozen_and_old_instance_supported(self):
        a=make_instance(self.source,'AMRAP',self.profile,self.records,self.setup,self.at)
        self.assertEqual(len(a['schedule_policy']['sessions']),18)
        self.assertIn('schedule_policy',prepare(a,1,1,self.at,[],{}))
        a['schedule_policy']['minimum_start_interval_seconds']=0
        with self.assertRaisesRegex(InvalidProgramme,'SCHEDULE_POLICY_MISMATCH'):prepare(a,1,1,self.at,[],{})
        a.pop('schedule_policy')
        self.assertNotIn('schedule_policy',prepare(a,1,1,self.at,[],{}))
        with self.assertRaises(InvalidProgramme):index(policy(self.source),7,1)
    def test_all_source_contracts_use_existing_validator(self):
        root=Path(__file__).resolve().parents[1]/'data/research/coaching'
        source=json.loads((root/'pilot2018-sbd.json').read_text())
        req=self.request();req['arm']='PER_ADAPTED';req['setup']={**self.setup,'exercise_mapping':'numbered_sbd_adaptation_v1'}
        self.assertEqual(preview(source,req,self.records,True)['input_status'],'ready')
        self.assertEqual(len(policy(source)['sessions']),30)
        source=json.loads((root/'helms2018.json').read_text())
        req['arm']='1RMG';req['profile']=dict(sex='male',age=25,training_months=36,body_mass_kg=80,healthy=True,lifts_weekly_last_6_months=True)
        req['setup']={**self.setup,'rest_seconds':300}
        req['max_record_ids']={r['exercise_id']:r['id'] for r in self.records[:2]}
        self.assertEqual(preview(source,req,self.records[:2],True)['input_status'],'ready')
        self.assertEqual(len(policy(source)['sessions']),23)
    def test_next_actions_for_open_wait_delay_and_closed(self):
        a=make_instance(self.source,'AMRAP',self.profile,self.records,self.setup,self.at)
        self.assertEqual(next_session(a,[],[],self.at)['next_session'],{'week':1,'day':1})
        history=[{'workout_id':'w1','snapshot':{'started_at':self.at},'execution':{'state':'active'},
                  'events':[{'at':'2026-10-15T10:00:00Z'}]}]
        self.assertEqual(next_session(a,history,[],self.at)['state'],'workout_open')
        history[0]['execution']['state']='stopped'
        r=next_session(a,history,[],'2026-10-16T09:00:00Z')
        self.assertEqual(r['state'],'waiting_for_schedule');self.assertEqual(r['earliest_start_at'],'2026-10-17T09:00:00+00:00')
        r=next_session(a,history,[],'2026-11-16T09:00:00Z')
        self.assertEqual(r['state'],'schedule_available');self.assertIsNone(r['automatic_load_adjustment'])
        self.assertEqual(r['next_session'],{'week':1,'day':2})
        self.assertEqual(next_session(a,history,[{'id':'done'}],self.at)['state'],'programme_closed')
        self.assertEqual(next_session(a,history*18,[],self.at)['state'],'awaiting_evaluation')
    def test_api_no_write_owner_and_revalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            db=WorkoutStore(Path(directory)/'test.sqlite');user='owner'
            app.dependency_overrides[owner]=lambda:user;app.dependency_overrides[store]=lambda:db
            try:
                client=TestClient(app)
                for r in self.records:db.register_max(user,r)
                entry={'source_id':self.source['id'],'version':digest(self.source),'status':'research_preview','definition':self.source}
                with patch('backend.coaching_api.catalog',return_value={'schema_version':3,'items':[entry]}),patch.dict(os.environ,COACHING_PREVIEW_OWNER_IDS='owner'):
                    payload=self.request();r=client.post('/v3/programme-readiness',json=payload)
                    self.assertEqual(r.status_code,200,r.text);self.assertTrue(r.json()['can_create_instance'])
                    with db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM execution_workouts').fetchone()[0],0)
                    create=dict(payload,id='instance')
                    entry['status']='suspended'
                    self.assertEqual(client.post('/v3/programme-instances',json=create).status_code,422)
                    entry['status']='research_preview'
                    r=client.post('/v3/programme-instances',json=create);self.assertEqual(r.status_code,200,r.text)
                    r=client.get('/v3/programme-instances/instance/next-session',params={'at':self.at})
                    self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['state'],'schedule_available')
                    user='other'
                    r=client.post('/v3/programme-readiness',json=payload)
                    self.assertEqual(r.json()['input_status'],'needs_input');self.assertFalse(r.json()['can_create_instance'])
                    self.assertEqual(client.get('/v3/programme-instances/instance/next-session',params={'at':self.at}).status_code,404)
            finally:app.dependency_overrides.clear()
