"""Internal SBD omission prototype; explicit loads, never an approved novice prescription."""
import copy
from .core import digest, number
from .coaching import rounded
from .workout import require, timestamp, max_record, POLICY
from .sbd import EXERCISES, enrich as reference_enrich
from .execution_facts import pain_reported

ENGINE = 'novice-sbd-choice-v1'
ARM = 'SBD_2D_OMISSION'
ADAPTATION = 'petrizzo_ohp_omitted_2d_v1'


def definition():
    return {
        'id': 'novice-sbd-choice-v1', 'adapter_version': ENGINE,
        'title': 'SBD 주 2회 · 직접 중량 선택 조정안',
        'scientific_approval': False, 'review_status': 'internal_product_prototype',
        'publication_status': 'internal_preview', 'exercises': list(EXERCISES),
        'evidence': {'url': 'https://www.asep.org/asep/asep/JEPonlineOCTOBER2018_Petrizzo.pdf',
                     'locator': 'Procedures, pp. 86-87',
                     'review': 'reviews/novice-sbd-20261016.json',
                     'outcome_scope': 'squat_progression_sustainability_not_sbd_efficacy'},
        'adaptations': [
            {'id': ADAPTATION, 'basis': 'product_policy',
             'change': 'Choose two weekly sessions; omit OHP without replacing it; bench on day 1, deadlift on day 2.',
             'limitation': 'Reduced total training dose. This exact SBD-only programme was not studied.'},
            {'id': 'explicit_load_choice_v1', 'basis': 'user_choice',
             'change': 'Every session requires explicit working loads; 1RM records are comparison references only.',
             'limitation': 'Not a substitute for the source supervised 5RM assessment or real-time coaching. No unsupervised safety claim.'},
        ],
        'protocol': {'weeks': 12, 'days_per_week': 2,
            'sessions': [{'week': w, 'day': d, 'exercises': list(EXERCISES[:2] if d == 1 else (EXERCISES[0], EXERCISES[2]))}
                         for w in range(1, 13) for d in (1, 2)],
            'working_sets': {EXERCISES[0]: 3, EXERCISES[1]: 3, EXERCISES[2]: 1}, 'reps': 5,
            'automatic_load_adjustment': None,
            'source_stop_rule': 'Original study ended at 12 weeks or inability to sustain chosen squat progression.',
            'product_stop_rule': 'User can stop earlier; no automatic reset, deload, or stalled classification.'}}


def validate_source(source):
    require(source == definition(), 'UNSUPPORTED_NOVICE_DEFINITION')


def make_instance(source, arm, profile, records, setup, at):
    validate_source(source); timestamp(at)
    require(arm == ARM, 'UNKNOWN_ARM')
    require(number(profile.get('age'), 18, 100) and profile.get('independent_sbd') is True,
            'EXPERIENCED_ADULT_REVIEW_SCOPE_REQUIRED')
    require(setup.get('mode') == 'user_selected_source' and setup.get('accept_scope_limits') is True
            and setup.get('accept_adaptations') is True and setup.get('adaptation_id') == ADAPTATION,
            'EXPLICIT_SBD_ADAPTATION_REQUIRED')
    values = [max_record(r) for r in records]
    require(len(values) == len({r['exercise_id'] for r in values}) and
            {r['exercise_id'] for r in values} <= set(EXERCISES), 'INVALID_OPTIONAL_MAX_REFERENCES')
    for r in values:
        require(timestamp(r['measured_at']) <= timestamp(at), 'BASELINE_TIME_INVALID')
    # References may be estimated: they do not prescribe this prototype's working loads.
    for key in ('rest_seconds', 'between_exercise_rest_seconds'):
        require(type(setup.get(key)) is int and 1 <= setup[key] <= 3600, 'EXPLICIT_REST_REQUIRED')
    require(isinstance(setup.get('warmup'), str) and bool(setup['warmup'].strip()), 'EXPLICIT_WARMUP_REQUIRED')
    rounded(100, setup.get('equipment_step_kg'))
    return {'engine_version': ENGINE, 'source': copy.deepcopy(source), 'arm': arm,
            'profile': copy.deepcopy(profile), 'max_records': values, 'setup': copy.deepcopy(setup),
            'created_at': at, 'programme_version': digest({'source': source, 'arm': arm, 'engine': ENGINE}),
            'adaptations': copy.deepcopy(source['adaptations'])}


