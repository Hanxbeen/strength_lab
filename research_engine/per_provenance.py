"""PER source-to-execution comparison; no new prescription or source correction."""
from collections import Counter
from copy import deepcopy

SOURCE_IDS = {
    'Squat': 'barbell_back_squat',
    'Front squat': 'barbell_front_squat',
    'Bench press': 'barbell_bench_press',
    'Deadlift': 'barbell_deadlift',
}

def row_mapping(row):
    original = SOURCE_IDS[row['source_exercise']]
    applied = row['numbered_sbd_anchor']
    return {
        'source_exercise_id': original,
        'applied_exercise_id': applied,
        'substituted': original != applied,
        'basis': 'product_substitution' if original != applied else 'source_label',
        'load_reference_exercise_id': applied,
        'load_reference_basis': 'product_rule_frozen_measured_1rm',
        'source_load_reference_verified': False,
        'source_percentage': row['percent_1rm'],
        'source_locator': deepcopy(row['source']),
        'set_role': row['role'],
    }

def mapping_review(source):
    counts = Counter()
    substitutions = []
    session_keys = set()
    unknown_roles = 0
    for session in source['protocol']['sessions']:
        for row in session['rows']:
            mapped = row_mapping(row)
            counts[row['source_exercise']] += row['sets']
            if row['role'] == 'unspecified':
                unknown_roles += row['sets']
            if mapped['substituted']:
                session_keys.add((session['week'], session['day']))
                substitutions.append({
                    'week': session['week'], 'day': session['day'],
                    'sets': row['sets'], 'reps': row['reps'], **mapped})
    return {
        'kind': 'source_mapping_review',
        'exact_source_replication': False,
        'source_set_counts': dict(counts),
        'total_encoded_sets': sum(counts.values()),
        'working_sets_verified': False,
        'unclassified_sets': unknown_roles,
        'substituted_row_count': len(substitutions),
        'substituted_set_count': sum(row['sets'] for row in substitutions),
        'affected_session_count': len(session_keys),
        'substitutions': substitutions,
        'initial_load_basis': 'frozen_measured_max_of_applied_exercise_times_source_percentage',
        'cached_example_kg_used': False,
        'front_squat_from_back_squat_1rm_supported': False,
        'release_status': 'internal_adaptation_not_public',
    }
