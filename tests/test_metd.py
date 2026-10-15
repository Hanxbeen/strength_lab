import copy,json,os,tempfile,unittest
from pathlib import Path
from datetime import datetime,timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner,store
from backend.workout_store import WorkoutStore,replay
from research_engine import metd
from research_engine.core import digest,InvalidProgramme
from scripts.extract_metd2021 import extract

ROOT=Path(__file__).resolve().parents[1]

class METDTests(unittest.TestCase):
    def setUp(self):
        self.source=json.loads(Path(os.environ.get('METD_MANIFEST_PATH',ROOT/'data/research/coaching/metd2021.json')).read_text())
        self.at='2026-10-15T09:00:00Z'
        self.profile={'age':30,'independent_sbd':True,'training_years':5,'powerlifting_years':3,'rpe_training_years':2}
        self.setup={'mode':'user_selected_source','accept_scope_limits':True,'accept_adaptations':True,
            'rest_seconds':180,'between_exercise_rest_seconds':300,'equipment_step_kg':2.5,'warmup':'progressive user-selected'}
        self.records=[dict(id=e,exercise_id=e,value=v,unit='kg',kind='measured',measured_at='2026-10-01T09:00:00Z')
                      for e,v in zip(metd.EXERCISES,[150,100,200])]
    def instance(self,arm):return metd.make_instance(self.source,arm,self.profile,self.records,self.setup,self.at)
    def snapshot(self,arm):return metd.prepare(self.instance(arm),1,1,self.at,[],{} if arm=='AMRAP' else {e:100 for e in metd.EXERCISES[:2]})
    def event(self,i,kind,**data):return dict(id=str(i),type=kind,at=(datetime.fromisoformat(self.at.replace('Z','+00:00'))+timedelta(seconds=i*300)).isoformat(),**data)
    def test_extraction_and_arm_counts(self):
        self.assertEqual(extract(),self.source);metd.validate_source(self.source)
        self.assertEqual(len(self.source['protocol']['sessions']),18)
        for arm,working,total in [('MAX',36,36),('MAX_BOFF',108,108),('AMRAP',36,144)]:
            snapshots=[metd.prepare(self.instance(arm),w,d,self.at,[],{} if arm=='AMRAP' else
                {e:100 for e in (metd.EXERCISES[:2] if d!=2 else metd.EXERCISES[1:])}) for w in range(1,7) for d in (1,2,3)]
            rows=[r for s in snapshots for r in s['session']['sets']]
            self.assertEqual(len(rows),total);self.assertEqual(sum(r['set_role']!='warmup' for r in rows),working)
    def test_amrap_not_fixed_reps_or_growth(self):
        snap=self.snapshot('AMRAP');ex=replay(snap,[])
        self.assertEqual([r['weight_kg'] for r in ex['sets'][:4]],[60,75,90,105])
        self.assertIsNone(ex['sets'][3]['reps']['min']);self.assertIsNone(ex['summary']['minimum_reps_completion_bounds_percent'])
        events=[]
        for row in ex['sets']:
            if events:events.append(self.event(len(events)+1,'rest_end',outcome='completed'))
            events.append(self.event(len(events)+1,'set_result',set_id=row['id'],reps=12 if row['set_role']=='working' else 5,rpe=9))
        events.append(self.event(len(events)+1,'finish'))
        result=replay(snap,events)
        self.assertIsNone(result['summary']['minimum_reps_completion_percent'])
        self.assertIsNone(result['summary']['chart'][3]['reps_shortfall'])
        self.assertEqual(result['summary']['recorded_sets'],8)
    def test_backoff_uses_actual_not_planned_or_1rm(self):
        snap=self.snapshot('MAX_BOFF');sid=snap['session']['sets'][0]['id']
        self.assertIsNone(replay(snap,[])['sets'][1]['weight_kg'])
        events=[self.event(1,'change_load',set_id=sid,value=90,unit='kg',reason='fatigue'),
                self.event(2,'set_result',set_id=sid,reps=1,rpe=9.5)]
        ex=replay(snap,events);self.assertEqual(ex['sets'][1]['weight_kg'],72.5)
        self.assertEqual(ex['sets'][1]['unrounded_weight_kg'],72)
        self.assertIsNone(snap['session']['sets'][1]['weight_kg'])
        events += [self.event(3,'rest_end',outcome='completed'),self.event(4,'change_load',set_id=ex['sets'][1]['id'],value=70,unit='kg',reason='fatigue'),
                   self.event(5,'set_result',set_id=ex['sets'][1]['id'],reps=3)]
        ex=replay(snap,events);self.assertEqual(ex['sets'][1]['actual']['weight_kg'],70)
        self.assertEqual(ex['sets'][2]['weight_kg'],72.5)
    def test_missing_single_requires_choice(self):
        snap=self.snapshot('MAX_BOFF');rows=snap['session']['sets']
        ev=[self.event(1,'skip_set',set_id=rows[0]['id'],reason='time')]
        with self.assertRaisesRegex(InvalidProgramme,'SOURCE_LOAD_UNAVAILABLE'):
            replay(snap,ev+[self.event(2,'set_result',set_id=rows[1]['id'],reps=3)])
        ev += [self.event(2,'change_load',set_id=rows[1]['id'],value=60,unit='kg',reason='other'),
               self.event(3,'set_result',set_id=rows[1]['id'],reps=3)]
        self.assertEqual(replay(snap,ev)['sets'][1]['actual']['weight_kg'],60)
        zero=[self.event(1,'set_result',set_id=rows[0]['id'],reps=0)]
        self.assertIsNone(replay(snap,zero)['sets'][1]['weight_kg'])
    def test_source_and_scope_validation(self):
        with self.assertRaises(InvalidProgramme):metd.prepare(self.instance('MAX'),1,1,self.at,[],{})
        with self.assertRaises(InvalidProgramme):metd.prepare(self.instance('AMRAP'),7,1,self.at,[],{})
        self.profile['rpe_training_years']=0
        with self.assertRaises(InvalidProgramme):self.instance('MAX')
        self.source['protocol']['arms']['AMRAP']['load']['percent']=95
        self.source['protocol_sha256']=digest(self.source['protocol'])
        with self.assertRaises(InvalidProgramme):metd.validate_source(self.source)

