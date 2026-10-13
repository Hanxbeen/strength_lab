"""Source-specific Helms 2018 programme and auditable decisions; no AI at runtime."""
import copy
from decimal import Decimal, ROUND_HALF_UP
from .core import digest, number, InvalidProgramme
from .workout import require, timestamp, max_record, POLICY

from .execution_facts import pain_reported

ENGINE = 'helms-2018-v1'
SOURCE_ID = '10.3389/fphys.2018.00247'
EXERCISES = ('barbell_back_squat', 'barbell_bench_press')

def validate_source(source):
    require(source.get('id') == SOURCE_ID and source.get('adapter_version') == ENGINE, 'UNSUPPORTED_SOURCE')
    require(source.get('protocol_sha256') == digest(source.get('protocol')), 'PROTOCOL_HASH_MISMATCH')
    require(source.get('review_status') == 'source_extracted' and source.get('scientific_approval') is False,
            'UNSUPPORTED_REVIEW_STATE')
    require(source.get('publication_status') != 'suspended', 'SOURCE_SUSPENDED')

def rounded(weight, step):
    require(number(step, .1, 100), 'INVALID_EQUIPMENT_STEP')
    result=float((Decimal(str(weight))/Decimal(str(step))).quantize(Decimal('1'), rounding=ROUND_HALF_UP)*Decimal(str(step)))
    require(result > 0, 'LOAD_BELOW_EQUIPMENT_MINIMUM')
    return result

def make_instance(source, arm, profile, records, setup, at):
    validate_source(source); timestamp(at)
    require(arm in ('1RMG','RPEG'), 'UNKNOWN_ARM')
    require(setup.get('mode') == 'user_selected_source', 'EXPLICIT_SOURCE_SELECTION_REQUIRED')
    require(setup.get('accept_scope_limits') is True, 'SCOPE_ACKNOWLEDGEMENT_REQUIRED')
    require(number(profile.get('body_mass_kg'),20,400), 'BODY_MASS_REQUIRED')
    missing=[k for k in ('sex','age','training_months','lifts_weekly_last_6_months','healthy') if k not in profile]
    require(not missing, 'PROFILE_INCOMPLETE')
    require(number(profile['age'],18,100) and number(profile['training_months'],0,1000), 'INVALID_PROFILE')
    require(profile['healthy'] is True, 'HEALTH_SCOPE_REQUIRES_REVIEW')
    values={r['exercise_id']:max_record(r) for r in records}
    require(set(values)==set(EXERCISES), 'EXERCISE_SPECIFIC_MAXES_REQUIRED')
    for r in values.values():
        require(r['kind']=='measured' and timestamp(r['measured_at'])<=timestamp(at), 'MEASURED_BASELINE_REQUIRED')
    differences=[]
    if profile['sex']!='male': differences.append('sex')
    if not 19<=profile['age']<=35: differences.append('age')
    if profile['training_months']<24 or profile['lifts_weekly_last_6_months'] is not True: differences.append('training_experience')
    for eid,ratio in zip(EXERCISES,(1.5,1.25)):
        if values[eid]['weight_kg']/profile['body_mass_kg']<ratio:differences.append(eid+'_relative_strength')
    # This implementation offers source use only, not an unreviewed extrapolated programme.
    require(not differences, 'OUTSIDE_STUDY_SCOPE:'+','.join(differences))
    require(number(setup.get('rest_seconds'),300,420), 'SOURCE_REST_RANGE_300_420')
    rounded(100, setup.get('equipment_step_kg'))
    require(isinstance(setup.get('warmup'),str) and bool(setup['warmup'].strip()), 'EXPLICIT_WARMUP_REQUIRED')
    return {'engine_version':ENGINE,'source':copy.deepcopy(source),'arm':arm,'profile':copy.deepcopy(profile),
            'max_records':list(values.values()),'setup':copy.deepcopy(setup),'created_at':at,
            'programme_version':digest({'source':source,'arm':arm,'engine':ENGINE}),
            'adaptations':['User-selected warmup; research testing and supervision are not reproduced',
                           'Equipment rounding is product policy; adjustments require user confirmation']}

def session_target(instance,week,day):
    require(type(week)==int and type(day)==int and 1<=week<=8 and 1<=day<=3, 'INVALID_SESSION')
    require(not (week==8 and day==3), 'POST_TEST_EVALUATION_NOT_TRAINING')
    return instance['source']['protocol']['weeks'][week-1]['days'][day-1]

def adjustment(arm, actual, target_reps, rpe_range):
    """Exact reported arithmetic; not a universal recommendation or an auto-applied change."""
    if actual.get('reason') is not None and actual.get('reason')!='fatigue':
        return {'status':'needs_context','factor':None,'reason':'Non-performance interruption must not be treated as muscular failure'}
    missed=max(0,target_reps-actual['reps'])
    if missed and actual.get('failure')!='momentary_concentric':
        return {'status':'needs_context','factor':None,'reason':'Confirm performance failure; unattempted repetitions are not failures'}
    if arm=='1RMG': delta=-.04*missed
    elif missed: delta=-.04*(10-rpe_range[1]+missed)
    elif actual.get('rpe') is None:
        return {'status':'needs_rpe','factor':None}
    else:
        rpe=actual['rpe'];lo,hi=rpe_range
        delta=.04*(lo-rpe) if rpe<lo else -.04*(rpe-hi) if rpe>hi else 0
    if 1+delta<=0:return {'status':'needs_review','factor':None}
    return {'status':'participant_choice' if arm=='RPEG' and delta==0 else 'source_calculation',
            'factor':round(1+delta,6),'change_percent':round(delta*100,4),
            'basis':'source_reported','source_id':SOURCE_ID,'locator':'Training protocol; Table 3',
            'automatically_applied':False}

