"""Runtime contracts; mocked Auth/DB transports are not live integration evidence."""
import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore, StorageUnavailable
from backend.coaching_store import initialize

USER = '00000000-0000-4000-8000-000000000001'

class AuthBoundaryTests(unittest.TestCase):
    def test_malformed_success_responses_fail_closed(self):
        for value in (None, [], {}, {'id':None}, {'id':123}, {'id':'bad'}):
            with self.subTest(value=value), patch.dict(os.environ, {
                'SUPABASE_URL':'https://example.invalid', 'SUPABASE_PUBLISHABLE_KEY':'test'}, clear=True), \
                patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(value).encode())):
                with self.assertRaises(HTTPException) as caught:
                    owner('Bearer test')
                self.assertEqual(caught.exception.status_code,503)

    def test_verified_owner_comes_from_auth_response(self):
        with patch.dict(os.environ, {'SUPABASE_URL':'https://example.invalid',
              'SUPABASE_PUBLISHABLE_KEY':'test'}, clear=True), \
              patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps({'id':USER}).encode())):
            self.assertEqual(owner('Bearer test'),USER)

    def test_expired_token_and_provider_failure_are_distinct(self):
        for upstream,expected in ((401,401),(403,401),(429,503),(500,503)):
            with self.subTest(upstream=upstream), patch.dict(os.environ, {
                'SUPABASE_URL':'https://example.invalid','SUPABASE_PUBLISHABLE_KEY':'test'},clear=True), \
                patch('urllib.request.urlopen',side_effect=urllib.error.HTTPError(
                    'https://example.invalid',upstream,'private upstream text',{},None)):
                with self.assertRaises(HTTPException) as caught:
                    owner('Bearer test')
                self.assertEqual(caught.exception.status_code,expected)
                self.assertNotIn('private',str(caught.exception.detail))

    def test_host_independent_production_requires_postgres(self):
        for mode in ('production','staging'):
            with self.subTest(mode=mode),patch.dict(os.environ,{
                'MUGEMUGE_ENV':mode,'WORKOUT_DATABASE_PATH':'/tmp/not-production.sqlite'},clear=True):
                with self.assertRaises(HTTPException) as caught:store(USER)
                self.assertEqual(caught.exception.status_code,503)

class RuntimeReadinessTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.db=WorkoutStore(Path(self.folder.name)/'ledger.sqlite')
        initialize(self.db)
        app.dependency_overrides[owner]=lambda:USER
        app.dependency_overrides[store]=lambda:self.db
        self.client=TestClient(app)
        self.data={'coverage':{'entry':{'learning_path_count':1}},
                   'supply_audit':{'all_levels_data_ready':True}}
        self.catalog=patch('backend.coaching_api.routines',return_value=self.data)
        self.catalog.start()
    def tearDown(self):
        self.catalog.stop();app.dependency_overrides.clear();self.folder.cleanup()

    def test_readiness_does_not_claim_writes_or_create_records(self):
        response=self.client.get('/v3/runtime-readiness')
        self.assertEqual(response.status_code,200,response.text)
        data=response.json()
        self.assertTrue(data['ready']);self.assertFalse(data['write_verified'])
        self.assertFalse(data['client_execution_verified'])
        self.assertEqual(data['storage'],'local_sqlite')
        with self.db.connect() as c:
            for table in ('execution_maxes','execution_workouts','coaching_instances','coaching_evaluations'):
                self.assertEqual(c.execute('SELECT count(*) FROM '+table).fetchone()[0],0)

    def test_incomplete_supply_is_not_ready(self):
        self.data['supply_audit']['all_levels_data_ready']=False
        response=self.client.get('/v3/runtime-readiness')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['checks']['catalogue'],'incomplete')

    def test_missing_migration_is_not_ready(self):
        with self.db.connect() as c:c.execute('DROP TABLE coaching_evaluations')
        response=self.client.get('/v3/runtime-readiness')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['checks']['ledger'],'unavailable')

    def test_catalogue_outage_is_distinct_from_empty_supply(self):
        with patch('backend.coaching_api.routines',side_effect=HTTPException(503,'secret detail')):
            response=self.client.get('/v3/runtime-readiness')
        self.assertEqual(response.status_code,503)
        self.assertEqual(response.json()['checks']['catalogue'],'unavailable')
        self.assertNotIn('secret',response.text)

    def test_database_outage_is_sanitized(self):
        with patch.object(self.db,'connect',side_effect=StorageUnavailable('secret-dsn')):
            response=self.client.get('/v3/runtime-readiness')
        self.assertEqual(response.status_code,503)
        self.assertNotIn('secret',response.text)

    def test_readiness_requires_login(self):
        app.dependency_overrides.pop(owner)
        self.assertEqual(self.client.get('/v3/runtime-readiness').status_code,401)

if __name__=='__main__':unittest.main()
