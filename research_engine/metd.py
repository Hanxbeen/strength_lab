"""METD 2021: three source arms, no generated progression or inferred RPE load."""
import copy
from .core import digest,number
from .coaching import rounded
from .workout import require,timestamp,max_record,DEPENDENT_POLICY
from .sbd import EXERCISES,enrich as enrich_reference

ENGINE='metd-2021-v1'
ARMS=('MAX','MAX_BOFF','AMRAP')

def validate_source(source):
    require(source.get('id')=='metd2021-sbd-v1' and source.get('adapter_version')==ENGINE,'UNSUPPORTED_SOURCE')
    require(source.get('scientific_approval') is False and source.get('review_status')=='source_extracted' and
            source.get('publication_status')=='internal_preview','UNSUPPORTED_REVIEW_STATE')
    p=source.get('protocol',{})
    require(digest(p)==source.get('protocol_sha256'),'PROTOCOL_HASH_MISMATCH')
    require(source.get('exercises')==list(EXERCISES) and p.get('weeks')==6 and p.get('days_per_week')==3,'INVALID_SCHEDULE')
    expected=[{'week':w,'day':d,'exercises':list(EXERCISES[:2] if d!=2 else EXERCISES[1:]),'locator':'sec36'}
              for w in range(1,7) for d in range(1,4)]
    require(p.get('sessions')==expected and set(p.get('arms',{}))==set(ARMS),'INCOMPLETE_SCHEDULE')
    for arm in ARMS:
        a=p['arms'][arm]
        require(a['working_sets']==(3 if arm=='MAX_BOFF' else 1),'INVALID_SETS')
        if arm=='AMRAP':
            require(a['load']=={'kind':'percentage_1rm','percent':70} and a['reps']=={'kind':'until_rpe','rpe':[9,9.5]},'SOURCE_RULE_MISMATCH')
            require(a['warmup']['sets']==[{'percent':p,'reps':5} for p in (40,50,60)],'SOURCE_WARMUP_MISMATCH')
        else:
            require(a['load']=={'kind':'self_selected_rpe','rpe':[9,9.5]} and a['reps']=={'kind':'fixed','value':1},'SOURCE_RULE_MISMATCH')
    require(p['arms']['MAX_BOFF']['backoff']=={'sets':2,'reps':3,'percent_actual_single_load':80,'rpe_target':None},'SOURCE_BACKOFF_MISMATCH')

def make_instance(source,arm,profile,records,setup,at):
    validate_source(source);timestamp(at);require(arm in ARMS,'UNKNOWN_ARM')
    require(setup.get('mode')=='user_selected_source' and setup.get('accept_scope_limits') is True and
            setup.get('accept_adaptations') is True,'SCOPE_ACKNOWLEDGEMENT_REQUIRED')
    require(number(profile.get('age'),18,100) and profile.get('independent_sbd') is True,'EXPERIENCED_ADULT_REVIEW_SCOPE_REQUIRED')
    # Internal preview boundary, not a claim that everyone outside the study is unsafe.
    require(number(profile.get('training_years'),4,80) and number(profile.get('powerlifting_years'),2,80) and
            number(profile.get('rpe_training_years'),1,80),'EXPERIENCE_SCOPE_REQUIRES_REVIEW')
    values=[max_record(r) for r in records]
    require(len(values)==3 and {r['exercise_id'] for r in values}==set(EXERCISES),'SBD_MAX_REFERENCES_REQUIRED')
    for r in values:require(r['kind']=='measured' and timestamp(r['measured_at'])<=timestamp(at),'MEASURED_BASELINE_REQUIRED')
    for k in ('rest_seconds','between_exercise_rest_seconds'):
        require(type(setup.get(k)) is int and 1<=setup[k]<=3600,'EXPLICIT_REST_REQUIRED')
    rounded(100,setup.get('equipment_step_kg'))
    if arm!='AMRAP':require(isinstance(setup.get('warmup'),str) and bool(setup['warmup'].strip()),'EXPLICIT_WARMUP_REQUIRED')
    return {'engine_version':ENGINE,'source':copy.deepcopy(source),'arm':arm,'profile':copy.deepcopy(profile),
        'max_records':values,'setup':copy.deepcopy(setup),'created_at':at,
        'programme_version':digest({'source':source,'arm':arm,'engine':ENGINE}),
        'adaptations':copy.deepcopy(source['adaptations'])}