def prepare(instance,week,day,at,history,initial_loads=None):
    target=session_target(instance,week,day);timestamp(at)
    require(timestamp(at)>=timestamp(instance['created_at']), 'BEFORE_INSTANCE')
    rows=[];decisions=[];initial_loads=initial_loads or {}
    maxima={r['exercise_id']:r['weight_kg'] for r in instance['max_records']}
    arm=instance['arm'];setup=instance['setup']
    for eid in EXERCISES:
        pct=target['percent_1rm']
        previous=next((h for h in history if h['week']==week-1 and h['day']==day),None)
        previous_rows=[r for r in previous['execution']['sets'] if r['exercise_id']==eid] if previous else []
        if arm=='1RMG':
            if week in (3,5,7):
                require(previous is not None, 'PRIOR_WEEK_REQUIRED')
                all_done=bool(previous_rows) and all(r['status']=='recorded' and r['actual']['reps']>=r['reps']['min'] and r['actual']['weight_kg']>=r['weight_kg'] for r in previous_rows)
                if not all_done:pct=instance['source']['protocol']['weeks'][week-2]['days'][day-1]['percent_1rm']
                decisions.append({'exercise_id':eid,'kind':'conditional_weekly_progression',
                     'previous_workout_id':previous['workout_id'],'all_sets_completed':all_done,
                     'percent_1rm':pct,'locator':'Table 2 footnote; Training protocol',
                     'limitation':'Missed sessions/skipped sets conservatively prevent increase; product policy'})
            raw=maxima[eid]*pct/100
            weight=rounded(raw,setup['equipment_step_kg'])
            load={'kind':'percentage_1rm','percent':pct,'baseline_max_kg':maxima[eid]}
        else:
            weight=initial_loads.get(eid)
            require(number(weight,.1,2000), 'RPE_LOAD_SELECTION_REQUIRED:'+eid)
            raw=weight
            load={'kind':'rpe_range','range':target['rpe_range']}
            decisions.append({'exercise_id':eid,'kind':'history_for_load_selection',
                'previous_workout_id':previous['workout_id'] if previous else None,
                'previous_sets':[{'weight_kg':r['actual']['weight_kg'],'reps':r['actual']['reps'],'rpe':r['actual'].get('rpe')} for r in previous_rows if r['actual']],
                'locator':'Training protocol',
                'limitation':'Week 1 load was researcher-selected in the study; user selection here is an explicit adaptation' if week==1 else None})
        for n in range(1,target['sets']+1):
            rows.append({'id':eid+':'+str(n),'exercise_id':eid,'set':n,
                         'reps':{'min':target['reps'],'max':target['reps']},'load':copy.deepcopy(load),
                         'weight_kg':weight,'unrounded_weight_kg':raw,'tempo':{'kind':'not_encoded'},
                         'rest_after':{'operator':'eq','seconds':setup['rest_seconds']} if n<target['sets'] else None})
    return {'schema_version':2,'policy_version':POLICY,'programme_id':'helms2018-'+arm,
            'programme_version':instance['programme_version'],'source':copy.deepcopy(instance['source']),
            'definition':{'progression':{'kind':'coaching_source'},'provenance':{}},
            'session':{'sets':rows,'user_choices':{'between_exercise_rest_seconds':600}},
            'max_records':instance['max_records'],'started_at':at,
            'coaching':{'engine':ENGINE,'week':week,'day':day,'arm':arm,'target':target,
                        'equipment_step_kg':setup['equipment_step_kg'],'decisions':decisions,
                        'instance_created_at':instance['created_at'],'setup':copy.deepcopy(setup)}}

def enrich(snapshot, execution):
    context=snapshot['coaching'];result=copy.deepcopy(execution)
    result['coaching']={**context,'scientific_approval':False,
                       'application':'user_selected_source_with_explicit_adaptations',
                       'growth_prediction':None}
    current=next((r for r in result['sets'] if r['id']==result['next_set_id']),None)
    performed=[r for r in result['sets'] if r['actual']]
    if current and performed and result['state'] in ('active','resting') and not pain_reported(result['sets']) and not result.get('legacy_read_only'):
        last=performed[-1]
        if last['exercise_id']==current['exercise_id'] and result['sets'].index(current)>0 and result['sets'][result['sets'].index(current)-1]['id']==last['id']:
            decision=adjustment(context['arm'],last['actual'],last['reps']['min'],context['target']['rpe_range'])
            if decision.get('factor') is not None:
                raw=last['actual']['weight_kg']*decision['factor']
                try:
                    proposal=rounded(raw,context['equipment_step_kg'])
                    if proposal>2000 or (decision['factor']<1 and proposal>=last['actual']['weight_kg']) or (decision['factor']>1 and proposal<=last['actual']['weight_kg']):proposal=None
                except InvalidProgramme:proposal=None
                decision.update(source_weight_kg=raw,proposed_weight_kg=proposal,
                                rounding_policy='nearest-half-up-user-equipment-v1')
            result['coaching']['next_set_decision']=decision
    result['summary']['growth_prediction']=None
    result['summary']['volume_load_kg_reps']=sum(r['actual']['weight_kg']*r['actual']['reps'] for r in performed)
    result['summary']['rpe_missing_sets']=sum(r['actual'].get('rpe') is None for r in performed)
    for chart,row in zip(result['summary']['chart'],result['sets']):
        chart['actual_rpe']=row['actual'].get('rpe') if row['actual'] else None
        chart['source_rpe_range']=context['target']['rpe_range'] if context['arm']=='RPEG' else None
    return result
