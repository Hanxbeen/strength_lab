"""Transport contract tests, not a claim of deployed Postgres end-to-end coverage."""
import unittest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace
from fastapi import HTTPException
from backend.postgres_store import LedgerConnection, PostgresWorkoutStore
from backend.workout_api import store, execute
from backend.workout_store import Conflict, StorageUnavailable

OWNER = '00000000-0000-4000-8000-000000000001'

class PostgresTransportTests(unittest.TestCase):
    def test_parameters_stay_bound(self):
        raw = MagicMock()
        db = LedgerConnection(raw, OWNER)
        params = (OWNER, "literal?'%s", '{}')
        db.execute('INSERT OR IGNORE INTO execution_maxes VALUES(?,?,?)', params)
        raw.execute.assert_called_once_with(
            'INSERT INTO execution_maxes VALUES(%s,%s,%s) ON CONFLICT DO NOTHING', params)

    def test_owner_lock(self):
        raw = MagicMock()
        LedgerConnection(raw, OWNER).execute('BEGIN IMMEDIATE')
        raw.execute.assert_called_once_with(
            'SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
            ('execution-ledger:' + OWNER,))

    def test_role_claims_ssl_and_transaction(self):
        connection = MagicMock()
        factory = MagicMock()
        factory.return_value.__enter__.return_value = connection
        driver = SimpleNamespace(connect=factory, IntegrityError=type('Integrity', (Exception,), {}),
                                 Error=type('DriverError', (Exception,), {}))
        with patch.dict('sys.modules', {'psycopg': driver}):
            with PostgresWorkoutStore('test-only-dsn', OWNER).connect() as db:
                db.execute('SELECT payload FROM execution_maxes WHERE owner=?', (OWNER,))
        self.assertEqual(connection.execute.call_args_list[0].args, ('SET LOCAL ROLE authenticated',))
        claims = connection.execute.call_args_list[1].args
        self.assertIn(OWNER, claims[1][0])
        self.assertEqual(factory.call_args.kwargs['sslmode'], 'verify-full')
        self.assertIsNone(factory.call_args.kwargs['prepare_threshold'])
        factory.return_value.__exit__.assert_called_once_with(None, None, None)

    def test_database_failure_is_sanitized(self):
        error = type('DriverError', (Exception,), {})
        integrity = type('Integrity', (error,), {})
        driver = SimpleNamespace(connect=MagicMock(side_effect=error('secret-dsn')),
                                 IntegrityError=integrity, Error=error)
        with patch.dict('sys.modules', {'psycopg': driver}):
            with self.assertRaises(HTTPException) as caught:
                execute(lambda: PostgresWorkoutStore('secret-dsn', OWNER).maxes(OWNER))
        self.assertEqual(caught.exception.status_code, 503)
        self.assertNotIn('secret', caught.exception.detail)

    def test_vercel_cannot_fallback_to_sqlite(self):
        with patch.dict('os.environ', {'VERCEL':'1','WORKOUT_DATABASE_PATH':'/tmp/unsafe.sqlite'}, clear=True):
            with self.assertRaises(HTTPException) as caught:
                store(OWNER)
        self.assertEqual(caught.exception.status_code, 503)

    def test_configured_postgres_is_selected(self):
        with patch.dict('os.environ', {'WORKOUT_POSTGRES_DSN':'test-only','VERCEL':'1'}, clear=True):
            self.assertIsInstance(store(OWNER), PostgresWorkoutStore)

    def test_invalid_owner_rejected_before_connection(self):
        with self.assertRaises(ValueError):
            PostgresWorkoutStore('test-only', 'unverified-owner')

if __name__ == '__main__':
    unittest.main()
