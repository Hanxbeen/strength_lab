"""Lifecycle boundary and factual-result regression tests using a real source fixture."""
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore, Conflict
from backend.workout_result import project
from research_engine.core import InvalidProgramme
import test_workout_execution as fixtures


class ResultTests(unittest.TestCase):
    def setUp(self):
        fixtures.WorkoutTests.setUpClass()
        self.f = fixtures.WorkoutTests(); self.f.setUp()
        self.folder = tempfile.TemporaryDirectory()
        self.db = WorkoutStore(Path(self.folder.name)/'ledger.sqlite')
        self.db.create('a','w',self.f.snapshot)
        self.start = datetime(2026,10,11,10,tzinfo=timezone.utc)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.folder.cleanup()

    def append(self, event):
        rev=self.db.get('a','w')['execution']['revision']
        return self.db.append('a','w',rev,event)

    def reconcile(self, seconds):
        return self.db.reconcile_inactivity('a','w',self.start+timedelta(seconds=seconds))

    def test_hour_boundary_and_unknown_not_failure(self):
        self.assertEqual(self.reconcile(3599)['execution']['state'],'active')
        out=self.reconcile(3600)
        self.assertEqual(out['execution']['state'],'stopped')
        self.assertIsNone(out['execution']['summary']['minimum_reps_completion_percent'])
        result=project(out)
        self.assertGreater(result['counts']['unknown'],0)
        self.assertEqual(result['counts']['not_attempted'],0)
        self.assertFalse(result['resume_available'])
        self.assertEqual(self.reconcile(7200)['execution']['revision'],1)
        with self.assertRaisesRegex(InvalidProgramme,'WORKOUT_CLOSED'):
            self.append(self.f.event('resume',7201))

    def test_activity_resets_deadline_not_total_workout_duration(self):
        self.append(self.f.event('change_load',3500,set_id=self.f.first,value=80,unit='kg',reason='fatigue'))
        self.assertEqual(self.reconcile(3600)['execution']['state'],'active')
        self.assertEqual(self.reconcile(7100)['execution']['state'],'stopped')

    def test_rest_changes_keep_plan_and_actual(self):
        self.append(self.f.result())
        plan=self.db.get('a','w')['execution']['active_rest']['target_seconds']
        self.append(self.f.event('rest_adjust',20,target_seconds=300))
        self.append(self.f.event('rest_adjust',30,target_seconds=60))
        out=self.append(self.f.event('rest_end',70,outcome='completed'))
        rest=project(out)['charts']['rests'][0]
        self.assertEqual((rest['planned_seconds'],rest['selected_seconds'],rest['actual_seconds']),(plan,60,60))
        self.assertEqual(len(rest['adjustments']),2)
        self.assertEqual(rest['delta_from_plan_seconds'],60-plan)

    def test_abandoned_rest_is_not_one_hour_confirmed_recovery(self):
        self.append(self.f.result())
        out=self.reconcile(3610)
        rest=project(out)['charts']['rests'][0]
        self.assertIsNone(rest['actual_seconds'])
        self.assertIsNone(rest['delta_from_plan_seconds'])
        self.assertEqual(rest['measurement_status'],'unconfirmed')

    def test_changed_weight_baseline_and_no_grade(self):
        self.append(self.f.event('change_load',1,set_id=self.f.first,value=60,unit='kg',reason='fatigue'))
        out=self.append(self.f.result(reps=2))
        result=project(out)
        point=result['charts']['sets_by_exercise']['barbell_half_squat'][0]
        self.assertEqual(point['actual_percent_reference_max'],60)
        self.assertEqual(point['target_percent_reference_max'],85)
        self.assertEqual(point['actual_reps'],2)
        self.assertIsNone(result['assessment'])
        self.assertIsNone(result['charts']['research_growth_slope'])
        self.assertFalse(result['coaching']['available'])

    def test_explicit_stop_keeps_missing_unknown(self):
        out=self.append(self.f.event('interrupt',20,reason='user_interruption'))
        self.assertEqual(out['execution']['state'],'stopped')
        self.assertEqual(project(out)['counts']['not_attempted'],0)

    def test_closed_workout_unchanged_and_owner_isolation(self):
        out=self.append(self.f.event('finish',20,reason='time'))
        self.assertEqual(self.reconcile(8000),out)
        with self.assertRaises(KeyError): self.db.reconcile_inactivity('b','w',self.start+timedelta(hours=2))

    def test_api_result_reconcile_and_no_client_system_event(self):
        app.dependency_overrides[owner]=lambda:'a'
        app.dependency_overrides[store]=lambda:self.db
        client=TestClient(app)
        self.assertEqual(client.get('/v2/workouts/w/result').status_code,200)
        response=client.post('/v2/workouts/w/reconcile')
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['state'],'stopped')
        response=client.post('/v2/workouts/w/events',json={'expected_revision':1,
            'event':self.f.event('interrupt',9000,reason='inactivity')})
        self.assertEqual(response.status_code,422)
        app.dependency_overrides[owner]=lambda:'b'
        self.assertEqual(client.get('/v2/workouts/w/result').status_code,404)

    def test_retry_and_stale_revision_after_reconcile(self):
        event=self.f.result()
        self.append(event)
        self.reconcile(3610)
        self.assertEqual(self.db.append('a','w',0,event)['execution']['state'],'stopped')
        with self.assertRaisesRegex(Conflict,'STALE_REVISION'):
            self.db.append('a','w',1,self.f.event('rest_end',3620,outcome='completed'))

    def test_invalid_rest_change_is_atomic(self):
        self.append(self.f.result())
        before=self.db.get('a','w')
        with self.assertRaisesRegex(InvalidProgramme,'INVALID_REST_TARGET'):
            self.append(self.f.event('rest_adjust',20,target_seconds=-1))
        self.assertEqual(self.db.get('a','w'),before)
