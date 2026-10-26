"""Selection data derived from the validated DB source; no personal prescription."""
from copy import deepcopy
from research_engine.programme_dispatch import validate_source, exercises

def options(item, allowed):
    source = item['definition']
    validate_source(source)
    engine = source['adapter_version']
    protocol = source['protocol']
    common = {
        'source_id': item['source_id'], 'source_version': item['version'],
        'exercise_ids': list(exercises(source)),
        'access': 'internal_preview' if allowed else 'not_released',
        'can_request_start': allowed,
        'start_requires_readiness_check': True,
        'input_list_is_exhaustive': False,
        'input_validation_endpoint': '/v3/programme-readiness',
        'recommendation_status': 'not_assessed',
        'difficulty_rank': None,
        'scientific_approval': False,
        'adaptations': deepcopy(source.get('adaptations', [])),
        'definition_reference': 'definition',
        'personal_weights_kg': None,
    }
    if engine == 'sbd-evidence-synthesis-v1':
        specs=[('SBD_SYNTHESIS',source['title'])]
        context='독립적으로 SBD를 수행하고 작업 중량을 아는 사용자'
        basis='explicit_product_synthesis_not_trial_replication'
        inputs=['age','independent_sbd','current_pain','exercise_restriction','starting_loads_kg',
                'starting_load_origins','initial_loads_kg','rest_seconds','between_exercise_rest_seconds','warmup','equipment_step_kg']
        if source['experience_context']=='trained':inputs+=['training_months']
        limits=['일반 근력훈련 근거를 바탕으로 무게무게가 구성했어요. 이 전체 SBD 일정이 논문에서 직접 실험된 것은 아니에요.',
                '8주·5회 반복·종목 선택은 제품 규칙이에요. 중량은 직접 정하고 실패 반복을 요구하지 않아요.']
    elif engine == 'petrizzo-2018-v1':
        specs = [('FOUR_LIFT', source['title'])]
        context = '네 동작을 배웠고 시작 중량을 알고 있는 성인의 기초 바벨 훈련'
        basis = 'source_structure_with_explicit_choices'
        inputs = ['age', 'independent_sbd', 'independent_ohp', 'starting_loads_kg',
                  'starting_load_origins', 'initial_loads_kg', 'rest_seconds',
                  'between_exercise_rest_seconds', 'warmup', 'equipment_step_kg']
        limits = ['원 연구는 지도자 감독과 초기 5회 중량 평가를 포함했어요.',
                  '프레스와 데드리프트 배치 및 직접 중량 선택을 명시한 구성이에요.',
                  '혼자 처음 배우는 사용자를 위한 자세 평가 기능은 제공하지 않아요.']
    elif engine == 'novice-sbd-choice-v1':
        specs = [('SBD_2D_OMISSION', 'SBD 주 2회 · 직접 중량 선택')]
        context = '독립적으로 SBD를 수행하고 작업 중량을 고를 수 있는 성인의 초급 구성 검토용'
        basis = 'product_adaptation'
        inputs = ['age', 'independent_sbd', 'initial_loads_kg', 'rest_seconds',
                  'between_exercise_rest_seconds', 'warmup', 'equipment_step_kg']
        limits = ['OHP를 제외한 이 전체 구성의 효과는 원 연구에서 검증하지 않았어요.',
                  '첫 중량을 모르는 입문자의 시작 안내는 아직 제공하지 않아요.']
    elif engine in ('sbd-template-v1','per-source-labels-v1'):
        specs = [('PER_ADAPTED', 'SBD 10주 · 주기화 조정안')]
        context = '독립 SBD 수행 성인의 주기화 구성 검토용; 중급 적합성은 미평가'
        basis = 'product_adaptation'
        inputs = ['age', 'independent_sbd', 'measured_sbd_maxes', 'rest_seconds',
                  'between_exercise_rest_seconds', 'warmup', 'equipment_step_kg']
        limits = ['원 자료의 동작을 SBD 기준 동작으로 바꾼 조정이 포함돼요.',
                  '연구와 같은 전체 훈련을 재현하거나 중급 적합성을 보장하지 않아요.']
        if source['id']=='pilot2018-per-source-labels-v1':
            specs=[('PER_SOURCE_LABELS',source['title'])]
            common['exercise_ids']=list(source['exercises'])
            context='SBD와 프런트스쿼트를 독립 수행하고 RPE를 사용하는 훈련 경험자'
            basis='supplement_labels_and_formula_with_explicit_product_choices'
            inputs+=['sex','training_years','powerlifting_years','independent_front_squat',
                     'rpe_familiarized','prior_moderate_high_load_training','accept_source_discrepancy']
            limits=['보충표의 프런트스쿼트를 그대로 포함하며, 해당 중량은 표의 스쿼트 1RM을 참조해요.',
                    '본문의 SBD 설명과 보충표의 종목 표기는 달라요. 연구 전체를 재현했다고 볼 수 없어요.',
                    '원 연구는 감독과 RPE 사전 연습을 포함했어요. RPE 9 초과를 피하되 자동 감량하지 않아요.',
                    '515개는 표에 기록된 전체 세트예요. 준비 세트와 본세트 구분은 확인되지 않았어요.']
    elif engine == 'metd-2021-v1':
        specs = [('MAX', 'SBD 6주 · 고노력도 싱글'),
                 ('MAX_BOFF', 'SBD 6주 · 싱글과 백오프'),
                 ('AMRAP', 'SBD 6주 · 70% 1RM 반복')]
        context = '기존 근력·파워리프팅·RPE 훈련 경험 조건을 확인하는 숙련 구성 검토용'
        basis = 'source_arm_with_execution_choices'
        inputs = ['age', 'independent_sbd', 'training_years', 'powerlifting_years',
                  'rpe_training_years', 'measured_sbd_maxes', 'rest_seconds',
                  'between_exercise_rest_seconds', 'equipment_step_kg']
        limits = ['적은 세트 수가 낮은 난이도를 뜻하지 않아요.',
                  '주요 세트 목표 RPE는 9–9.5예요. 초급 루틴으로 분류하지 않아요.']
    else:
        specs = [('1RMG', '스쿼트·벤치 8주 · 1RM 비율'),
                 ('RPEG', '스쿼트·벤치 8주 · RPE')]
        context = '연구 참여 조건에 부합하는 훈련 경험자의 스쿼트·벤치 구성'
        basis = 'source_arm_with_execution_choices'
        inputs = ['sex', 'age', 'body_mass_kg', 'training_months',
                  'lifts_weekly_last_6_months', 'healthy', 'measured_squat_bench_maxes',
                  'rest_seconds', 'warmup', 'equipment_step_kg']
        limits = ['데드리프트를 포함하지 않아요.',
                  '연구 대상 조건과 다른 사용자에게 적용하는 검토는 완료되지 않았어요.']
    result = []
    for arm, title in specs:
        if engine == 'helms-2018-v1':
            sessions = []
            for week in protocol['weeks']:
                for day, row in enumerate(week['days'], 1):
                    if row.get('kind') == 'post_test':
                        continue
                    target = {'sets_per_exercise': row['sets'], 'reps': row['reps'],
                              'rest_seconds_range': [300, 420]}
                    if arm == '1RMG':
                        target.update(load_kind='conditional_percentage_1rm',
                                      table_percent_1rm=row['percent_1rm'],
                                      conditional_progression=row['conditional_progression'])
                    else:
                        target.update(load_kind='user_selected_rpe', rpe_range=row['rpe_range'])
                    sessions.append({'week': week['week'], 'day': day,
                                     'exercise_ids': common['exercise_ids'], 'target': target})
            duration = len(protocol['weeks'])
        else:
            sessions = deepcopy(protocol['sessions'])
            duration = protocol['weeks']
        arm_inputs = list(inputs)
        if engine == 'metd-2021-v1' and arm != 'AMRAP':
            arm_inputs += ['initial_rpe_loads_kg', 'warmup']
        if engine == 'helms-2018-v1' and arm == 'RPEG':
            arm_inputs += ['initial_rpe_loads_kg']
        value = dict(common, arm=arm, title=title, experience_context=context,
                     prescription_basis=basis, required_inputs=arm_inputs, limits=limits,
                     duration_weeks=duration, training_sessions=len(sessions), sessions=sessions)
        if engine == 'metd-2021-v1':
            value['arm_prescription'] = deepcopy(protocol['arms'][arm])
        elif engine in ('novice-sbd-choice-v1', 'petrizzo-2018-v1', 'sbd-evidence-synthesis-v1'):
            value['arm_prescription'] = {k: deepcopy(protocol[k]) for k in
                ('working_sets', 'reps', 'automatic_load_adjustment', 'source_stop_rule', 'product_stop_rule')}
        if engine in ('sbd-template-v1','per-source-labels-v1'):
            from research_engine.per_provenance import mapping_review
            value['source_mapping_review'] = mapping_review(source)
        result.append(value)
    return result