class METDAPITests(METDTests):
    def test_all_arms_full_lifecycle(self):
        with tempfile.TemporaryDirectory() as directory:
            db=WorkoutStore(Path(directory)/'workouts.sqlite');user='metd-owner'
            app.dependency_overrides[owner]=lambda:user;app.dependency_overrides[store]=lambda:db
            try:
                with patch.dict(os.environ,COACHING_PREVIEW_OWNER_IDS=user),patch('backend.coaching_api.catalog',return_value={'schema_version':3,'items':[
                    {'source_id':self.source['id'],'version':digest(self.source),'status':'research_preview','definition':self.source}]}):
                    client=TestClient(app)
                    for r in self.records:db.register_max(user,r)
                    def post(url,payload):
                        r=client.post(url,json=payload);self.assertEqual(r.status_code,200,r.text);return r.json()
                    for arm in metd.ARMS:
                        base='/v3/programme-instances/'+arm
                        post('/v3/programme-instances',dict(id=arm,source_id=self.source['id'],source_version=digest(self.source),arm=arm,
                            created_at=self.at,profile=self.profile,setup=self.setup,max_record_ids={r['exercise_id']:r['id'] for r in self.records}))
                        for w in range(1,7):
                            for d in (1,2,3):
                                at=datetime.fromisoformat(self.at.replace('Z','+00:00'))+timedelta(days=(w-1)*7+(d-1)*2)
                                wid=arm+str(w)+str(d);loads={} if arm=='AMRAP' else {e:100 for e in (metd.EXERCISES[:2] if d!=2 else metd.EXERCISES[1:])}
                                request=dict(workout_id=wid,week=w,day=d,started_at=at.isoformat(),initial_rpe_loads_kg=loads)
                                ex=post(base+'/workouts',request)['execution']
                                self.assertEqual(post(base+'/workouts',request)['execution'],ex)
                                def send(kind,**data):
                                    nonlocal at,ex
                                    at+=timedelta(seconds=300)
                                    ex=post('/v2/workouts/'+wid+'/events',{'expected_revision':ex['revision'],
                                        'event':dict(id=str(ex['revision']),at=at.isoformat(),type=kind,**data)})['execution']
                                while ex['next_set_id']:
                                    if ex['state']=='resting':send('rest_end',outcome='completed')
                                    row=next(r for r in ex['sets'] if r['id']==ex['next_set_id'])
                                    send('set_result',set_id=row['id'],reps=row['reps']['min'] if row['reps']['min'] is not None else 10,rpe=9)
                                send('finish')
                        at+=timedelta(days=5)
                        result=post(base+'/evaluations',dict(id='end',at=at.isoformat(),outcome='completed',post_max_record_ids={},comparison_conditions={}))
                        self.assertEqual(result['training']['closed_sessions'],18);self.assertIsNone(result['total_delta_kg'])
            finally:app.dependency_overrides.clear()
