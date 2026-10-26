"""Source-labelled PER runs for normal owners, while old instances stay unchanged."""
import copy,json,unittest
from datetime import datetime,timedelta
from unittest.mock import patch
from tests import test_sbd
from research_engine import sbd
from research_engine.core import digest,InvalidProgramme
from research_engine.programme_dispatch import exercises,max_exercises
from backend.programme_access import availability

class SourceLabelAPITests(test_sbd.SBDAPITests):
    def setUp(self):
        super().setUp()
        self.source=json.loads((test_sbd.ROOT/'data/research/coaching/pilot2018-source-labels.json').read_text())
        self.profile.update(sex='male',training_years=3,powerlifting_years=2,
            independent_front_squat=True,rpe_familiarized=True,prior_moderate_high_load_training=True)
        self.setup.update(exercise_mapping='source_labels_verified_formula_v1',accept_source_discrepancy=True)
        self.catalog.stop()
        self.catalog=patch('backend.coaching_api.catalog',return_value={'schema_version':3,'items':[
            dict(source_id=self.source['id'],version=digest(self.source),status='research_preview',definition=self.source)]})
        self.catalog.start()
        self.env.stop();self.env=patch.dict('os.environ',COACHING_PREVIEW_OWNER_IDS='');self.env.start()
    def instance(self):
        return sbd.make_instance(self.source,'PER_SOURCE_LABELS',self.profile,self.records,self.setup,self.at)
    def request(self):
        return dict(id='sbd',source_id=self.source['id'],source_version=digest(self.source),
            arm='PER_SOURCE_LABELS',created_at=self.at,profile=self.profile,setup=self.setup,
            max_record_ids={r['exercise_id']:r['id'] for r in self.records})
    def create(self):
        r=self.client.post('/v3/programme-instances',json=self.request())
        self.assertEqual(r.status_code,200,r.text)
        self.assertTrue(r.json()['instance']['access_decision']['public_selection'])
    def test_allowlist_and_incomplete_evaluation(self):
        req=self.request();req['max_record_ids']={}
        self.assertEqual(self.client.post('/v3/programme-instances',json=req).status_code,422)
        self.create()
        self.start(1,1,datetime.fromisoformat(self.at.replace('Z','+00:00')))
        r=self.client.post('/v3/programme-instances/sbd/evaluations',json={'id':'bad','at':self.at,'outcome':'completed'})
        self.assertEqual(r.status_code,422)
    def test_substitution_provenance_survives_change_stop_and_reload(self):
        self.create();at=datetime.fromisoformat(self.at.replace('Z','+00:00'));ex=self.start(1,1,at)
        front=next(r for r in ex['sets'] if r['source_exercise']=='Front squat')
        self.assertEqual(front['exercise_id'],'barbell_front_squat')
        mapping=front['source_mapping']
        self.assertFalse(mapping['substituted'])
        self.assertTrue(mapping['source_load_reference_verified'])
        self.assertEqual(mapping['load_reference_exercise_id'],'barbell_back_squat')
        for row in ex['sets'][:2]:
            at+=timedelta(seconds=60);ex=self.event('w1d1',ex,at,type='set_result',set_id=row['id'],reps=row['reps']['min'],rpe=8)
            at+=timedelta(seconds=ex["active_rest"]["target_seconds"]);ex=self.event('w1d1',ex,at,type='rest_end',outcome='completed')
        ex=self.event('w1d1',ex,at,type='change_load',set_id=front['id'],value=90,unit='kg',reason='fatigue')
        ex=self.event('w1d1',ex,at,type='set_result',set_id=front['id'],reps=1,rpe=9)
        at+=timedelta(seconds=30);ex=self.event('w1d1',ex,at,type='rest_end',outcome='skipped')
        next_id=ex['next_set_id']
        ex=self.event('w1d1',ex,at,type='change_load',set_id=next_id,value=80,unit='kg',reason='pain')
        ex=self.event('w1d1',ex,at,type='interrupt',reason='user_interruption')
        restored=self.client.get('/v2/workouts/w1d1').json()['execution']
        row=next(r for r in restored['sets'] if r['id']==front['id'])
        self.assertEqual(row['source_mapping'],mapping)
        self.assertEqual(row['weight_kg'],105);self.assertEqual(row['actual']['weight_kg'],90)
        self.assertEqual(restored['rests'][-1]['elapsed_seconds'],30)
        self.assertEqual(restored['coaching']['source_mapping_review']['substituted_set_count'],0)
        self.assertIsNone(restored['coaching']['next_set_decision']['factor'])
        self.assertEqual(restored['state'],'stopped')
    def test_source_reference_contract_and_scope(self):
        self.assertEqual(len(exercises(self.source)),4)
        self.assertEqual(len(max_exercises(self.source)),3)
        row=self.client.get('/v3/routines').json()['routines'][0]
        self.assertNotIn('barbell_front_squat',row['input_contract']['max_record_exercise_ids'])
        self.assertIn('barbell_front_squat',row['exercise_ids'])
        for field in ('independent_front_squat','rpe_familiarized','prior_moderate_high_load_training'):
            req=self.request();req['profile']=dict(self.profile);req['profile'].pop(field)
            result=self.client.post('/v3/routines/preview',json=req).json()
            self.assertFalse(result['can_create_instance'])
            self.assertIn('profile.'+field,[x['field'] for x in result['missing_inputs']])
            self.assertEqual(self.client.post('/v3/programme-instances',json=req).status_code,422)
        self.setup['accept_source_discrepancy']=False
        with self.assertRaises(InvalidProgramme):self.instance()
    def test_all_rows_match_audit_and_version_cannot_self_release(self):
        from scripts.build_per_source_labels import build
        self.assertEqual(self.source,build())
        original=copy.deepcopy(self.source)
        self.source['protocol']['sessions'][0]['rows'][2]['load_reference']['exercise_id']='barbell_front_squat'
        self.source['protocol_sha256']=digest(self.source['protocol'])
        with self.assertRaises(InvalidProgramme):self.instance()
        self.assertFalse(availability(self.source)['public_selection'])
        self.source=original
        self.assertEqual(sum(r['sets'] for s in self.source['protocol']['sessions'] for r in s['rows'] if r['exercise_id']=='barbell_front_squat'),22)
