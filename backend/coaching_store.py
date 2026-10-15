"""Owner-scoped programme instances linked to the existing durable workout ledger."""
import json
from research_engine.core import digest
from research_engine.workout import replay, timestamp, require
from research_engine.programme_dispatch import enrich
from .workout_store import Conflict

def initialize(db):
    with db.connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS coaching_instances(
          owner TEXT NOT NULL,id TEXT NOT NULL,payload TEXT NOT NULL,PRIMARY KEY(owner,id));
        CREATE TABLE IF NOT EXISTS coaching_sessions(
          owner TEXT NOT NULL,instance_id TEXT NOT NULL,week INTEGER NOT NULL,day INTEGER NOT NULL,
          workout_id TEXT NOT NULL,PRIMARY KEY(owner,instance_id,week,day),UNIQUE(owner,workout_id));
        CREATE TABLE IF NOT EXISTS coaching_evaluations(
          owner TEXT NOT NULL,instance_id TEXT NOT NULL,id TEXT NOT NULL,revision INTEGER NOT NULL,
          fingerprint TEXT NOT NULL,payload TEXT NOT NULL,at TEXT NOT NULL,
          PRIMARY KEY(owner,instance_id,id),UNIQUE(owner,instance_id,revision));
        """)

def instance(db,user,id):
    initialize(db)
    with db.connect() as c:row=c.execute('SELECT payload FROM coaching_instances WHERE owner=? AND id=?',(user,id)).fetchone()
    if not row:raise KeyError(id)
    return json.loads(row[0])

def save_instance(db,user,id,value):
    initialize(db)
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        old=c.execute('SELECT payload FROM coaching_instances WHERE owner=? AND id=?',(user,id)).fetchone()
        if old and digest(json.loads(old[0]))!=digest(value):raise Conflict('INSTANCE_ID_CONFLICT')
        c.execute('INSERT OR IGNORE INTO coaching_instances VALUES(?,?,?)',(user,id,json.dumps(value)))
    return value

def history(db,user,id):
    initialize(db)
    with db.connect() as c:
        rows=c.execute('SELECT s.week,s.day,s.workout_id,w.snapshot,w.events FROM coaching_sessions s JOIN execution_workouts w ON w.owner=s.owner AND w.id=s.workout_id WHERE s.owner=? AND s.instance_id=? ORDER BY s.week,s.day',(user,id)).fetchall()
    return [{'week':w,'day':d,'workout_id':wid,'snapshot':json.loads(s),
             'execution':enrich(json.loads(s),replay(json.loads(s),json.loads(e))),'events':json.loads(e)}
            for w,d,wid,s,e in rows]

def start(db,user,id,wid,week,day,snapshot):
    initialize(db);replay(snapshot,[])
    ordinal=(week-1)*3+day
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        old=c.execute('SELECT w.id,w.snapshot FROM coaching_sessions s JOIN execution_workouts w ON w.owner=s.owner AND w.id=s.workout_id WHERE s.owner=? AND s.instance_id=? AND s.week=? AND s.day=?',(user,id,week,day)).fetchone()
        if old:
            if old[0]!=wid or digest(json.loads(old[1]))!=digest(snapshot):raise Conflict('SESSION_ALREADY_STARTED')
        else:
            if c.execute('SELECT 1 FROM coaching_evaluations WHERE owner=? AND instance_id=?',(user,id)).fetchone():
                raise Conflict('PROGRAMME_CLOSED')
            prior=c.execute('SELECT s.week,s.day,w.snapshot,w.events FROM coaching_sessions s JOIN execution_workouts w ON w.owner=s.owner AND w.id=s.workout_id WHERE s.owner=? AND s.instance_id=? ORDER BY s.week,s.day',(user,id)).fetchall()
            if len(prior)!=ordinal-1:raise Conflict('SEQUENTIAL_SESSION_REQUIRED')
            if prior:
                first=json.loads(prior[0][2])
                nominal_days=(week-1)*7+(day-1)*2
                require((timestamp(snapshot['started_at'])-timestamp(first['started_at'])).total_seconds()>=nominal_days*86400,
                        'SOURCE_SCHEDULE_COMPRESSED')
            for pw,pd,ps,pe in prior:
                result=replay(json.loads(ps),json.loads(pe))
                if result['state'] not in ('completed','stopped'):raise Conflict('PREVIOUS_SESSION_OPEN')
            if prior:
                last=json.loads(prior[-1][2]);events=json.loads(prior[-1][3])
                require(timestamp(snapshot['started_at'])>=timestamp(events[-1]['at']), 'SESSION_TIME_ORDER')
                # A 48-hour minimum is a conservative product policy, not a quoted research threshold.
                require((timestamp(snapshot['started_at'])-timestamp(last['started_at'])).total_seconds()>=172800,
                        'NONCONSECUTIVE_DAYS_REQUIRED')
            if c.execute('SELECT 1 FROM execution_workouts WHERE owner=? AND id=?',(user,wid)).fetchone():raise Conflict('WORKOUT_ID_CONFLICT')
            c.execute('INSERT INTO execution_workouts VALUES(?,?,?,?,0)',(user,wid,json.dumps(snapshot),'[]'))
            c.execute('INSERT INTO coaching_sessions VALUES(?,?,?,?,?)',(user,id,week,day,wid))
    return db.get(user,wid)
