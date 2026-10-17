"""Factual result projection. No grading, generated advice, or inferred growth."""
from copy import deepcopy
from research_engine.core import digest


def project(record):
    execution = record['execution']
    groups = {}
    references = {m['exercise_id']: m for m in execution.get('max_records', [])}
    for row in execution['sets']:
        actual = row.get('actual')
        target = row.get('weight_kg')
        maximum = references.get(row['exercise_id'])
        baseline = maximum['weight_kg'] if maximum else None
        series = groups.setdefault(row['exercise_id'], [])
        series.append({
            'set_id': row['id'], 'ordinal': len(series) + 1, 'status': row['status'],
            'target_weight_kg': target,
            'actual_weight_kg': actual['weight_kg'] if actual else None,
            'target_reps': deepcopy(row['reps']),
            'actual_reps': actual['reps'] if actual else None,
            'weight_delta_kg': actual['weight_kg'] - target if actual and target is not None else None,
            'reference_max_id': maximum['id'] if maximum else None,
            'reference_max_kind': maximum['kind'] if maximum else None,
            'target_percent_reference_max': 100 * target / baseline if baseline and target is not None else None,
            'actual_percent_reference_max': 100 * actual['weight_kg'] / baseline if baseline and actual else None,
            'changes': deepcopy(row.get('changes', [])),
            'reason_reports': deepcopy(row.get('reason_reports', {})),
            'actual': deepcopy(actual),
        })
    rests = []
    for rest in execution.get('rests', []):
        confirmed = rest['outcome'] != 'interrupted' and not rest.get('measurement_status')
        original = rest.get('original_target_seconds', rest['target_seconds'])
        elapsed = rest['elapsed_seconds'] if confirmed else None
        rests.append({'after_set_id': rest['after_set_id'], 'kind': rest.get('kind'),
                      'planned_seconds': original, 'selected_seconds': rest['target_seconds'],
                      'actual_seconds': elapsed,
                      'delta_from_plan_seconds': elapsed - original if elapsed is not None else None,
                      'outcome': rest['outcome'], 'measurement_status': 'timer_confirmed' if confirmed else 'unconfirmed',
                      'adjustments': deepcopy(rest.get('adjustments', []))})
    termination = next((e for e in reversed(record['events']) if e['type'] in ('finish','interrupt')), None)
    return {
        'schema_version': 'workout-result-v1', 'workout_id': record['workout_id'],
        'programme_id': execution['programme_id'], 'programme_version': execution['programme_version'],
        'execution_policy': execution['policy_version'], 'revision': execution['revision'],
        'event_digest': digest(record['events']), 'state': execution['state'],
        'termination': deepcopy(termination), 'resume_available': execution['state'] not in ('completed','stopped'),
        'charts': {'sets_by_exercise': groups, 'rests': rests,
                   'x_axis': 'set_ordinal_within_exercise', 'weight_unit': 'kg',
                   'missing_value_policy': 'gap_not_zero', 'research_growth_slope': None},
        'counts': {'recorded': sum(r.get('actual') is not None for r in execution['sets']),
                   'unknown': sum(r['status'] == 'pending' for r in execution['sets']),
                   'skipped': sum(r['status'] == 'skipped' for r in execution['sets']),
                   'not_attempted': sum(r['status'] == 'not_attempted' for r in execution['sets'])},
        'assessment': None,
        'coaching': {'mode': 'on_explicit_request', 'available': False,
                     'reason': 'service_not_connected', 'free_request_limit': None},
    }
