"""Durable single-server ledger. Owner comes only from verified authentication.

Not a replacement for the existing iOS cloud sync. Set WORKOUT_DATABASE_PATH
to a persistent private volume; missing configuration fails closed.
"""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from research_engine.core import InvalidProgramme, digest
from research_engine.workout import max_record, replay as base_replay

def replay(snapshot, events):
    result = base_replay(snapshot, events)
    if snapshot.get("coaching"):
        from research_engine.coaching import enrich
        return enrich(snapshot, result)
    return result


class Conflict(ValueError):
    pass

class WorkoutStore:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS execution_maxes (
                  owner TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL,
                  PRIMARY KEY(owner,id));
                CREATE TABLE IF NOT EXISTS execution_workouts (
                  owner TEXT NOT NULL, id TEXT NOT NULL, snapshot TEXT NOT NULL,
                  events TEXT NOT NULL, revision INTEGER NOT NULL,
                  PRIMARY KEY(owner,id));
            ''')

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def register_max(self, owner, record):
        value = max_record(record)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT payload FROM execution_maxes WHERE owner=? AND id=?', (owner, value['id'])).fetchone()
            if old and json.loads(old[0]) != value: raise Conflict('MAX_ID_CONFLICT')
            db.execute('INSERT OR IGNORE INTO execution_maxes VALUES (?,?,?)', (owner, value['id'], json.dumps(value)))
        return value

    def maxes(self, owner):
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT payload FROM execution_maxes WHERE owner=? ORDER BY id', (owner,))]

    def create(self, owner, id, snapshot):
        replay(snapshot, [])
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT snapshot FROM execution_workouts WHERE owner=? AND id=?', (owner, id)).fetchone()
            if old and digest(json.loads(old[0])) != digest(snapshot): raise Conflict('WORKOUT_ID_CONFLICT')
            db.execute('INSERT OR IGNORE INTO execution_workouts VALUES (?,?,?,?,0)', (owner, id, json.dumps(snapshot), '[]'))
        return self.get(owner, id)

    def get(self, owner, id):
        with self.connect() as db:
            row = db.execute('SELECT snapshot,events FROM execution_workouts WHERE owner=? AND id=?', (owner, id)).fetchone()
        if not row: raise KeyError('WORKOUT_NOT_FOUND')
        snapshot, events = map(json.loads, row)
        return {'workout_id': id, 'execution': replay(snapshot, events), 'events': events}

    def append(self, owner, id, expected_revision, event):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT snapshot,events,revision FROM execution_workouts WHERE owner=? AND id=?', (owner, id)).fetchone()
            if not row: raise KeyError('WORKOUT_NOT_FOUND')
            snapshot, events = json.loads(row[0]), json.loads(row[1])
            old = next((e for e in events if e['id'] == event.get('id')), None)
            if old is not None:
                if digest(old) != digest(event): raise Conflict('EVENT_ID_CONFLICT')
            else:
                if expected_revision != row[2]: raise Conflict('STALE_REVISION')
                events.append(event)
                result = replay(snapshot, events)
                db.execute('UPDATE execution_workouts SET events=?,revision=? WHERE owner=? AND id=?',
                           (json.dumps(events), result['revision'], owner, id))
            result = replay(snapshot, events)
        return {'workout_id': id, 'execution': result, 'events': events}
