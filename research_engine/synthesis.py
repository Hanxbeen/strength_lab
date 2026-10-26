"""Explicit SBD product programmes; general evidence is not an exact SBD trial."""
import copy
from . import novice
from .core import digest,number
from .coaching import rounded
from .workout import require,timestamp,max_record
from .sbd import enrich as factual_enrich
ENGINE='sbd-evidence-synthesis-v1'
ARM='SBD_SYNTHESIS'
EXERCISES=novice.EXERCISES
SOURCE_URL='https://pmc.ncbi.nlm.nih.gov/articles/PMC12965823/'

def definition(level):
    require(level in ('foundation','trained'),'UNKNOWN_SYNTHESIS_LEVEL')
    days,sets=(2,2) if level=='foundation' else (3,3)
    return dict(id=f'mugemuge-sbd-{level}-v1',adapter_version=ENGINE,
        title=f'SBD 주 {days}회 · 무게무게 근거 종합',experience_context=level,
        review_status='reviewed_product_synthesis',publication_status='explicit_selection_candidate',
        scientific_approval=False,independent_expert_review=False,exercises=list(EXERCISES),
        evidence=dict(url=SOURCE_URL,locator='2026 ACSM position stand: Table 6, strength, implications',
            kind='overview_of_reviews',outcome_scope='general_strength_not_validation_of_this_SBD_programme',
            limits=['Many included participants were inexperienced; not a powerlifting-only review.',
                    'No individual growth curve or effect size is assigned to this product programme.']),
        adaptations=[
            dict(id='sbd_selection',basis='product_policy',change='Select SBD for the powerlifting MVP; not a whole-body general fitness claim.'),
            dict(id='fixed_cycle',basis='product_policy',change=f'Eight weeks, {days} nonconsecutive sessions per week, {sets} sets of five per lift. This exact combination was not tested by the review.'),
            dict(id='effort_and_load',basis='user_choice',change='Known submaximal working loads; stop with repetitions in reserve. No 1RM test or fixed percentage required.'),
            dict(id='rest',basis='user_choice',change='Explicit inter-set/inter-exercise rest and warmup; no optimal-rest claim.'),
            dict(id='progression',basis='product_policy',change='Review actual sets and choose repeat/increase/decrease. No automatic increment, reset, plateau diagnosis or growth forecast.')],
        protocol=dict(weeks=8,days_per_week=days,
            sessions=[dict(week=w,day=d,exercises=list(EXERCISES)) for w in range(1,9) for d in range(1,days+1)],
            working_sets={e:sets for e in EXERCISES},reps=5,automatic_load_adjustment=None,
            source_stop_rule=None,product_stop_rule='Stop for pain, loss of control or user choice; incomplete records remain unknown.',
            effort_guidance='실패할 때까지 반복하지 않아요. 자세가 흐트러지거나 통증이 생기면 멈춰요.',
            duration_basis='product_review_interval_not_expected_growth_deadline'),
        product_scope=dict(adult=True,independent_sbd=True,known_working_loads=True,
                           training_months_min=6 if level=='trained' else 0))
def validate_source(source):
    require(source==definition(source.get('experience_context')),'UNSUPPORTED_SYNTHESIS_DEFINITION')
def make_instance(source,arm,profile,records,setup,at):
    validate_source(source);timestamp(at);require(arm==ARM,'UNKNOWN_ARM')
    require(number(profile.get('age'),18,100) and profile.get('independent_sbd') is True,'EXPERIENCED_ADULT_REVIEW_SCOPE_REQUIRED')
    require(profile.get('current_pain') is False and profile.get('exercise_restriction') is False,'CURRENT_HEALTH_SCOPE_REQUIRED')
    if source['experience_context']=='trained':
        require(number(profile.get('training_months'),6,900),'TRAINING_EXPERIENCE_SCOPE_REQUIRED')
    require(setup.get('mode')=='user_selected_source' and setup.get('accept_scope_limits') is True
            and setup.get('accept_adaptations') is True and setup.get('adaptation_id')==source['id'],'SYNTHESIS_ACKNOWLEDGEMENT_REQUIRED')
    for key in ('rest_seconds','between_exercise_rest_seconds'):
        require(type(setup.get(key)) is int and 1<=setup[key]<=3600,'EXPLICIT_REST_REQUIRED')
    require(isinstance(setup.get('warmup'),str) and bool(setup['warmup'].strip()),'EXPLICIT_WARMUP_REQUIRED')
    step=setup.get('equipment_step_kg');rounded(100,step)
    loads=setup.get('starting_loads_kg',{});origins=setup.get('starting_load_origins',{})
    require(set(loads)==set(EXERCISES) and set(origins)==set(EXERCISES),'STARTING_LOAD_RECORDS_REQUIRED')
    for e in EXERCISES:
        require(number(loads[e],.1,2000) and abs(rounded(loads[e],step)-loads[e])<1e-8,'INVALID_STARTING_LOAD')
        require(origins[e] in ('known_working_load','coach_assessed_working_load','self_reported_intro_trial'),'STARTING_LOAD_ORIGIN_REQUIRED')
    values=[max_record(r) for r in records]
    require(len(values)==len({r['exercise_id'] for r in values}) and {r['exercise_id'] for r in values}<=set(EXERCISES),'INVALID_OPTIONAL_MAX_REFERENCES')
    for r in values:require(timestamp(r['measured_at'])<=timestamp(at),'BASELINE_TIME_INVALID')
    return dict(engine_version=ENGINE,source=copy.deepcopy(source),arm=arm,profile=copy.deepcopy(profile),
        max_records=values,setup=copy.deepcopy(setup),created_at=at,
        programme_version=digest(dict(source=source,arm=arm,engine=ENGINE)),adaptations=copy.deepcopy(source['adaptations']))
def session_inputs(instance,exercise_ids,history):
    result=novice.session_inputs(instance,exercise_ids,history)
    result['help_delivery']='entry_learning_or_qualified_support'
    for guide in result['load_selection']:
        guide['evidence_limit']='First-load observations are self-reports, not technique certification or a validated 5RM.'
        guide['choice_policy']='synthesis-explicit-user-choice-v1'
    return result
def prepare(instance,week,day,at,history,initial_loads=None):
    snap=novice.prepare(instance,week,day,at,history,initial_loads)
    for row in snap['session']['sets']:
        row['source_locator']='Product SBD prescription; ACSM2026 Table6 is general evidence, not this exact set/rep protocol'
    for choice in snap['coaching']['decisions']:
        e=choice['exercise_id']
        if novice.previous_reference(history,e)['status']=='no_history':
            require(choice['selected_kg']==instance['setup']['starting_loads_kg'][e],'FIRST_LOAD_MUST_MATCH_REGISTERED_START')
            choice['starting_load_origin']=instance['setup']['starting_load_origins'][e]
    snap['coaching'].update(engine=ENGINE,arm=ARM,application='explicit_product_synthesis',
        evidence_scope=instance['source']['evidence'],load_selection_context=session_inputs(instance,EXERCISES,history))
    return snap
def enrich(snapshot,result):
    result=factual_enrich(snapshot,result)
    result['coaching']['application']='explicit_product_synthesis_not_trial_replication'
    return result
