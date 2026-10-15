"""Deterministic execution ledger. Research targets are never overwritten by actuals."""
import copy
from datetime import datetime
from decimal import Decimal
from .core import InvalidProgramme, digest, number, instantiate_session, progression

POLICY = 'execution-ledger-v2'
DEPENDENT_POLICY = 'execution-ledger-v3'
from .execution_facts import pain_reported, short_interset_rests
REASONS = {'fatigue', 'pain', 'time', 'equipment', 'interruption', 'other'}

def require(condition, code):
    if not condition:
        raise InvalidProgramme(code)

def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.utcoffset() is not None, 'TIMEZONE_REQUIRED')
        return result
    except (AttributeError, TypeError, ValueError):
        raise InvalidProgramme('INVALID_TIMESTAMP')

def kg(value, unit):
    require(unit in ('kg', 'lb') and number(value, 0, 5000), 'INVALID_MASS')
    result = Decimal(str(value)) * (Decimal('0.45359237') if unit == 'lb' else Decimal(1))
    require(result <= 2000, 'INVALID_MASS')
    return float(result)

def max_record(record):
    require(isinstance(record.get('id'), str) and 0 < len(record['id']) <= 100, 'MAX_ID_REQUIRED')
    require(isinstance(record.get('exercise_id'), str) and bool(record['exercise_id']), 'EXERCISE_REQUIRED')
    require(record.get('kind') in ('measured', 'estimated'), 'MAX_KIND_REQUIRED')
    timestamp(record.get('measured_at'))
    value = kg(record.get('value'), record.get('unit'))
    require(value > 0, 'INVALID_MAX')
    return {**copy.deepcopy(record), 'weight_kg': value}

def create_workout(bundle, session_id, profile, setup, max_records, started_at):
    start = timestamp(started_at)
    setup = copy.deepcopy(setup)
    # API callers must reference an immutable registration, not supply anonymous max numbers.
    setup.pop('measured_1rm_kg', None)
    refs = setup.pop('max_record_ids', {})
    normalized = [max_record(r) for r in max_records]
    require(len({r['id'] for r in normalized}) == len(normalized), 'DUPLICATE_MAX_ID')
    selected = []
    for exercise_id, record_id in refs.items():
        record = next((r for r in normalized if r['id'] == record_id), None)
        require(record is not None and record['exercise_id'] == exercise_id, 'MAX_EXERCISE_MISMATCH')
        require(record['kind'] == 'measured', 'MEASURED_MAX_REQUIRED')
        require(timestamp(record['measured_at']) <= start, 'FUTURE_MAX')
        setup.setdefault('measured_1rm_kg', {})[exercise_id] = record['weight_kg']
        selected.append(record)
    session = instantiate_session(bundle, session_id, profile, setup)
    return {'schema_version': 2, 'policy_version': POLICY, 'programme_id': bundle['programme_id'],
            'programme_version': bundle['programme_version'], 'source': copy.deepcopy(bundle['definition']['source']),
            'definition': copy.deepcopy(bundle['definition']), 'session': session,
            'max_records': selected, 'started_at': started_at}

def guide(code, text, actions, basis='product_policy', evidence=None):
    return {'code': code, 'text': text, 'actions': actions, 'basis': basis,
            'policy_version': POLICY if basis == 'product_policy' else None, 'evidence': evidence}

