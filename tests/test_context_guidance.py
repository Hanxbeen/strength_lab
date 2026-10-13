import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore
from backend.context_api import context_catalog
from backend.repository import CatalogUnavailable
from research_engine.core import digest, InvalidProgramme
from research_engine.context_guidance import explain, validate_packet
from research_engine.coaching import make_instance, prepare
from scripts.context_import import build

ROOT = Path(__file__).resolve().parents[1]
PACKET = json.loads((ROOT/'data/research/coaching/context-evidence.json').read_text())

def execution():
    return dict(revision=2, active_rest=None, rests=[
        dict(after_set_id='s1',target_seconds=300,elapsed_seconds=120,shortfall_seconds=180,outcome='skipped',kind='between_sets')],
        sets=[dict(id='s1',status='recorded',reps={'min':5},actual={'reps':4,'reason':'fatigue'}),
              dict(id='s2',status='skipped',reps={'min':5},actual=None)])

class ContextTests(unittest.TestCase):
    def test_real_facts_without_prescription_mutation(self):
        value=execution(); before=copy.deepcopy(value)
        out=explain(value,PACKET)
        self.assertEqual(value,before)
        self.assertEqual(out['facts']['below_minimum_rep_set_ids'],['s1'])
        self.assertEqual(out['facts']['skipped_sets'],1)
        self.assertEqual(len(out['cards']),1)
        self.assertEqual(out['cards'][0]['source']['review_extent'],'abstract_only')
        self.assertEqual(out['facts']['short_rests'][0]['target_seconds'],300)
        self.assertIsNone(out['prescription_change'])
        self.assertIsNone(out['growth_prediction'])
    def test_open_rest_not_classified_as_short(self):
        value=execution(); value.update(rests=[],active_rest={'target_seconds':300})
        out=explain(value,PACKET)
        self.assertEqual(out['cards'],[])
        self.assertTrue(out['facts']['active_rest_excluded'])
    def test_finish_and_between_exercise_rest_not_interset_failure(self):
        for key,value in [('outcome','interrupted'),('kind','between_exercises')]:
            record=execution(); record['rests'][0][key]=value
            self.assertEqual(explain(record,PACKET)['cards'],[])
    def test_topics_are_explicit_not_plateau_diagnosis(self):
        out=explain(execution(),PACKET,'deload')
        self.assertEqual([c['source']['topic'] for c in out['cards']],['deload'])
        source=out['cards'][0]['source']
        self.assertEqual(source['statistics']['interval_kg'],[-10.4,3.2])
        self.assertNotIn('p_value',source['statistics'])
        self.assertIn('cessation',source['design'])
    def test_pain_suppresses_research_adjustment_cards(self):
        value=execution(); value['sets'][1]['reason']='pain'
        out=explain(value,PACKET,'volume')
        self.assertEqual(out['status'],'pain_review_needed')
        self.assertEqual(out['cards'],[])
    def test_invalid_approval_and_duplicate_topics_fail(self):
        for field,value in [('scientific_approval',True),('sources',[])]:
            packet=copy.deepcopy(PACKET);packet[field]=value
            with self.assertRaises(InvalidProgramme):validate_packet(packet)
    def test_import_is_versioned_and_non_overwriting(self):
        sql=build(PACKET)
        self.assertIn(digest(PACKET),sql)
        self.assertIn('ON CONFLICT DO NOTHING',sql)
    def test_bad_remote_hash_fails_closed(self):
        value={'schema_version':1,'items':[dict(id=PACKET['id'],version='wrong',
                    status='research_preview',definition=PACKET)]}
        with patch.dict('os.environ',SUPABASE_URL='https://example.invalid',SUPABASE_PUBLISHABLE_KEY='test'):
            with patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(value).encode())):
                with self.assertRaises(CatalogUnavailable):context_catalog()

class ContextAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.db=WorkoutStore(Path(self.tmp.name)/'workouts.sqlite')
        self.user='a'
        source=json.loads((ROOT/'data/research/coaching/helms2018.json').read_text())
        records=[dict(id=e,exercise_id=e,value=v,unit='kg',kind='measured',measured_at='2026-10-01T10:00:00Z')
                 for e,v in [('barbell_back_squat',160),('barbell_bench_press',120)]]
        profile=dict(sex='male',age=25,training_months=36,body_mass_kg=80,healthy=True,lifts_weekly_last_6_months=True)
        setup=dict(mode='user_selected_source',accept_scope_limits=True,rest_seconds=300,equipment_step_kg=2.5,warmup='user-defined')
        snapshot=prepare(make_instance(source,'1RMG',profile,records,setup,'2026-10-12T09:00:00Z'),
                         1,1,'2026-10-12T09:00:00Z',[])
        self.db.create('a','w',snapshot)
        app.dependency_overrides[owner]=lambda:self.user
        app.dependency_overrides[store]=lambda:self.db
        self.client=TestClient(app)
        self.item=dict(id=PACKET['id'],version=digest(PACKET),status='research_preview',definition=PACKET)
        self.mock=patch('backend.context_api.context_catalog',return_value={'schema_version':1,'items':[self.item]})
        self.catalog=self.mock.start()
        self.url='/v3/workouts/w/evidence?evidence_version='+digest(PACKET)
    def tearDown(self):
        self.mock.stop();app.dependency_overrides.clear();self.tmp.cleanup()
    def test_owner_revision_and_no_write(self):
        before=self.db.get('a','w')
        response=self.client.get(self.url+'&topic=volume')
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['evidence_version'],digest(PACKET))
        self.assertEqual(self.db.get('a','w'),before)
        self.user='b';self.catalog.reset_mock()
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.catalog.assert_not_called()
    def test_actual_set_and_rest_events_drive_guidance(self):
        sid=self.db.get('a','w')['execution']['sets'][0]['id']
        self.db.append('a','w',0,dict(id='set1',type='set_result',set_id=sid,reps=7,
                       reason='fatigue',at='2026-10-12T09:01:00Z'))
        self.db.append('a','w',1,dict(id='rest1',type='rest_end',outcome='skipped',
                       at='2026-10-12T09:03:00Z'))
        response=self.client.get(self.url)
        self.assertEqual(response.status_code,200,response.text)
        out=response.json()
        self.assertEqual(out['execution_revision'],2)
        self.assertEqual(out['facts']['short_rests'][0]['shortfall_seconds'],180)
        self.assertEqual(out['cards'][0]['source']['topic'],'rest')
        self.assertIsNone(out['prescription_change'])
    def test_suspended_and_outage_leave_record_readable(self):
        self.item['status']='suspended'
        self.assertEqual(self.client.get(self.url).status_code,503)
        self.catalog.side_effect=CatalogUnavailable('offline')
        self.assertEqual(self.client.get(self.url).status_code,503)
        self.assertEqual(self.client.get('/v2/workouts/w').status_code,200)
    def test_unknown_topic_and_missing_version(self):
        self.assertEqual(self.client.get(self.url+'&topic=magic').status_code,422)
        self.assertEqual(self.client.get('/v3/workouts/w/evidence').status_code,422)
    def test_auth_required(self):
        app.dependency_overrides.pop(owner)
        self.assertEqual(self.client.get(self.url).status_code,401)

if __name__ == '__main__': unittest.main()