def prepare(instance,week,day,at,history,initial_loads=None):
    require(type(week) is int and type(day) is int and 1<=week<=6 and 1<=day<=3,'INVALID_SESSION')
    require(timestamp(at)>=timestamp(instance['created_at']),'BEFORE_INSTANCE')
    arm=instance['arm'];target=instance['source']['protocol']['sessions'][(week-1)*3+day-1]
    loads=initial_loads or {};setup=instance['setup'];step=setup['equipment_step_kg']
    if arm=='AMRAP':require(not loads,'PERCENTAGE_TEMPLATE_REQUIRES_NO_RPE_START_LOADS')
    else:
        require(set(loads)==set(target['exercises']),'EXPLICIT_DAILY_LOADS_REQUIRED')
        for v in loads.values():require(number(v,.1,2000) and abs(rounded(v,step)-v)<1e-8,'INVALID_DAILY_LOAD')
    maxima={r['exercise_id']:r for r in instance['max_records']};rows=[]
    def add(eid,label,reps,load,weight,role,locator):
        rows.append({'id':eid+':'+label,'exercise_id':eid,'set':len(rows)+1,'reps':reps,'load':load,
            'weight_kg':weight,'tempo':{'kind':'not_encoded'},'set_role':role,'source_locator':locator,
            'rest_after':{'operator':'eq','seconds':setup['rest_seconds'],'basis':'user_choice'}})
    for eid in target['exercises']:
        if arm=='AMRAP':
            for pct in (40,50,60,70):
                effort=pct==70;raw=maxima[eid]['weight_kg']*pct/100
                add(eid,'main' if effort else 'warmup'+str(pct),
                    {'min':None,'max':None,'kind':'until_rpe','rpe':[9,9.5]} if effort else {'min':5,'max':5},
                    {'kind':'percentage_1rm','percent':pct,'max_record_id':maxima[eid]['id']},
                    rounded(raw,step),'working' if effort else 'warmup','sec39' if effort else 'sec36')
                rows[-1]['unrounded_weight_kg']=raw
        else:
            add(eid,'main',{'min':1,'max':1},{'kind':'self_selected_rpe','rpe':[9,9.5],'basis':'user_choice'},loads[eid],'working','sec37')
            if arm=='MAX_BOFF':
                for n in (1,2):
                    add(eid,'backoff'+str(n),{'min':3,'max':3},
                        {'kind':'percent_actual_set','percent':80,'set_id':eid+':main','equipment_step_kg':step},
                        None,'backoff','sec38')
    rows[-1]['rest_after']=None
    previous=next((h for h in reversed(history) if h['day']==day),None)
    reference=None if previous is None else {'workout_id':previous['workout_id'],'week':previous['week'],
        'sets':copy.deepcopy(previous['execution']['sets']),'rests':copy.deepcopy(previous['execution']['rests']),
        'limitation':'Prior actuals are reference only, not automatically selected loads or inferred 1RM.'}
    return {'schema_version':2,'policy_version':DEPENDENT_POLICY,'programme_id':instance['source']['id'],
        'programme_version':instance['programme_version'],'source':copy.deepcopy(instance['source']),
        'definition':{'progression':{'kind':'coaching_source'},'provenance':{}},
        'session':{'sets':rows,'user_choices':{'between_exercise_rest_seconds':setup['between_exercise_rest_seconds']}},
        'max_records':copy.deepcopy(instance['max_records']),'started_at':at,
        'coaching':{'engine':ENGINE,'week':week,'day':day,'arm':arm,'target':copy.deepcopy(target),
            'initial_rpe_loads_kg':copy.deepcopy(loads),'adaptations':copy.deepcopy(instance['adaptations']),
            'previous_same_day':reference,'decisions':[],'setup':copy.deepcopy(setup),'equipment_step_kg':step}}

def enrich(snapshot,result):
    result=enrich_reference(snapshot,result)
    result['coaching']['application']='source_arm_with_explicit_execution_choices'
    result['summary']['source_comparison']='Actual vs selected research arm; not research-effect attainment.'
    result['coaching']['effort_checks']=[{'set_id':r['id'],'target':r['reps'].get('rpe',r['load'].get('rpe')),
        'actual_rpe':r['actual']['rpe'] if r['actual'] else None,
        'status':'not_recorded' if not r['actual'] else 'unknown' if r['actual']['rpe'] is None else
            'below_target' if r['actual']['rpe']<9 else 'above_target' if r['actual']['rpe']>9.5 else 'within_target',
        'load_adjustment':None} for r in result['sets'] if r['set_role']=='working']
    result['coaching']['source_testing']=copy.deepcopy(snapshot['source']['protocol']['testing'])
    return result