def previous_reference(history, eid):
    prior = next((h for h in reversed(history) if any(r['exercise_id'] == eid for r in h['execution']['sets'])), None)
    if prior is None:
        return {'exercise_id': eid, 'status': 'no_history', 'automatic_load_kg': None}
    rows = [r for r in prior['execution']['sets'] if r['exercise_id'] == eid]
    pain = pain_reported(prior['execution']['sets'])
    completed = all(r['actual'] is not None and r['actual']['reps'] == 5 and
                    r['actual']['weight_kg'] == r['weight_kg'] and not r['changes'] for r in rows)
    status = ('pain_context_required' if pain else 'previous_session_not_completed'
              if prior['execution']['state'] != 'completed' else
              'selected_plan_completed' if completed else 'changed_or_incomplete')
    return {'exercise_id': eid, 'workout_id': prior['workout_id'],
            'history_events_sha256': digest(prior['events']), 'status': status,
            'sets': copy.deepcopy(rows), 'rests': copy.deepcopy(prior['execution']['rests']),
            'automatic_load_kg': None,
            'basis': 'observed_execution_not_progression_or_safety_approval'}


def load_selection(reference, equipment_step_kg):
    """Product navigation, not a source-derived load/progression prescription."""
    status = reference['status']
    messages = {
        'no_history': '이 종목의 이전 기록이 없어요. 알고 있는 작업 중량을 직접 입력하거나 중량 선택 도움을 받아 주세요.',
        'selected_plan_completed': '지난 목표를 수행했어요. 기록을 참고해 오늘 중량을 선택해 주세요. 자동 증량 기준은 아니에요.',
        'changed_or_incomplete': '지난 목표와 실제 수행이 달랐어요. 세트별 중량과 횟수를 확인하고 오늘 중량을 선택해 주세요.',
        'previous_session_not_completed': '지난 운동은 중단됐어요. 기록하지 않은 세트는 실패로 판단하지 않아요.',
        'pain_context_required': '지난 운동에 통증·불편함 기록이 있어요. 현재 상태를 먼저 확인해 주세요. 감량하면 안전하다는 뜻은 아니에요.',
    }
    pain = status == 'pain_context_required'
    weights = {r['actual']['weight_kg'] for r in reference.get('sets', []) if r.get('actual')}
    comparable = status == 'selected_plan_completed' and len(weights) == 1
    return {
        'contract_version': 'novice-load-selection-v1',
        'exercise_id': reference['exercise_id'], 'status': status,
        'basis': 'product_navigation_with_observed_records',
        'message': messages[status],
        'actions': (['review_current_discomfort', 'seek_qualified_help', 'defer_session'] if pain else
                    ['enter_known_working_load', 'seek_load_selection_help', 'defer_session'] if status == 'no_history' else
                    ['review_previous_sets', 'enter_working_load', 'seek_load_selection_help', 'defer_session']),
        'input': {'field': 'initial_loads_kg.' + reference['exercise_id'],
                  'unit': 'kg', 'equipment_step_kg': equipment_step_kg,
                  'default_value': None, 'required_to_start': True},
        'recommended_load_kg': None, 'recommended_increment_kg': None,
        'reference_load_kg': next(iter(weights)) if comparable else None,
        'recorded_choice_types': ['repeat', 'increase'] if comparable else [],
        'choice_policy': 'novice-confirmed-choice-v1',
        'one_rm_test_required': False, 'automatic_progression': False,
        'current_readiness_assessed': False,
        'reference_workout_id': reference.get('workout_id'),
        'reference_events_sha256': reference.get('history_events_sha256'),
        'evidence_limit': 'Source used supervised initial assessment; no validated unsupervised first-load rule is implemented.',
    }


def session_inputs(instance, exercise_ids, history):
    references = [previous_reference(history, eid) for eid in exercise_ids]
    return {
        'required_field': 'initial_loads_kg', 'exercise_ids': list(exercise_ids),
        'previous_exercises': references,
        'selection_basis': 'user_choice_not_automatic_prescription',
        'load_selection': [load_selection(ref, instance['setup']['equipment_step_kg']) for ref in references],
        'help_delivery': 'external_qualified_support_not_in_app_assessment',
    }


