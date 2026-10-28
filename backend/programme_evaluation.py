"""Append-only owner-scoped programme closure and explicitly comparable measurements."""
import json
from research_engine.core import digest
from research_engine.workout import timestamp,require
from research_engine.programme_dispatch import exercises
from .workout_store import Conflict,replay
from . import coaching_store

def project_evaluation(payload, results):
    from copy import deepcopy
    from .experience_content import programme_analysis
    value=deepcopy(payload)
    value['analysis']=programme_analysis(value,results)
    return value

def project_stored(db,user,instance_id,payload):
    history=coaching_store.history(db,user,instance_id)
    # Only records referenced by this evaluation revision; never append later history.
    indexed={x['workout_id']:x for x in history}
    results=[]
    for ref in payload['history_inputs']:
        row=indexed[ref['workout_id']]
        events=row['events'][:ref['revision']]
        require(digest(events)==ref['events_sha256'],'EVALUATION_HISTORY_MISMATCH')
        results.append(replay(row['snapshot'],events))
    return project_evaluation(payload,results)

def list_evaluations(db,user,instance_id):
    coaching_store.instance(db,user,instance_id)
    with db.connect() as c:
        payloads=[json.loads(r[0]) for r in c.execute('SELECT payload FROM coaching_evaluations WHERE owner=? AND instance_id=? ORDER BY revision',(user,instance_id))]
    return [project_stored(db,user,instance_id,p) for p in payloads]

def evaluate(db,user,instance_id,request):
    instance=coaching_store.instance(db,user,instance_id)
    fingerprint=digest(request);at=timestamp(request['at'])
    require(request['outcome'] in ('completed','stopped'),'INVALID_PROGRAMME_OUTCOME')
    expected=set(exercises(instance['source']))
    require(set(request['post_max_record_ids'])<=expected and set(request['comparison_conditions'])<=expected,'UNEXPECTED_EXERCISE')
    require(all(x in ('same','different','unknown') for x in request['comparison_conditions'].values()),'INVALID_COMPARISON_CONDITIONS')
    with db.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        old=c.execute('SELECT fingerprint,payload FROM coaching_evaluations WHERE owner=? AND instance_id=? AND id=?',(user,instance_id,request['id'])).fetchone()
        if old:
            if old[0]!=fingerprint:raise Conflict('EVALUATION_ID_CONFLICT')
            return project_stored(db,user,instance_id,json.loads(old[1]))
        latest=c.execute('SELECT id,revision,payload FROM coaching_evaluations WHERE owner=? AND instance_id=? ORDER BY revision DESC LIMIT 1',(user,instance_id)).fetchone()
        if request.get('supersedes_id')!=(latest[0] if latest else None):raise Conflict('EVALUATION_REVISION_CONFLICT')
        if latest:
            prior=json.loads(latest[2])
            require(at>=timestamp(prior['at']),'EVALUATION_TIME_ORDER')
            require(request['outcome']==prior['outcome'],'PROGRAMME_OUTCOME_IMMUTABLE')
        sessions=c.execute('SELECT s.workout_id,w.snapshot,w.events,w.revision FROM coaching_sessions s JOIN execution_workouts w ON w.owner=s.owner AND w.id=s.workout_id WHERE s.owner=? AND s.instance_id=? ORDER BY s.week,s.day',(user,instance_id)).fetchall()
        require(bool(sessions),'NO_TRAINING_HISTORY')
        results=[];last_at=timestamp(instance['created_at']);last_event_at=last_at;refs=[]
        for wid,snapshot,events,revision in sessions:
            snap=json.loads(snapshot);ev=json.loads(events);execution=replay(snap,ev)
            require(execution['state'] in ('completed','stopped'),'PREVIOUS_SESSION_OPEN')
            last_event_at=max(last_event_at,timestamp(ev[-1]['at']))
            last_at=max(last_at,max(timestamp(e['at']) for e in ev if e['type'] in ('finish','interrupt')))
            results.append(execution)
            refs.append({'workout_id':wid,'revision':revision,'events_sha256':digest(ev)})
        require(at>=last_event_at,'EVALUATION_BEFORE_LATEST_RECORD')
        source=instance['source']
        planned=(len(source['protocol']['sessions']) if 'sessions' in source['protocol'] else
                 sum(d.get('kind')!='post_test' for w in source['protocol']['weeks'] for d in w['days']))
        if request['outcome']=='completed':require(len(sessions)==planned,'PROGRAMME_NOT_FINISHED')
        baselines={r['exercise_id']:r for r in instance['max_records']};lifts=[]
        for eid in exercises(source):
            base=baselines.get(eid);rid=request['post_max_record_ids'].get(eid);post=None;status='not_measured'
            condition=request['comparison_conditions'].get(eid,'unknown')
            if rid:
                row=c.execute('SELECT payload FROM execution_maxes WHERE owner=? AND id=?',(user,rid)).fetchone()
                require(row is not None,'POST_MAX_NOT_FOUND');post=json.loads(row[0])
                require(post['exercise_id']==eid,'POST_MAX_EXERCISE_MISMATCH')
                require(last_at<=timestamp(post['measured_at'])<=at,'POST_MAX_TIME_INVALID')
                status=('baseline_not_recorded' if base is None else 'estimated' if post['kind']!='measured' else 'baseline_estimated' if base['kind']!='measured'
                        else ('comparable' if condition=='same' else 'conditions_'+condition))
            delta=post['weight_kg']-base['weight_kg'] if status=='comparable' else None
            lifts.append({'exercise_id':eid,'baseline':base,'post':post,'comparison_conditions':condition,
                'conditions_basis':'user_self_report','status':status,'delta_kg':delta,
                'change_percent':round(delta/base['weight_kg']*100,4) if delta is not None else None})
        all_rows=[r for result in results for r in result['sets']]
        # A four-lift programme must not add OHP to the powerlifting total.
        total_lifts = ([x for x in lifts if x['exercise_id'] in ('barbell_back_squat','barbell_bench_press','barbell_deadlift')]
                       if source.get('adapter_version') in ('petrizzo-2018-v1','sbd-template-v1','per-source-labels-v1') else lifts)
        payload={'id':request['id'],'instance_id':instance_id,'revision':latest[1]+1 if latest else 1,
            'supersedes_id':request.get('supersedes_id'),'at':request['at'],'outcome':request['outcome'],
            'programme_version':instance['programme_version'],'history_inputs':refs,'lifts':lifts,
            'total_delta_kg':sum(x['delta_kg'] for x in total_lifts) if all(x['delta_kg'] is not None for x in total_lifts) else None,
            'training':{'planned_sessions':planned,'closed_sessions':len(results),
                'completed_sessions':sum(x['state']=='completed' for x in results),
                'stopped_sessions':sum(x['state']=='stopped' for x in results),
                'recorded_sets':sum(r['actual'] is not None for r in all_rows),
                'changed_sets':sum(bool(r['changes']) for r in all_rows),
                'rest_count':sum(len(x['rests']) for x in results)},
            'growth_prediction':None,'causal_effect':None,
            'next_actions':['review_actuals','choose_next_programme','register_optional_post_test'],
            'interpretation':'Measured change is descriptive, not proof the programme caused it. No automatic next-cycle load.'}
        c.execute('INSERT INTO coaching_evaluations VALUES(?,?,?,?,?,?,?)',(user,instance_id,request['id'],payload['revision'],fingerprint,json.dumps(payload),request['at']))
        return project_evaluation(payload,results)
