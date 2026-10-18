import copy,json,tempfile,unittest,os
from datetime import datetime,timedelta
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner,store
from backend.workout_store import WorkoutStore
from research_engine.core import digest,InvalidProgramme
from research_engine import sbd

ROOT=Path(__file__).resolve().parents[1]

class SBDTests(unittest.TestCase):
    def setUp(self):
        self.source=json.loads(Path(os.environ.get('SBD_MANIFEST_PATH',ROOT/'data/research/coaching/pilot2018-sbd.json')).read_text())
        self.records=[dict(id=e,exercise_id=e,value=v,unit='kg',kind='measured',measured_at='2026-10-01T09:00:00Z') for e,v in zip(sbd.EXERCISES,[150,100,200])]
        self.profile={'age':30,'independent_sbd':True}
        self.setup={'mode':'user_selected_source','accept_scope_limits':True,'accept_adaptations':True,
            'exercise_mapping':'numbered_sbd_adaptation_v1','rest_seconds':180,'between_exercise_rest_seconds':300,
            'equipment_step_kg':2.5,'warmup':'user selected'}
        self.at='2026-10-15T09:00:00Z'
    def instance(self):return sbd.make_instance(self.source,'PER_ADAPTED',self.profile,self.records,self.setup,self.at)
    def test_data_and_original_labels(self):
        sbd.validate_source(self.source);sessions=self.source['protocol']['sessions']
        self.assertEqual(len(sessions),30)
        self.assertEqual(sum(r['sets'] for s in sessions for r in s['rows']),515)
        self.assertTrue(any(r['source_exercise']=='Front squat' for s in sessions for r in s['rows']))
        self.assertTrue(all(r['source']['cells'] for s in sessions for r in s['rows']))
    def test_baseline_and_units(self):
        a=self.instance();self.records[0].update(value=150/0.45359237,unit='lb');b=self.instance()
        x=sbd.prepare(a,1,1,self.at,[]);y=sbd.prepare(b,1,1,self.at,[])
        self.assertEqual(x['session']['sets'][0]['weight_kg'],75)
        self.assertEqual(x['session']['sets'][0]['weight_kg'],y['session']['sets'][0]['weight_kg'])
        self.records[0]['value']=999;self.assertEqual(a['max_records'][0]['weight_kg'],150)
    def test_invalid_inputs_and_source(self):
        original=copy.deepcopy(self.records)
        for kind in ('missing','future','estimated'):
            self.records=copy.deepcopy(original)
            if kind=='missing':self.records.pop()
            elif kind=='future':self.records[0]['measured_at']='2030-01-01T00:00:00Z'
            else:self.records[0]['kind']='estimated'
            with self.assertRaises(InvalidProgramme):self.instance()
        self.records=original;self.setup['accept_adaptations']=False
        with self.assertRaises(InvalidProgramme):self.instance()
        self.setup['accept_adaptations']=True
        self.source['protocol']['sessions'][0]['rows'][0]['percent_1rm']=999
        with self.assertRaises(InvalidProgramme):self.instance()
        self.source['protocol_sha256']=digest(self.source['protocol'])
        with self.assertRaises(InvalidProgramme):self.instance()