def prepare(instance, week, day, at, history, initial_loads=None):
    require(type(week) is int and type(day) is int and 1 <= week <= 12 and day in (1, 2), 'INVALID_SESSION')
    require(timestamp(at) >= timestamp(instance['created_at']), 'BEFORE_INSTANCE')
    target = instance['source']['protocol']['sessions'][(week - 1) * 2 + day - 1]
    setup = instance['setup']; loads = initial_loads or {}; step = setup['equipment_step_kg']
    require(set(loads) == set(target['exercises']), 'EXPLICIT_SESSION_LOADS_REQUIRED')
    rows = []
    for eid in target['exercises']:
        weight = loads[eid]
        require(number(weight, .1, 2000) and abs(rounded(weight, step) - weight) < 1e-8, 'INVALID_SESSION_LOAD')
        for n in range(instance['source']['protocol']['working_sets'][eid]):
            rows.append({'id': eid + ':' + str(n + 1), 'exercise_id': eid, 'set': len(rows) + 1,
                'reps': {'min': 5, 'max': 5}, 'weight_kg': weight,
                'load': {'kind': 'explicit_user_choice', 'basis': 'user_choice'},
                'tempo': {'kind': 'not_encoded'}, 'set_role': 'working',
                'source_locator': 'Petrizzo2018 Procedures pp.86-87; SBD omission is product adaptation',
                'rest_after': {'operator': 'eq', 'seconds': setup['rest_seconds'], 'basis': 'user_choice'}})
    rows[-1]['rest_after'] = None
    return {'schema_version': 2, 'policy_version': POLICY, 'programme_id': instance['source']['id'],
        'programme_version': instance['programme_version'], 'source': copy.deepcopy(instance['source']),
        'definition': {'progression': {'kind': 'coaching_source'}, 'provenance': {}},
        'session': {'sets': rows, 'user_choices': {'between_exercise_rest_seconds': setup['between_exercise_rest_seconds']}},
        'max_records': copy.deepcopy(instance['max_records']), 'started_at': at,
        'coaching': {'engine': ENGINE, 'week': week, 'day': day, 'arm': ARM,
            'target': copy.deepcopy(target), 'initial_loads_kg': copy.deepcopy(loads),
            'adaptations': copy.deepcopy(instance['adaptations']), 'setup': copy.deepcopy(setup),
            'equipment_step_kg': step,
            'previous_exercises': [previous_reference(history, eid) for eid in target['exercises']],
            'load_selection_context': {'contract_version': 'novice-load-selection-v1',
                'load_selection': session_inputs(instance, target['exercises'], history)['load_selection']},
            'decisions': [{'exercise_id': eid, 'selected_kg': loads[eid], 'basis': 'user_choice',
                           'automatically_applied': False} for eid in target['exercises']]}}


def record_load_choices(snapshot, choices, history):
    """Validate explicit choices against current records; never choose a load for the user."""
    require(isinstance(choices, dict), 'INVALID_LOAD_CHOICES')
    loads = snapshot['coaching']['initial_loads_kg']
    require(set(choices) <= set(loads), 'UNEXPECTED_LOAD_CHOICE')
    decisions = {d['exercise_id']: d for d in snapshot['coaching']['decisions']}
    for eid, choice in choices.items():
        require(isinstance(choice, dict) and set(choice) == {
            'kind', 'reference_workout_id', 'reference_events_sha256'}, 'INVALID_LOAD_CHOICE')
        require(choice['kind'] in ('repeat', 'increase'), 'INVALID_LOAD_CHOICE')
        ref = previous_reference(history, eid)
        require(ref.get('workout_id') == choice['reference_workout_id']
                and ref.get('history_events_sha256') == choice['reference_events_sha256'],
                'STALE_LOAD_REFERENCE')
        guide = load_selection(ref, snapshot['coaching']['equipment_step_kg'])
        require(choice['kind'] in guide['recorded_choice_types'], 'LOAD_CHOICE_NOT_AVAILABLE')
        base = guide['reference_load_kg']
        require(loads[eid] == base if choice['kind'] == 'repeat' else loads[eid] > base,
                'LOAD_CHOICE_VALUE_MISMATCH')
        decisions[eid].update({
            'choice_kind': choice['kind'], 'reference_workout_id': ref['workout_id'],
            'reference_events_sha256': ref['history_events_sha256'],
            'reference_load_kg': base, 'chosen_increment_kg': round(loads[eid] - base, 8),
            'rule_version': 'novice-confirmed-choice-v1',
            'rule_basis': 'product_adaptation_of_petrizzo_completion_trigger',
            'eligibility_meaning': 'record_matches_choice_not_current_readiness_or_safe_increment',
        })
    snapshot['coaching']['load_choices'] = copy.deepcopy(choices)
    return snapshot


def enrich(snapshot, result):
    result = reference_enrich(snapshot, result)
    result['coaching']['application'] = 'internal_sbd_omission_prototype_not_validated_novice_prescription'
    return result
