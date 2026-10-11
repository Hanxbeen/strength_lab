"""API integration on real source definitions; auth and remote catalog are isolated test doubles."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore
import test_workout_execution as fixtures

class WorkoutAPITests(unittest.TestCase):
    def setUp(self):
        fixtures.WorkoutTests.setUpClass()
        self.fixture = fixtures.WorkoutTests();self.fixture.setUp()
        self.folder = tempfile.TemporaryDirectory()
        self.db = WorkoutStore(Path(self.folder.name)/'test.sqlite')
        self.user = 'owner-a'
        app.dependency_overrides[owner] = lambda:self.user
        app.dependency_overrides[store] = lambda:self.db
        self.client = TestClient(app)
        self.catalog = patch('backend.workout_api.source_catalog', return_value={'items':[self.fixture.bundle]})
        self.catalog.start()

    def tearDown(self):
        self.catalog.stop();app.dependency_overrides.clear();self.folder.cleanup()

    def start(self):
        f=self.fixture
        self.assertEqual(self.client.post('/v2/max-records',json=f.record).status_code,200)
        return self.client.post('/v2/workouts',json={'workout_id':'w1','programme_id':f.bundle['programme_id'],
            'programme_version':f.bundle['programme_version'],'session_id':f.bundle['sessions'][0]['id'],
            'started_at':'2026-10-11T10:00:00Z','profile':f.profile,'setup':f.setup})

    def test_register_start_record_rest_finish_reload(self):
        self.assertEqual(self.start().status_code,200)
        events=[self.fixture.result(),self.fixture.event('rest_end',70,outcome='skipped'),self.fixture.event('finish',80,reason='time')]
        for revision,event in enumerate(events):
            response=self.client.post('/v2/workouts/w1/events',json={'expected_revision':revision,'event':event})
            self.assertEqual(response.status_code,200,response.text)
        loaded=self.client.get('/v2/workouts/w1').json()['execution']
        self.assertEqual(loaded['revision'],3);self.assertEqual(loaded['state'],'stopped')
        self.assertEqual(loaded['summary']['rest_shortfall_seconds'],120)

    def test_owner_and_stale_revision(self):
        self.start()
        self.user='owner-b'
        self.assertEqual(self.client.get('/v2/workouts/w1').status_code,404)
        self.assertEqual(self.client.get('/v2/max-records').json()['items'],[])
        self.user='owner-a'
        response=self.client.post('/v2/workouts/w1/events',json={'expected_revision':9,'event':self.fixture.result()})
        self.assertEqual(response.status_code,409)

    def test_anonymous_rejected(self):
        app.dependency_overrides.pop(owner)
        self.assertEqual(self.client.get('/v2/max-records').status_code,401)

    def test_bad_event_is_422_not_500(self):
        self.start()
        response=self.client.post('/v2/workouts/w1/events',json={'expected_revision':0,'event':{'id':'bad','type':'what','at':'invalid'}})
        self.assertEqual(response.status_code,422)

    def test_wrong_max_variant_cannot_start(self):
        self.fixture.record['exercise_id']='barbell_back_squat'
        self.assertEqual(self.start().status_code,422)

    def test_readiness_lists_missing_max_and_setup(self):
        f=self.fixture
        response=self.client.post('/v2/workout-readiness',json={'workout_id':'w1','programme_id':f.bundle['programme_id'],
            'programme_version':f.bundle['programme_version'],'session_id':f.bundle['sessions'][0]['id'],
            'started_at':'2026-10-11T10:00:00Z','profile':f.profile,'setup':{}})
        self.assertEqual(response.status_code,200)
        self.assertFalse(response.json()['ready'])
        self.assertIn('MEASURED_MAX_REQUIRED',[i['code'] for i in response.json()['issues']])
        self.assertEqual(len(response.json()['issues']),6)

if __name__=='__main__':unittest.main()
