"""Pure validation, compilation and explanation. No network or AI dependency."""
import copy
import hashlib
import json
import math
from decimal import Decimal, ROUND_HALF_UP

SCHEMA_VERSION = 2
ENGINE_VERSION = 'source-programme-v2'

class InvalidProgramme(ValueError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()

def number(value, lower, upper):
    return type(value) in (int, float) and math.isfinite(value) and lower <= value <= upper

def validate(p):
    errors = []
    if p.get('schema_version') != SCHEMA_VERSION: errors.append('schema')
    source = p.get('source', {})
    if len(source.get('sha256', '')) != 64: errors.append('source_digest')
    if not source.get('pmid') or not source.get('url'): errors.append('source_identity')
    if not p.get('population') or not p.get('context'): errors.append('context')
    if not number(p.get('weeks'), 1, 104) or type(p.get('weeks')) != int: errors.append('weeks')
    if not number(p.get('sessions_per_week'), 1, 7) or type(p.get('sessions_per_week')) != int: errors.append('frequency')
    movements = p.get('exercises', [])
    if not movements: errors.append('empty_exercises')
    ids = [x.get('id') for x in movements]
    if len(ids) != len(set(ids)) or any(not x for x in ids): errors.append('exercise_identity')
    for x in movements:
        if type(x.get('sets')) != int or not number(x.get('sets'), 1, 30): errors.append('sets')
        reps = x.get('reps', {})
        if not number(reps.get('min'), 1, 100) or not number(reps.get('max'), 1, 100) or reps.get('min', 0) > reps.get('max', 0): errors.append('reps')
        load = x.get('load', {})
        if load.get('kind') not in ('initial_percent_1rm', 'rir', 'repetition_maximum'): errors.append('load_kind')
        if load.get('kind') == 'initial_percent_1rm' and (not number(load.get('percent'), 1, 100) or load.get('reference_exercise') != x.get('id')): errors.append('load_reference')
        if load.get('kind') == 'rir' and not number(load.get('target'), 0, 10): errors.append('rir')
        if load.get('kind') == 'repetition_maximum' and load.get('failure') != 'momentary_concentric': errors.append('failure_definition')
        rest = x.get('rest', {})
        if rest.get('operator') not in ('eq', 'gte') or not number(rest.get('seconds'), 1, 3600): errors.append('rest')
    # Every execution field must resolve to a source locator or an explicit policy.
    required = ['weeks', 'sessions_per_week', 'population', 'context', 'progression', 'spacing', 'order']
    required += ['exercises.'+str(i)+'.'+f for i in range(len(movements)) for f in ('id','sets','reps','load','rest','tempo')]
    for key in required:
        proof = p.get('provenance', {}).get(key, {})
        if proof.get('kind') not in ('source_reported', 'product_policy', 'not_reported'): errors.append('provenance:'+key)
        value=p
        for segment in key.split('.'):
            value=value[int(segment)] if isinstance(value,list) else value[segment]
        if proof.get('value_sha256') != digest(value): errors.append('changed_value:'+key)
        if proof.get('kind') == 'source_reported' and (not proof.get('locator') or proof.get('source_sha256') != source.get('sha256')): errors.append('source_link:'+key)
        if proof.get('kind') == 'product_policy' and not proof.get('policy_id'): errors.append('policy_link:'+key)
    if errors: raise InvalidProgramme(','.join(errors))

def compile_programme(p):
    validate(p)
    sessions = []
    for week in range(1, p['weeks']+1):
        for ordinal in range(1, p['sessions_per_week']+1):
            steps = []
            for exercise in p['exercises']:
                for n in range(1, exercise['sets']+1):
                    steps.append({'id':f"{exercise['id']}:{n}", 'exercise_id':exercise['id'], 'set':n,
                                  'reps':copy.deepcopy(exercise['reps']), 'load':copy.deepcopy(exercise['load']),
                                  'tempo':copy.deepcopy(exercise['tempo']),
                                  'rest_after':copy.deepcopy(exercise['rest']) if n < exercise['sets'] else None})
            sessions.append({'id':f'{p["id"]}:w{week}:s{ordinal}', 'week':week, 'ordinal':ordinal, 'sets':steps,
                             'between_exercise_rest':p['context']['between_exercise_rest']})
    version = digest({'definition':p,'compiler':ENGINE_VERSION})
    return {'schema_version':2, 'engine_version':ENGINE_VERSION, 'programme_id':p['id'],
            'programme_version':version, 'definition':copy.deepcopy(p), 'sessions':sessions,
            'session_count':len(sessions), 'working_set_count':sum(len(s['sets']) for s in sessions),
            'evidence_status':'SOURCE_STRUCTURED', 'scientific_approval':False,
            'client_contract':'requires_schema_v2', 'chart_publishable':False,
            'readiness':'REQUIRES_EXPLICIT_SETUP',
            'required_setup':['exercise_specific_loads','warmup_choice','exercise_order','unreported_transition_rest'],
            'explanation':'Source-based workload template; unreported execution choices must be explicitly supplied and labelled as product/user choices.'}

def assess_profile(p, profile):
    """Evidence applicability, not medical clearance or a safety diagnosis."""
    pop = p['population']; differences=[]; missing=[]
    for key in ('sex','age','training_months','healthy'):
        if key not in profile: missing.append(key)
    if profile.get('sex') is not None and profile['sex'] != pop['sex']: differences.append('sex')
    if 'age' in profile:
        age=profile['age']
        if not number(age,0,130) or age < pop['min_age'] or (pop.get('age_min_exclusive') and age == pop['min_age']) or (pop.get('max_age') is not None and age > pop['max_age']): differences.append('age')
    if 'training_months' in profile and (not number(profile['training_months'],0,1200) or profile['training_months'] < pop['training_months']): differences.append('training_months')
    if 'healthy' in profile and profile['healthy'] is not True: differences.append('health_scope')
    return {'within_recorded_scope':not differences and not missing,'differences':differences,'missing':missing,
            'note':'Evidence applicability only; not individual efficacy or safety certification.'}

def initial_load(p, exercise_id, maxes, step_kg=None):
    x=next(x for x in p['exercises'] if x['id']==exercise_id)
    if x['load']['kind'] != 'initial_percent_1rm':
        return {'weight_kg':None,'target':copy.deepcopy(x['load']),'reason':'Choose load to match the recorded effort target; no 1RM conversion is assumed.'}
    reference=x['load']['reference_exercise'];weight=maxes.get(reference)
    if not number(weight,0.1,2000): raise InvalidProgramme('Exact exercise-specific measured 1RM required: '+reference)
    exact=Decimal(str(weight))*Decimal(str(x['load']['percent']))/Decimal('100')
    rounded=exact
    if step_kg is not None:
        if not number(step_kg,0.1,100): raise InvalidProgramme('Invalid equipment increment')
        step=Decimal(str(step_kg));rounded=(exact/step).quantize(Decimal('1'),rounding=ROUND_HALF_UP)*step
        if rounded <= 0: raise InvalidProgramme('Equipment rounding produced zero load')
    return {'weight_kg':float(rounded),'source_weight_kg':float(exact),'reference_exercise':reference,
            'source_percent':x['load']['percent'], 'source_locator':p['provenance']['exercises.0.load']['locator'],
            'policy':None if step_kg is None else {'id':'equipment-nearest-half-up-v1','increment_kg':step_kg},
            'application':'initial_only'}

def progression(p, actual_reps):
    """Return only supported adjustment instructions, never invent a kg step."""
    if type(actual_reps) != int or not 0 <= actual_reps <= 100: raise InvalidProgramme('Invalid actual reps')
    rule=p['progression']
    if rule['kind']=='bounded_load_adjustment':
        if actual_reps < rule['target_reps']:
            return {'action':'decrease','kg_range':rule['decrease_kg'],'apply_to':'next_set','source':p['provenance']['progression']}
        if actual_reps > rule['target_reps']:
            return {'action':'increase_eligible','kg_range':rule['increase_kg'],'apply_to':'user_confirmed_source_timing_unspecified','source':p['provenance']['progression']}
        return {'action':'no_rule_triggered'}
    return {'action':'adjust_to_rm_range','target':rule['target'],'kg_step':None,'apply_to':'successive_sets','source':p['provenance']['progression']}

def validate_schedule(p, days):
    expected=p['weeks']*p['sessions_per_week']
    if len(days)!=expected or any(type(d)!=int for d in days) or days!=sorted(set(days)): raise InvalidProgramme('Missing or duplicate training days')
    if any(not 0 <= d < p['weeks']*7 for d in days): raise InvalidProgramme('Days outside programme')
    if any(sum(w*7 <= d < (w+1)*7 for d in days)!=p['sessions_per_week'] for w in range(p['weeks'])): raise InvalidProgramme('Frequency changed')
    minimum=p['spacing'].get('min_day_difference')
    if minimum and any(b-a < minimum for a,b in zip(days,days[1:])): raise InvalidProgramme('Recovery interval violated')
    return {'days':list(days),'source_programme_unchanged':True,'policy':'user_calendar_assignment-v1'}

def instantiate_session(bundle, session_id, profile, setup):
    """Resolve explicit user decisions; never silently fill omissions in a study."""
    p=bundle['definition'];validate(p)
    if bundle['programme_version'] != digest({'definition':p,'compiler':ENGINE_VERSION}): raise InvalidProgramme('Programme version mismatch')
    if not assess_profile(p,profile)['within_recorded_scope']: raise InvalidProgramme('Outside or unknown recorded population scope')
    session=next((s for s in bundle['sessions'] if s['id']==session_id),None)
    if session is None: raise InvalidProgramme('Unknown session')
    # Recompile: a forged/edited session array cannot bypass the canonical definition.
    canonical=compile_programme(p)
    if canonical['sessions'] != bundle['sessions']: raise InvalidProgramme('Compiled schedule changed')
    order=setup.get('exercise_order',[])
    if len(order)!=len(p['exercises']) or set(order)!={x['id'] for x in p['exercises']}: raise InvalidProgramme('Explicit complete exercise order required')
    if p['order'].get('first') and order[0]!=p['order']['first']: raise InvalidProgramme('Source exercise order violated')
    if not isinstance(setup.get('warmup'),str) or not setup['warmup'].strip(): raise InvalidProgramme('Explicit warmup choice required')
    transition=setup.get('between_exercise_rest_seconds')
    if not number(transition,1,3600): raise InvalidProgramme('Explicit between-exercise rest required')
    source_rest=p['context']['between_exercise_rest']
    if source_rest.get('operator')=='gte' and transition<source_rest['seconds']: raise InvalidProgramme('Source minimum rest violated')
    if 'dumbbell_bulgarian_split_squat' in order and setup.get('split_squat_reps') not in ('per_leg','total'):
        raise InvalidProgramme('Source does not specify unilateral counting; explicit choice required')
    result=copy.deepcopy(session); result['sets']=[];decisions=[]
    first_session=session['week']==1 and session['ordinal']==1
    for id in order:
        x=next(x for x in p['exercises'] if x['id']==id)
        if x['load']['kind']=='initial_percent_1rm' and first_session:
            load=initial_load(p,id,setup.get('measured_1rm_kg',{}),setup.get('equipment_step_kg'))
            weight=load['weight_kg'];decisions.append(load)
        else:
            weight=setup.get('working_loads_kg',{}).get(id)
            if not number(weight,0.1,2000): raise InvalidProgramme('Exercise working load required: '+id)
            if x['load']['kind']=='repetition_maximum' and first_session:
                if setup.get('measured_rm_reps',{}).get(id)!=x['load']['initial_rm_test_reps']:
                    raise InvalidProgramme('Exercise-specific initial RM measurement required: '+id)
            decisions.append({'exercise_id':id,'weight_kg':weight,'origin':'user_measured_or_selected','target':x['load']})
        for row in session['sets']:
            if row['exercise_id']==id:
                step=copy.deepcopy(row);step['weight_kg']=weight;result['sets'].append(step)
    result.update(programme_version=bundle['programme_version'],readiness='READY',
                  classification='SOURCE_BASED_WITH_EXPLICIT_USER_CHOICES',
                  user_choices=copy.deepcopy(setup),population_check=assess_profile(p,profile),
                  load_decisions=decisions,scientific_approval=False)
    return result

def explain_exercise(p, exercise_id):
    i=next(i for i,x in enumerate(p['exercises']) if x['id']==exercise_id);x=p['exercises'][i]
    reps=str(x['reps']['min']) if x['reps']['min']==x['reps']['max'] else str(x['reps']['min'])+'~'+str(x['reps']['max'])
    rest=('최소 ' if x['rest']['operator']=='gte' else '')+str(x['rest']['seconds'])+'초'
    load=x['load']
    if load['kind']=='initial_percent_1rm': intensity='처음에는 해당 동작의 측정 1RM '+str(load['percent'])+'%'
    elif load['kind']=='rir': intensity='목표 횟수를 마친 뒤 '+str(load['target'])+'회 정도 더 할 수 있는 중량'
    else: intensity='정해진 반복 범위에서 바른 자세의 다음 반복이 어려워지는 중량'
    return {'text':f"원 연구의 {p['arm']}군은 {x['sets']}세트, {reps}회, 세트 사이 {rest}를 사용했습니다. {intensity}을 기준으로 합니다.",
            'scope':'원 연구의 운동 조건 설명이며 개인 효과 예측이 아닙니다.',
            'source_url':p['source']['url'],
            'evidence':[p['provenance']['exercises.'+str(i)+'.'+key] for key in ('sets','reps','load','rest')]}