class SBDAPITests(SBDTests):
    def setUp(self):
        super().setUp();self.tmp=tempfile.TemporaryDirectory();self.db=WorkoutStore(Path(self.tmp.name)/'test.sqlite')
        self.user='sbd-owner';self.env=patch.dict('os.environ',COACHING_PREVIEW_OWNER_IDS=self.user);self.env.start()
        app.dependency_overrides[owner]=lambda:self.user;app.dependency_overrides[store]=lambda:self.db
        self.client=TestClient(app)
        self.catalog=patch('backend.coaching_api.catalog',return_value={'schema_version':3,'items':[
            {'source_id':self.source['id'],'version':digest(self.source),'status':'research_preview','definition':self.source}]})
        self.catalog.start()
        for r in self.records:self.db.register_max(self.user,r)
    def tearDown(self):
        self.catalog.stop();self.env.stop();app.dependency_overrides.clear();self.tmp.cleanup()
    def create(self):
        r=self.client.post('/v3/programme-instances',json={'id':'sbd','source_id':self.source['id'],'source_version':digest(self.source),
            'arm':'PER_ADAPTED','created_at':self.at,'profile':self.profile,'setup':self.setup,
            'max_record_ids':{r['exercise_id']:r['id'] for r in self.records}})
        self.assertEqual(r.status_code,200,r.text)
    def start(self,w,d,at):
        r=self.client.post('/v3/programme-instances/sbd/workouts',json={'workout_id':f'w{w}d{d}','week':w,'day':d,'started_at':at.isoformat()})
        self.assertEqual(r.status_code,200,r.text);return r.json()['execution']
    def event(self,wid,ex,at,**event):
        r=self.client.post('/v2/workouts/'+wid+'/events',json={'expected_revision':ex['revision'],
            'event':{'id':f'e{ex["revision"]}','at':at.isoformat(),**event}})
        self.assertEqual(r.status_code,200,r.text);return r.json()['execution']
    def test_full_30_session_lifecycle(self):
        self.create();start=datetime.fromisoformat(self.at.replace('Z','+00:00'));count=0
        for week in range(1,11):
            for day in range(1,4):
                at=start+timedelta(days=(week-1)*7+(day-1)*2);wid=f'w{week}d{day}';ex=self.start(week,day,at)
                if week>1:self.assertIsNotNone(ex['coaching']['previous_same_day'])
                for row in ex['sets']:
                    at+=timedelta(seconds=60);ex=self.event(wid,ex,at,type='set_result',set_id=row['id'],reps=row['reps']['min'],rpe=8);count+=1
                    if ex['active_rest']:
                        at+=timedelta(seconds=ex['active_rest']['target_seconds']);ex=self.event(wid,ex,at,type='rest_end',outcome='completed')
                ex=self.event(wid,ex,at,type='finish');self.assertEqual(ex['state'],'completed')
        self.assertEqual(count,515)
        self.db.register_max(self.user,{**self.records[0],'id':'post','value':155,'measured_at':(at+timedelta(days=2)).isoformat()})
        request={'id':'end','at':(at+timedelta(days=3)).isoformat(),'outcome':'completed','post_max_record_ids':{sbd.EXERCISES[0]:'post'},'comparison_conditions':{sbd.EXERCISES[0]:'same'}}
        r=self.client.post('/v3/programme-instances/sbd/evaluations',json=request);self.assertEqual(r.status_code,200,r.text)
        result=r.json();self.assertEqual(result['lifts'][0]['delta_kg'],5);self.assertIsNone(result['lifts'][1]['delta_kg'])
        self.assertIsNone(result['total_delta_kg']);self.assertIsNone(result['growth_prediction'])
        self.assertEqual(self.client.post('/v3/programme-instances/sbd/evaluations',json=request).json(),result)
        request['comparison_conditions']={sbd.EXERCISES[0]:'different'}
        self.assertEqual(self.client.post('/v3/programme-instances/sbd/evaluations',json=request).status_code,409)
        request.update(id='corrected',supersedes_id='end')
        r=self.client.post('/v3/programme-instances/sbd/evaluations',json=request);self.assertEqual(r.status_code,200,r.text)
        self.assertIsNone(r.json()['lifts'][0]['delta_kg'])
        self.assertEqual(len(self.client.get('/v3/programme-instances/sbd').json()['evaluations']),2)
        self.user='other';self.assertEqual(self.client.get('/v3/programme-instances/sbd').status_code,404)
    def test_changed_load_short_rest_and_early_closure(self):
        self.create();at=datetime.fromisoformat(self.at.replace('Z','+00:00'));ex=self.start(1,1,at);row=ex['sets'][0]
        at+=timedelta(seconds=10);ex=self.event('w1d1',ex,at,type='change_load',set_id=row['id'],value=60,unit='kg',reason='fatigue')
        at+=timedelta(seconds=60);ex=self.event('w1d1',ex,at,type='set_result',set_id=row['id'],reps=0,rpe=9)
        self.assertEqual(ex['active_rest']['basis'],'user_choice')
        at+=timedelta(seconds=30);ex=self.event('w1d1',ex,at,type='rest_end',outcome='skipped')
        ex=self.event('w1d1',ex,at,type='finish',reason='time')
        self.assertEqual(ex['sets'][0]['weight_kg'],75);self.assertEqual(ex['sets'][0]['actual']['weight_kg'],60)
        self.assertEqual(ex['rests'][0]['elapsed_seconds'],30)
        r=self.client.post('/v3/programme-instances/sbd/evaluations',json={'id':'stop','at':at.isoformat(),'outcome':'stopped'})
        self.assertEqual(r.status_code,200,r.text);self.assertTrue(all(x['delta_kg'] is None for x in r.json()['lifts']))
        r=self.client.post('/v3/programme-instances/sbd/workouts',json={'workout_id':'w1d2','week':1,'day':2,'started_at':(at+timedelta(days=2)).isoformat()})
        self.assertEqual(r.status_code,409,r.text)
    def test_interrupted_workout_can_close_programme(self):
        self.create()
        at=datetime.fromisoformat(self.at.replace('Z','+00:00'))
        ex=self.start(1,1,at)
        at+=timedelta(seconds=60)
        ex=self.event('w1d1',ex,at,type='interrupt',reason='user_interruption')
        self.assertEqual(ex['state'],'stopped')
        r=self.client.post('/v3/programme-instances/sbd/evaluations',json={
            'id':'interrupted-end','at':at.isoformat(),'outcome':'stopped'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['training']['stopped_sessions'],1)
        self.assertEqual(r.json()['training']['recorded_sets'],0)

    def test_reconnect_lists_only_owner_instances_with_cursor(self):
        from backend import coaching_store
        self.create()
        at=datetime.fromisoformat(self.at.replace('Z','+00:00'))
        self.start(1,1,at)
        value=coaching_store.instance(self.db,self.user,'sbd')
        coaching_store.save_instance(self.db,self.user,'sbd-2',value)
        coaching_store.save_instance(self.db,'other','foreign',value)
        # New HTTP client has no instance ID cached.
        fresh=TestClient(app)
        first=fresh.get('/v3/programme-instances',params={'limit':1})
        self.assertEqual(first.status_code,200,first.text)
        self.assertEqual(first.json()['items'][0]['instance_id'],'sbd')
        self.assertEqual(first.json()['items'][0]['latest_workout_id'],'w1d1')
        second=fresh.get('/v3/programme-instances',params={'limit':1,'after':first.json()['next_cursor']}).json()
        self.assertEqual([x['instance_id'] for x in second['items']],['sbd-2'])
        self.assertIsNone(second['next_cursor'])
        self.assertEqual(fresh.get('/v3/programme-instances',params={'limit':0}).status_code,422)
        self.user='other'
        self.assertEqual([x['instance_id'] for x in fresh.get('/v3/programme-instances').json()['items']],['foreign'])
        self.assertEqual(fresh.get('/v3/programme-instances/sbd').status_code,404)

    def test_substitution_provenance_survives_change_stop_and_reload(self):
        self.create()
        at=datetime.fromisoformat(self.at.replace('Z','+00:00'))
        ex=self.start(1,1,at)
        front=next(r for r in ex['sets'] if r['source_exercise']=='Front squat')
        mapping=front['source_mapping']
        self.assertEqual(front['exercise_id'],'barbell_back_squat')
        self.assertEqual(mapping['source_exercise_id'],'barbell_front_squat')
        self.assertEqual(mapping['load_reference_exercise_id'],'barbell_back_squat')
        self.assertTrue(mapping['substituted'])
        self.assertFalse(mapping['source_load_reference_verified'])
        # Work through preceding rows to reach the first substituted set.
        for row in ex['sets'][:2]:
            at+=timedelta(seconds=60)
            ex=self.event('w1d1',ex,at,type='set_result',set_id=row['id'],reps=row['reps']['min'],rpe=8)
            at+=timedelta(seconds=180)
            ex=self.event('w1d1',ex,at,type='rest_end',outcome='completed')
        at+=timedelta(seconds=1)
        ex=self.event('w1d1',ex,at,type='change_load',set_id=front['id'],value=90,unit='kg',reason='fatigue')
        at+=timedelta(seconds=60)
        ex=self.event('w1d1',ex,at,type='set_result',set_id=front['id'],reps=2,rpe=9)
        at+=timedelta(seconds=30)
        ex=self.event('w1d1',ex,at,type='rest_end',outcome='skipped')
        ex=self.event('w1d1',ex,at,type='interrupt',reason='user_interruption')
        restored=self.client.get('/v2/workouts/w1d1').json()['execution']
        actual=next(r for r in restored['sets'] if r['id']==front['id'])
        self.assertEqual(actual['source_mapping'],mapping)
        self.assertEqual(actual['weight_kg'],105)
        self.assertEqual(actual['actual']['weight_kg'],90)
        self.assertEqual(restored['rests'][-1]['elapsed_seconds'],30)
        self.assertEqual(restored['state'],'stopped')
        self.assertEqual(restored['coaching']['source_mapping_review']['substituted_set_count'],22)
        self.assertIsNone(restored['coaching']['next_set_decision']['factor'])

    def test_allowlist_and_incomplete_evaluation(self):
        self.user='not-allowed'
        r=self.client.post('/v3/programme-instances',json={'id':'x','source_id':self.source['id'],'source_version':digest(self.source),
            'arm':'PER_ADAPTED','created_at':self.at,'profile':self.profile,'setup':self.setup,'max_record_ids':{}})
        self.assertEqual(r.status_code,403)
        self.user='sbd-owner';self.create()
        self.start(1,1,datetime.fromisoformat(self.at.replace('Z','+00:00')))
        r=self.client.post('/v3/programme-instances/sbd/evaluations',json={'id':'bad','at':self.at,'outcome':'completed'})
        self.assertEqual(r.status_code,422)

if __name__=='__main__':unittest.main()
