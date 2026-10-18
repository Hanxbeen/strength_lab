"""Reported four-lift novice structure with explicit scheduling and load choices."""
import copy
from . import novice
from .core import digest, number
from .coaching import rounded
from .workout import require, timestamp, max_record

ENGINE = 'petrizzo-2018-v1'
EXERCISES = (*novice.EXERCISES, 'barbell_standing_shoulder_press')
ARM = 'FOUR_LIFT'
ADAPTATION = 'petrizzo_explicit_schedule_v1'

def definition(days=2):
    require(type(days) is int and days in (2,3), 'INVALID_FREQUENCY')
    sessions = []
    for week in range(1,13):
        for day in range(1,days+1):
            ordinal = (week-1)*days+day
            lifts = [EXERCISES[0], EXERCISES[1] if ordinal % 2 else EXERCISES[3]]
            if day == 2:
                lifts.append(EXERCISES[2])
            sessions.append({'week':week,'day':day,'exercises':lifts})
    return {
        'id':f'petrizzo2018-four-lift-{days}d-v1', 'adapter_version':ENGINE,
        'title':f'기초 바벨 주 {days}회 · 스쿼트·벤치·프레스·데드리프트',
        'scientific_approval':False,'review_status':'source_extracted','publication_status':'internal_preview',
        'exercises':list(EXERCISES),
        'evidence':{'url':'https://www.asep.org/asep/asep/JEPonlineOCTOBER2018_Petrizzo.pdf',
            'locator':'Methods / Procedures pp.86–87','review':'reviews/novice-sbd-20261016.json',
            'outcome_scope':'squat_progression_feasibility_not_individual_sbd_effect'},
        'study':{'recruited':58,'analyzed':40,'completed_12_weeks':24,
                 'stalled':15,'injury_withdrawal':1,'other_excluded_dropouts':18,
                 'design':'supervised_single_cohort_no_randomized_comparator'},
        'adaptations':[
            {'id':ADAPTATION,'basis':'product_policy',
             'change':'Bench first; alternate bench/standing press across consecutive sessions; deadlift once weekly on day2.',
             'limitation':'A concrete scheduling choice within reported frequency rules, not a separately tested arm.'},
            {'id':'initial_load_origin_v1','basis':'user_choice',
             'change':'Record coach-assessed 5RM or an already known working load for each lift.',
             'limitation':'Known working load is an adaptation; the study used supervised initial assessment. The app does not assess technique.'},
            {'id':'explicit_followup_loads_v1','basis':'user_choice',
             'change':'Select every subsequent load; completion-based repeat/increase references are optional.',
             'limitation':'No fixed increment, reset, stall diagnosis or long-gap prescription is inferred.'}],
        'protocol':{'weeks':12,'days_per_week':days,'sessions':sessions,
            'working_sets':{e:1 if e==EXERCISES[2] else 3 for e in EXERCISES},
            'reps':5,'automatic_load_adjustment':None,
            'source_stop_rule':'12 weeks or inability to sustain chosen squat progression.',
            'product_stop_rule':'User may stop; changed or incomplete work is retained without automatic reset.',
            'initial_assessment':'supervised five repetitions without form degradation',
            'rest':'participant_selected','warmup':'progressively heavier sets before each exercise'},
    }

def validate_source(source):
    require(source == definition(source.get('protocol',{}).get('days_per_week')), 'UNSUPPORTED_PETRIZZO_DEFINITION')

