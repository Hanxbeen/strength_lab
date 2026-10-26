"""Normal authenticated-owner selection, not a deployed authentication test."""
import copy,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner,store
from backend.workout_store import WorkoutStore
from backend.programme_access import availability
from research_engine.core import digest
from tests import test_petrizzo, test_coaching, test_metd, test_sbd
from backend.coaching_store import initialize
ROOT=Path(__file__).resolve().parents[1]

class RoutineSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=WorkoutStore(Path(self.tmp.name)/'work.sqlite')
        initialize(self.db)
        self.user='normal'
        app.dependency_overrides[owner]=lambda:self.user
        app.dependency_overrides[store]=lambda:self.db
        names=['petrizzo2018-four-lift-2d','petrizzo2018-four-lift-3d','helms2018','metd2021','pilot2018-sbd','novice-sbd-choice','pilot2018-source-labels']
        self.items=[]
        for name in names:
            s=json.loads((ROOT/'data/research/coaching'/f'{name}.json').read_text())
            self.items.append(dict(source_id=s['id'],version=digest(s),status='research_preview',definition=s))
        self.catalog=patch('backend.coaching_api.catalog',return_value={'schema_version':3,'items':self.items})
        self.catalog.start();self.env=patch.dict(os.environ,COACHING_PREVIEW_OWNER_IDS='');self.env.start()
        self.client=TestClient(app)
    def tearDown(self):
        self.catalog.stop();self.env.stop();app.dependency_overrides.clear();self.tmp.cleanup()
    def post(self,path,data,status=200):
        r=self.client.post(path,json=data);self.assertEqual(r.status_code,status,r.text);return r.json()
    def request_for(self,source,arm):
        if source['adapter_version']=='petrizzo-2018-v1':
            f=test_petrizzo.PetrizzoTests();f.fixture(source['protocol']['days_per_week']);records=[]
            at=f.at;loads={e:40 for e in source['protocol']['sessions'][0]['exercises']}
            daily=dict(initial_loads_kg=loads)
        elif source['id']=='pilot2018-per-source-labels-v1':
            f=test_sbd.SBDTests();f.setUp();records=f.records;at='2026-10-18T09:00:00Z'
            f.profile.update(sex='male',training_years=3,powerlifting_years=2,
                independent_front_squat=True,rpe_familiarized=True,prior_moderate_high_load_training=True)
            f.setup.update(exercise_mapping='source_labels_verified_formula_v1',accept_source_discrepancy=True)
            daily={}
        elif source['adapter_version']=='helms-2018-v1':
            f=test_coaching.CoachingTests();f.setUp();records=f.records;at='2026-10-18T09:00:00Z'
            daily=dict(initial_rpe_loads_kg={'barbell_back_squat':100,'barbell_bench_press':80} if arm=='RPEG' else {})
        else:
            f=test_metd.METDTests();f.setUp();records=f.records;at='2026-10-18T09:00:00Z'
            f.profile.update(sex='male',raw_powerlifting=True,daily_max_training_last_12_weeks=False)
            daily=dict(initial_rpe_loads_kg={e:100 for e in ('barbell_back_squat','barbell_bench_press')} if arm!='AMRAP' else {})
        records=copy.deepcopy(records)
        for r in records:
            r['id']=source['id']+'-'+arm+'-'+r['id']
            self.db.register_max(self.user,r)
        req=dict(source_id=source['id'],source_version=digest(source),arm=arm,created_at=at,
            profile=f.profile,setup=f.setup,max_record_ids={r['exercise_id']:r['id'] for r in records})
        return req,daily
    def test_eight_complete_options_and_explicit_coverage_gap(self):
        data=self.client.get('/v3/routines').json()
        self.assertEqual(len(data['routines']),8);self.assertEqual(len(data['unavailable_adaptations']),2)
        for r in data['routines']:
            self.assertEqual(r['access'],'explicit_selection')
            self.assertEqual(len(r['sessions']),r['training_sessions'])
            self.assertTrue(r['input_contract']['required_fields'])
            self.assertFalse(r['scientific_approval'])
        for experience,count in [('entry',0),('foundation',2),('trained',2),('experienced',4)]:
            result=self.client.get('/v3/routines',params={'experience':experience})
            self.assertEqual(result.status_code,200,result.text);self.assertEqual(len(result.json()['routines']),count)
        self.assertEqual(data['coverage']['entry']['state'],'not_ready')
        self.assertEqual(self.client.get('/v3/routines',params={'experience':'unknown'}).status_code,422)
    def test_every_public_option_preview_create_start_change_stop_reload(self):
        options=self.client.get('/v3/routines').json()['routines']
        for idx,row in enumerate(options):
            with self.subTest(arm=row['arm'],source=row['source_id']):
                req,daily=self.request_for(row['definition'],row['arm'])
                response=self.post('/v3/routines/preview',dict(req,**daily))
                self.assertEqual(response['session_status'],'ready')
                with self.db.connect() as c:self.assertEqual(c.execute('SELECT count(*) FROM coaching_instances').fetchone()[0],idx)
                self.assertFalse(response['persisted'])
                iid='i'+str(idx);wid='w'+str(idx);base='/v3/programme-instances/'+iid
                instance=self.post('/v3/programme-instances',dict(req,id=iid))['instance']
                self.assertTrue(instance['access_decision']['public_selection'])
                ex=self.post(base+'/workouts',dict(workout_id=wid,week=1,day=1,started_at=req['created_at'],**daily))['execution']
                sid=ex['next_set_id']
                for event in [dict(id='change',type='change_load',at=req['created_at'],set_id=sid,value=35,unit='kg',reason='fatigue'),
                              dict(id='result',type='set_result',at=req['created_at'],set_id=sid,reps=1,rpe=9),
                              dict(id='finish',type='finish',at=req['created_at'],reason='time')]:
                    ex=self.post('/v2/workouts/'+wid+'/events',dict(expected_revision=ex['revision'],event=event))['execution']
                self.assertEqual(ex['sets'][0]['actual']['weight_kg'],35)
                self.assertEqual(self.client.get(base).status_code,200)
                self.assertEqual(self.client.get(base+'/next-session',params={'at':'2026-10-21T09:00:00Z'}).status_code,200)
                self.user='other';self.assertEqual(self.client.get(base).status_code,404);self.user='normal'
    def test_metd_scope_is_same_in_preview_and_create(self):
        source=next(x['definition'] for x in self.items if x['source_id']=='metd2021-sbd-v1')
        req,daily=self.request_for(source,'AMRAP');req['profile'].pop('raw_powerlifting')
        result=self.post('/v3/routines/preview',dict(req,**daily))
        self.assertFalse(result['can_create_instance']);self.assertIsNone(result['session_preview'])
        self.assertIn('profile.raw_powerlifting',[x['field'] for x in result['missing_inputs']])
        self.post('/v3/programme-instances',dict(req,id='bad'),422)
        req['profile']['raw_powerlifting']=True;req['profile']['daily_max_training_last_12_weeks']=True
        self.assertEqual(self.post('/v3/routines/preview',dict(req,**daily))['input_status'],'outside_supported_scope')
        self.post('/v3/programme-instances',dict(req,id='bad2'),422)
    def test_changed_source_cannot_self_release_and_preview_needs_loads(self):
        s=copy.deepcopy(self.items[0]['definition']);s['title']='changed'
        self.assertFalse(availability(s)['public_selection'])
        req,daily=self.request_for(self.items[0]['definition'],'FOUR_LIFT')
        result=self.post('/v3/routines/preview',req)
        self.assertEqual(result['session_status'],'needs_session_input')
        self.assertIsNone(result['session_preview'])
        with patch('backend.programme_access.RELEASES',{}):
            self.post('/v3/programme-instances',dict(req,id='not-released'),403)
    def test_missing_or_suspended_catalogue_never_claims_coverage(self):
        with patch('backend.coaching_api.catalog',return_value={'items':[]}):
            data=self.client.get('/v3/routines').json()
            self.assertEqual(data['routines'],[])
            self.assertTrue(all(x['option_count']==0 for x in data['coverage'].values()))
        suspended=copy.deepcopy(self.items)
        for item in suspended:item['status']='suspended'
        with patch('backend.coaching_api.catalog',return_value={'items':suspended}):
            self.assertEqual(self.client.get('/v3/routines').json()['routines'],[])

    def test_login_still_required(self):
        app.dependency_overrides.pop(owner)
        self.assertEqual(self.client.get('/v3/routines').status_code,401)
