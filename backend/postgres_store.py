"""Server-only Postgres transport for the existing execution ledger.

Use a configured backend DSN, never a client-supplied connection string.
Queries run as authenticated under RLS after Supabase Auth verifies the owner.
The small SQL adaptation covers this repository's parameterized ledger queries.
"""
import json
from contextlib import contextmanager
from uuid import UUID

from .workout_store import WorkoutStore, Conflict, StorageUnavailable


class LedgerConnection:
    def __init__(self, connection, owner):
        self.connection = connection
        self.owner = owner

    def execute(self, statement, params=()):
        if statement.strip() == 'BEGIN IMMEDIATE':
            # Serialize writes per owner, including first inserts with no row to lock.
            return self.connection.execute(
                'SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))',
                ('execution-ledger:' + self.owner,))
        if statement.startswith('INSERT OR IGNORE INTO '):
            statement = statement.replace('INSERT OR IGNORE INTO ', 'INSERT INTO ', 1)
            statement = statement.rstrip(';') + ' ON CONFLICT DO NOTHING'
        # Ledger SQL contains no literal question marks; user values are parameters.
        return self.connection.execute(statement.replace('?', '%s'), params)


class PostgresWorkoutStore(WorkoutStore):
    schema_managed = True

    def __init__(self, dsn, owner, sslrootcert='system'):
        self.dsn = dsn
        self.owner = str(UUID(owner))
        self.sslrootcert = sslrootcert

    @contextmanager
    def connect(self):
        try:
            import psycopg
        except ImportError as error:
            raise StorageUnavailable('Postgres driver unavailable') from error
        try:
            with psycopg.connect(self.dsn, prepare_threshold=None, connect_timeout=10,
                                 sslmode='verify-full', sslrootcert=self.sslrootcert) as connection:
                connection.execute("SET LOCAL ROLE authenticated")
                connection.execute("SELECT set_config('request.jwt.claims', %s, true)",
                                   (json.dumps({'sub': self.owner, 'role': 'authenticated'}),))
                connection.execute("SET LOCAL search_path TO execution_private, pg_catalog")
                connection.execute("SET LOCAL statement_timeout TO '15s'")
                connection.execute("SET LOCAL lock_timeout TO '5s'")
                yield LedgerConnection(connection, self.owner)
        except psycopg.IntegrityError as error:
            raise Conflict('DATABASE_CONSTRAINT_CONFLICT') from error
        except psycopg.Error as error:
            # Do not return connection strings, credentials or raw driver errors.
            raise StorageUnavailable('Execution database unavailable') from error