def make_instance(source, arm, profile, records, setup, at):
    validate_source(source); timestamp(at)
    require(arm==ARM,'UNKNOWN_ARM')
    require(number(profile.get('age'),18,100) and profile.get('independent_sbd') is True
            and profile.get('independent_ohp') is True,'FOUR_LIFT_INSTRUCTION_REQUIRED')
    require(setup.get('mode')=='user_selected_source' and setup.get('accept_scope_limits') is True
            and setup.get('accept_adaptations') is True and setup.get('adaptation_id')==ADAPTATION,
            'EXPLICIT_FOUR_LIFT_SCHEDULE_REQUIRED')
    for key in ('rest_seconds','between_exercise_rest_seconds'):
        require(type(setup.get(key)) is int and 1<=setup[key]<=3600,'EXPLICIT_REST_REQUIRED')
    require(isinstance(setup.get('warmup'),str) and bool(setup['warmup'].strip()),'EXPLICIT_WARMUP_REQUIRED')
    step=setup.get('equipment_step_kg'); rounded(100,step)
    loads=setup.get('starting_loads_kg',{}); origins=setup.get('starting_load_origins',{})
    require(set(loads)==set(EXERCISES) and set(origins)==set(EXERCISES),'STARTING_LOAD_RECORDS_REQUIRED')
    for e in EXERCISES:
        require(number(loads[e],.1,2000) and abs(rounded(loads[e],step)-loads[e])<1e-8,'INVALID_STARTING_LOAD')
        require(origins[e] in ('coach_assessed_5rm','known_working_load'),'STARTING_LOAD_ORIGIN_REQUIRED')
    values=[max_record(r) for r in records]
    require(len(values)==len({r['exercise_id'] for r in values}) and
            {r['exercise_id'] for r in values}<=set(EXERCISES),'INVALID_OPTIONAL_MAX_REFERENCES')
    for r in values:
        require(timestamp(r['measured_at'])<=timestamp(at),'BASELINE_TIME_INVALID')
    return {'engine_version':ENGINE,'source':copy.deepcopy(source),'arm':arm,
        'profile':copy.deepcopy(profile),'max_records':values,'setup':copy.deepcopy(setup),'created_at':at,
        'programme_version':digest({'source':source,'arm':arm,'engine':ENGINE}),
        'adaptations':copy.deepcopy(source['adaptations'])}

def prepare(instance,week,day,at,history,initial_loads=None):
    snapshot=novice.prepare(instance,week,day,at,history,initial_loads)
    for decision in snapshot['coaching']['decisions']:
        eid=decision['exercise_id']
        if novice.previous_reference(history,eid)['status']=='no_history':
            require(decision['selected_kg']==instance['setup']['starting_loads_kg'][eid],
                    'FIRST_LOAD_MUST_MATCH_REGISTERED_START')
            decision['starting_load_origin']=instance['setup']['starting_load_origins'][eid]
            decision['starting_load_kg']=instance['setup']['starting_loads_kg'][eid]
    for row in snapshot['session']['sets']:
        row['source_locator']='Petrizzo2018 Procedures p.87; specific day assignment is product policy'
    snapshot['coaching']['engine']=ENGINE
    snapshot['coaching']['arm']=ARM
    snapshot['coaching']['load_selection_context']['load_selection']=session_inputs(
        instance, snapshot['coaching']['target']['exercises'], history)['load_selection']
    return snapshot

def session_inputs(instance, exercise_ids, history):
    result = novice.session_inputs(instance, exercise_ids, history)
    for item in result['load_selection']:
        if item['status'] == 'no_history':
            eid = item['exercise_id']
            item['registered_starting_load_kg'] = instance['setup']['starting_loads_kg'][eid]
            item['starting_load_origin'] = instance['setup']['starting_load_origins'][eid]
            item['input']['default_value'] = instance['setup']['starting_loads_kg'][eid]
            item['message'] = '등록한 시작 중량을 확인해 주세요. 수행 중 바꾼 중량은 따로 기록할 수 있어요.'
            item['actions'] = ['confirm_registered_starting_load', 'defer_session']
            item['basis'] = 'registered_user_choice_not_automatic_prescription'
    return result


def enrich(snapshot,result):
    from .sbd import enrich as reference_enrich
    result=reference_enrich(snapshot,result)
    result['coaching']['application']='four_lift_source_structure_with_explicit_choices'
    return result