def replay(workout, events):
    """Strict state machine. Rest uses elapsed wall time; pauses never erase physical recovery."""
    if workout['policy_version'] == 'execution-ledger-v1':
        from .workout_legacy_v1 import replay as legacy_replay
        result = legacy_replay(workout, events)
        result['historical_guides'] = result['guides']
        result['guides'] = [guide('LEGACY_READ_ONLY', '기존 버전 운동이에요. 기록을 확인하거나 종료할 수 있어요.',
                                  ['finish'] if result['state'] not in ('completed','stopped') else [])]
        result['next_set_id'] = None
        result['legacy_read_only'] = True
        result['migration_notice'] = '기존 계산 버전 기록이에요. 종료와 열람만 지원해요.'
        return result
    require(workout['policy_version'] in (POLICY, DEPENDENT_POLICY), 'UNSUPPORTED_POLICY')
    require(len(events) <= 2000, 'EVENT_LIMIT')
    rows = copy.deepcopy(workout['session']['sets'])
    for row in rows:
        row.update(status='pending', selected_weight_kg=row['weight_kg'], actual=None, changes=[])
    state = 'active'; cursor = 0; rest = None; rests = []; seen = {}; paused_from = None
    reason_reports = {}; event_targets = {}
    last_time = timestamp(workout['started_at']); guides = []
    def resolve_dependencies():
        if workout['policy_version'] != DEPENDENT_POLICY:return
        from .coaching import rounded
        for row in rows:
            dependency=row.get('load',{})
            if dependency.get('kind')!='percent_actual_set':continue
            parent=next((r for r in rows if r['id']==dependency['set_id']),None)
            actual=parent.get('actual') if parent else None
            available=actual is not None and actual['reps']==1 and actual['weight_kg']>0
            raw=actual['weight_kg']*dependency['percent']/100 if available else None
            row['unrounded_weight_kg']=raw
            representable=available and raw>=dependency['equipment_step_kg']/2
            row['weight_kg']=rounded(raw,dependency['equipment_step_kg']) if representable else None
            row['load_resolution']='actual_single' if representable else 'source_single_unavailable' if not available else 'below_equipment_minimum'
            if not row['changes']:row['selected_weight_kg']=row['weight_kg']
    def close_rest(at, outcome):
        nonlocal rest
        if rest is not None:
            elapsed = (at - timestamp(rest['started_at'])).total_seconds()
            rests.append({**rest, 'elapsed_seconds': elapsed, 'outcome': outcome,
                          'shortfall_seconds': max(0, rest['target_seconds'] - elapsed)})
            rest = None
    for event in events:
        require(isinstance(event, dict), 'INVALID_EVENT')
        eid = event.get('id'); require(isinstance(eid, str) and 0 < len(eid) <= 100, 'EVENT_ID_REQUIRED')
        fingerprint = digest(event)
        if eid in seen:
            require(seen[eid] == fingerprint, 'EVENT_ID_CONFLICT')
            continue
        seen[eid] = fingerprint
        at = timestamp(event.get('at')); require(at >= last_time, 'EVENT_TIME_ORDER'); last_time = at
        kind = event.get('type')
        if kind == 'reason_record':
            from .reasons import validate as validate_reason
            target=event.get('target_event_id')
            require(target in event_targets, 'REASON_TARGET_NOT_FOUND')
            old=reason_reports.get(target)
            require(event.get('supersedes_event_id') == (old['event_id'] if old else None), 'REASON_REVISION_CONFLICT')
            report={**validate_reason(event.get('response')), 'event_id':eid, 'recorded_at':event['at'],
                    'target_event_id':target,'supersedes_event_id':event.get('supersedes_event_id')}
            reason_reports[target]=report
            target_row=next((r for r in rows if r['id']==event_targets[target]),None)
            if target_row is not None:
                target_row.setdefault('reason_reports',{})[target]=report
            if 'pain_discomfort' in report['reason_codes'] and state in ('active','resting'):
                paused_from=state;state='paused'
            continue
        require(state not in ('completed', 'stopped'), 'WORKOUT_CLOSED')
        resolve_dependencies()
        current = rows[cursor] if cursor < len(rows) else None
        if kind in ('change_load','set_result','skip_set','finish'):
            event_targets[eid]=current['id'] if current and kind!='finish' else None
        if kind == 'pause':
            require(state in ('active', 'resting'), 'CANNOT_PAUSE')
            paused_from = state; state = 'paused'
        elif kind == 'resume':
            require(state == 'paused', 'NOT_PAUSED'); state = paused_from; paused_from = None
        elif kind == 'rest_end':
            require(state == 'resting' and rest is not None, 'NOT_RESTING')
            require(event.get('outcome') in ('completed', 'skipped'), 'REST_OUTCOME_REQUIRED')
            elapsed = (at - timestamp(rest['started_at'])).total_seconds()
            require(event['outcome'] != 'completed' or elapsed >= rest['target_seconds'], 'REST_NOT_ELAPSED')
            close_rest(at, event['outcome']); state = 'active'
        elif kind == 'finish':
            reason = event.get('reason')
            unresolved = any(r['status'] == 'pending' for r in rows)
            require(not unresolved or reason in REASONS, 'EARLY_FINISH_REASON_REQUIRED')
            close_rest(at, 'interrupted')
            for row in rows:
                if row['status'] == 'pending': row.update(status='not_attempted', reason=reason)
            state = 'stopped' if unresolved or reason == 'pain' else 'completed'
        elif kind in ('change_load', 'set_result', 'skip_set'):
            require(state == 'active' and current is not None, 'SET_NOT_AVAILABLE')
            require(event.get('set_id') == current['id'], 'SET_ORDER_MISMATCH')
            if kind == 'change_load':
                require(event.get('reason') in REASONS, 'CHANGE_REASON_REQUIRED')
                value = kg(event.get('value'), event.get('unit'))
                current['changes'].append({'event_id': eid, 'at': event['at'], 'from_kg': current['selected_weight_kg'],
                                           'to_kg': value, 'reason': event['reason']})
                current['selected_weight_kg'] = value
                if event['reason'] == 'pain':
                    paused_from = state; state = 'paused'
                continue
            if kind == 'skip_set':
                require(event.get('reason') in REASONS, 'SKIP_REASON_REQUIRED')
                current.update(status='skipped', reason=event['reason'])
            else:
                require(current['selected_weight_kg'] is not None, 'SOURCE_LOAD_UNAVAILABLE_SELECT_OR_SKIP')
                reps = event.get('reps')
                require(type(reps) == int and 0 <= reps <= 100, 'INVALID_REPS')
                reason = event.get('reason')
                require(reason is None or reason in REASONS, 'INVALID_REASON')
                rir = event.get('rir')
                require(rir is None or number(rir, 0, 10), 'INVALID_RIR')
                rpe = event.get('rpe')
                require(rpe is None or (number(rpe, 1, 10) and rpe * 2 == int(rpe * 2)), 'INVALID_RPE')
                require(event.get('failure') in (None, 'momentary_concentric', 'technical', 'not_reached'), 'INVALID_FAILURE')
                # A missing explanation must never prevent saving actual repetitions.
                current.update(status='recorded', actual={'reps': reps, 'weight_kg': current['selected_weight_kg'],
                               'rir': rir, 'rpe': rpe, 'failure': event.get('failure'), 'reason': reason, 'at': event['at']})
            cursor += 1
            if kind == 'set_result' and cursor < len(rows):
                transition = rows[cursor]['exercise_id'] != current['exercise_id']
                target = (workout['session']['user_choices']['between_exercise_rest_seconds'] if transition
                          else current['rest_after']['seconds'])
                rest = {'after_set_id': current['id'], 'started_at': event['at'], 'target_seconds': target,
                        'kind': 'between_exercises' if transition else 'between_sets',
                        'basis': 'explicit_setup' if transition else current['rest_after'].get('basis','source_reported')}
                state = 'resting'
            if event.get('reason') == 'pain':
                paused_from = state; state = 'paused'
        else:
            raise InvalidProgramme('UNKNOWN_EVENT_TYPE')
    resolve_dependencies()
    current = rows[cursor] if cursor < len(rows) else None
    if state == 'paused':
        guides.append(guide('PAUSED', '운동을 멈췄어요. 계속할지, 여기서 마칠지 선택해 주세요.', ['resume', 'finish']))
    if pain_reported(rows):
        guides.append(guide('PAIN_REPORTED', '통증이 기록됐어요. 앱은 통증에 맞는 중량이나 재개 여부를 판단하지 않아요.', ['finish']))
    if rest and state == 'resting':
        guides.append(guide('RESTING', '휴식 중이에요. 일찍 끝내면 실제 쉰 시간이 따로 기록돼요.', ['rest_end', 'pause', 'finish']))
    if state == 'active' and current:
        guides.append(guide('NEXT_SET', '중량을 확인하고 수행한 횟수를 기록해 주세요. 어렵다면 중량을 바꾸거나 건너뛸 수 있어요.', ['change_load', 'set_result', 'skip_set', 'pause', 'finish']))
        if current['selected_weight_kg'] is None:
            guides[-1]=guide('SOURCE_LOAD_UNAVAILABLE', '기준 단일 반복이 없어 백오프 중량을 계산하지 못했어요. 중량을 직접 선택하거나 건너뛰어 주세요.', ['change_load','skip_set','finish'])
    if state == 'active' and current is None:
        guides.append(guide('READY_TO_FINISH', '모든 세트를 기록했어요. 운동을 마쳐 주세요.', ['finish']))
    if state in ('completed', 'stopped'):
        guides.append(guide('SAVED_RESULT', '수행한 세트와 건너뛴 세트를 구분해 기록했어요. 미완료 분량을 다음 운동에 자동으로 더하지 않아요.', []))
    if short_interset_rests(rests):
        guides.append(guide('REST_SHORTFALL', '목표보다 짧게 쉰 구간이 있어요. 기록 비교이며, 운동 효과나 다음 중량을 단정하는 기준은 아니에요.', []))
    chart = []; achieved = 0; planned = 0
    for row in rows:
        actual = row['actual']; target = row['reps']['min']; planned += target or 0
        completed = actual['reps'] if actual else 0
        achieved += min(completed, target) if target is not None else 0
        chart.append({'set_id': row['id'], 'exercise_id': row['exercise_id'], 'status': row['status'],
                      'target_reps': row['reps'], 'actual_reps': completed if actual else None,
                      'target_weight_kg': row['weight_kg'], 'actual_weight_kg': actual['weight_kg'] if actual else None,
                      'reps_shortfall': max(0, target - completed) if target is not None and row['status'] != 'pending' else None,
                      'weight_delta_kg': actual['weight_kg'] - row['weight_kg'] if actual and row['weight_kg'] is not None else None})
    recorded = [r for r in rows if r['actual']]
    if recorded and state not in ('completed', 'stopped', 'paused') and not pain_reported(rows):
        last = recorded[-1]; actual = last['actual']
        # The bounded half-squat/deadlift rule must never leak into accessory RIR movements.
        if actual.get('reason') != 'pain' and current and current['exercise_id'] == last['exercise_id'] and last['load']['kind'] == 'initial_percent_1rm':
            instruction = progression(workout['definition'], actual['reps'])
            if instruction['action'] == 'decrease':
                guides.append(guide('SOURCE_DECREASE_RANGE', '원 연구에는 목표 횟수 미달 시 다음 세트 중량을 낮추는 규칙이 있어요. 자동 변경하지 않아요.',
                                    ['change_load'] if state == 'active' else [], 'source_reported', instruction))
        elif actual.get('reason') != 'pain' and last['load']['kind'] == 'rir':
            if actual['rir'] is None:
                guides.append(guide('EFFORT_UNKNOWN', '남은 반복 여유를 기록하지 않아 목표 강도 달성 여부는 알 수 없어요.', []))
            elif actual['rir'] != last['load']['target']:
                guides.append(guide('RIR_DIFFERENCE', '기록한 반복 여유가 목표와 달라요. 다음 중량은 직접 선택해 주세요. 자동 환산하지 않아요.', []))
        elif actual.get('reason') != 'pain' and last['load']['kind'] == 'repetition_maximum':
            guides.append(guide('RM_TARGET', '기록한 반복수와 반복 종료 사유를 확인해 주세요. 원문만으로 다음 중량을 정확히 계산할 수는 없어요.',
                                [], 'source_reported', workout['definition']['provenance']['progression']))
    open_repetition_targets=any(r['reps']['min'] is None for r in rows)
    if workout['policy_version']==DEPENDENT_POLICY:
        for item in guides:
            if item['policy_version'] is not None:item['policy_version']=DEPENDENT_POLICY
    return {'schema_version': 2, 'policy_version': workout['policy_version'], 'state': state, 'revision': len(seen),
            'programme_id': workout['programme_id'], 'programme_version': workout['programme_version'],
            'source': workout['source'], 'max_records': workout['max_records'], 'sets': rows,
            'next_set_id': current['id'] if current and state not in ('completed', 'stopped') else None,
            'active_rest': rest, 'rests': rests, 'rest_count': len(rests), 'guides': guides,
            'reason_reports': reason_reports,
            'summary': {'planned_sets': len(rows), 'recorded_sets': len(recorded),
                        'skipped_sets': sum(r['status'] == 'skipped' for r in rows),
                        'not_attempted_sets': sum(r['status'] == 'not_attempted' for r in rows),
                        'minimum_reps_completion_percent': None if open_repetition_targets or not planned or any(r['status']=='pending' for r in rows) else round(100 * achieved / planned, 2),
                        'minimum_reps_completion_bounds_percent': None if open_repetition_targets or not planned else [round(100 * achieved / planned, 2), round(100 * (achieved + sum(r['reps']['min'] for r in rows if r['status']=='pending')) / planned, 2)],
                        'unknown_sets': sum(r['status']=='pending' for r in rows),
                        'metric_version': 'effort-target-no-rep-ratio-v1' if open_repetition_targets else 'minimum-reps-v2',
                        'definition': 'No aggregate repetition ratio for effort-terminated sets.' if open_repetition_targets else 'Sum of per-set reps capped at prescribed minimum / planned minimum reps. Not strength gain or scientific adherence.',
                        'rest_shortfall_seconds': sum(r['shortfall_seconds'] for r in short_interset_rests(rests)),
                        'chart': chart, 'growth_prediction': None}}
