"""Versioned educational copy and factual projections, separate from source prescriptions."""
from copy import deepcopy
from research_engine.core import digest

VERSION = 'experience-content-v1'
BENCH_MANUAL = 'https://www.nsca.com/contentassets/24f7e187e9aa4a588439c9612231c7fd/tsac-module-3.0--3.3.pdf#page=19'
NHS = 'https://www.nhs.uk/live-well/exercise/strength-exercises/'
MOVEMENT = 'https://www.nsca.com/education/articles/ptq/teaching-resistance-training-movement-patterns/'
# These are editorial teaching summaries, never claims that a routine trial tested technique.
_GUIDES = {
 'barbell_back_squat': {
  'title':'바벨 백 스쿼트','equipment':['스쿼트 랙','바벨·원판','높이를 맞춘 세이프티'],
  'setup':['세이프티 높이와 바벨 거치 높이를 확인해요.','바를 목이 아닌 등 위에 안정적으로 놓고 양발을 편한 너비로 벌려요.'],
  'steps':['발바닥으로 바닥을 지지하며 무릎과 엉덩이를 함께 굽혀요.','몸통을 지지하고 균형을 유지할 수 있는 범위까지 내려가요.','발로 바닥을 밀어 일어서고 안정된 뒤 다음 반복을 시작해요.'],
  'mistakes':['뒤꿈치가 들리거나 균형을 잃은 채 깊이 내려가기','통제할 수 없는 속도로 내려가기','목으로 바벨을 받치기'],
  'demo':('https://www.nsca.com/education/videos/exercise-technique-high-bar-back-squat/','High-bar back squat'),
  'role':'스쿼트 종목 수행 연습과 중량 기록. 시연은 하이바 예시이며 다른 바 위치의 동일성을 보장하지 않아요.'},
 'barbell_bench_press': {
  'title':'바벨 벤치프레스','equipment':['벤치','바벨·원판','세이프티 또는 숙련된 보조자'],
  'setup':['벤치와 랙을 고정하고 실패 시 바를 안전하게 받을 방법을 확인해요.','발을 바닥에 놓고 어깨와 등을 벤치에 안정적으로 지지해요.','엄지로 바를 감싸고 손목과 팔의 정렬을 확인해요.'],
  'steps':['보조를 받아 바를 꺼내 안정시켜요.','바를 통제하며 가슴 쪽으로 내리고 튕기지 않아요.','몸의 지지를 유지하며 바를 밀어 올려요.','반복이 끝나면 양쪽 걸이에 걸린 것을 확인해요.'],
  'mistakes':['가슴에서 바를 튕기기','손목이 과도하게 꺾이기','보조 장치 없이 감당할 수 없는 중량 시도하기'],
  'demo':(BENCH_MANUAL,'Module 3.2-6, Barbell Bench Press, PDF page 19'),
  'role':'벤치프레스 종목 수행 연습과 중량 기록.'},
 'barbell_deadlift': {
  'title':'바벨 데드리프트','equipment':['바벨·원판','평평하고 미끄럽지 않은 바닥'],
  'setup':['바를 발 가까이에 두고 양발을 안정적으로 놓아요.','엉덩이를 뒤로 보내며 바를 잡고 몸통을 지지해요.'],
  'steps':['바와 몸의 거리를 가깝게 유지하며 바닥을 밀어요.','무릎과 엉덩이를 펴서 서되 허리를 뒤로 꺾지 않아요.','엉덩이를 뒤로 보내며 바를 통제해 내려놓고 자세를 다시 확인해요.'],
  'mistakes':['바가 몸에서 멀어지기','바를 갑자기 잡아당기기','마지막에 허리를 과도하게 젖히기'],
  'demo':('https://www.nsca.com/education/videos/exercise-technique-deadlift/','Deadlift'),
  'role':'데드리프트 종목 수행 연습과 중량 기록. 그립·스탠스 변경은 비교 조건에 남겨요.'},
 'barbell_standing_shoulder_press': {
  'title':'스탠딩 숄더프레스','equipment':['바벨·원판','랙','머리 위 여유 공간'],
  'setup':['발을 안정적으로 놓고 바를 어깨 앞에서 지지해요.','손목과 팔꿈치 위치를 확인하고 몸통을 지지해요.'],
  'steps':['얼굴을 피하며 바를 머리 위로 밀어요.','다리 반동이나 허리 과신전 없이 지지할 수 있는 범위에서 수행해요.','바를 어깨 앞으로 천천히 되돌려요.'],
  'mistakes':['바를 올리려고 허리를 크게 젖히기','다리 반동으로 다른 동작으로 바꾸기','머리 위 장애물 확인을 생략하기'],
  'demo':('https://www.acefitness.org/resources/everyone/exercise-library/71/standing-shoulder-press/','Standing shoulder press, barbell'),
  'role':'Petrizzo 원 구성의 수직 밀기 종목. SBD 합계에 포함하지 않아요.'},
 'barbell_front_squat': {
  'title':'프런트 스쿼트','equipment':['스쿼트 랙','바벨·원판','세이프티'],
  'setup':['바를 어깨 앞에 안정적으로 지지하고 세이프티를 확인해요.','팔꿈치를 들어 바가 굴러가지 않도록 지지해요.'],
  'steps':['몸통과 바의 지지를 유지하며 무릎과 엉덩이를 굽혀요.','균형과 팔꿈치 위치를 유지할 수 있는 범위에서 내려가요.','발로 바닥을 밀어 일어난 뒤 바를 랙에 놓아요.'],
  'mistakes':['팔꿈치가 떨어져 바가 앞으로 굴러가기','손목만으로 바를 지지하기','지지 자세가 불확실한데 부하를 늘리기'],
  'demo':('https://www.nsca.com/education/videos/exercise-technique-front-squat/','Front squat'),
  'role':'PER 보충표의 원종목을 보존해요. 표의 백 스쿼트 1RM 참조는 동일한 동작 또는 개인 적정 중량을 뜻하지 않아요.'},
 'sit_to_stand': {
  'title':'의자에서 일어나기','equipment':['움직이지 않는 의자','미끄럽지 않은 바닥'],
  'setup':['발바닥이 바닥에 닿도록 의자 앞쪽에 앉아요.'],
  'steps':['몸을 조금 앞으로 기울여요.','다리로 천천히 일어나 균형을 잡아요.','천천히 다시 앉아요.'],
  'mistakes':['의자가 밀리는 상태로 시작하기','균형을 잃으며 급하게 일어나기'],
  'demo':(NHS,'Sit-to-stand'),'role':'스쿼트 전 무부하 동작 경험. 바벨 자세 인증은 아니에요.'},
 'wall_press_up': {
  'title':'벽 밀기','equipment':['움직이지 않는 벽','미끄럽지 않은 바닥'],
  'setup':['벽에서 팔 길이 정도 떨어져 가슴 높이에 손을 대요.'],
  'steps':['몸을 곧게 유지하며 팔꿈치를 굽혀 벽에 가까워져요.','천천히 벽을 밀어 처음 위치로 돌아와요.'],
  'mistakes':['몸통이 처지거나 허리를 과도하게 젖히기','발이 미끄러지는 위치에서 연습하기'],
  'demo':(NHS,'Wall press-up'),'role':'밀기 동작 경험. 벤치프레스 중량을 추정하지 않아요.'},
 'wall_hip_hinge': {
  'title':'엉덩이 뒤로 보내기','equipment':['벽 앞의 빈 공간'],
  'setup':['벽을 등지고 서서 무릎을 가볍게 풀어요.'],
  'steps':['엉덩이를 뒤로 보내 벽에 가볍게 닿게 해요.','허리를 억지로 굽히지 않고 편한 범위에서 돌아와요.'],
  'mistakes':['엉덩이 대신 허리만 구부리기','벽에 닿으려 균형을 잃을 정도로 멀리 서기'],
  'demo':(MOVEMENT,'Hip hinge teaching progression'),
  'role':'데드리프트 전 힙힌지 경험. 벽을 사용하는 독립 연습은 제품 교육 구성입니다.'},
}

def exercise_guide(exercise_id):
    row = _GUIDES.get(exercise_id)
    if row is None:
        return {'exercise_id':exercise_id,'available':False,'reason':'UNREVIEWED_EXERCISE'}
    value = deepcopy(row); url, section = value.pop('demo')
    value.update(exercise_id=exercise_id, available=True, content_version=VERSION,
        basis='editorial_education_summary_not_trial_protocol',
        breathing_and_bracing=['반복 전 몸통을 안정적으로 지지해요.','가벼운 동작 학습에서는 자연스럽게 호흡하고 장시간 숨을 참도록 강요하지 않아요.','고중량 호흡과 지지 방법을 모르면 지도자에게 확인한 뒤 진행해요.'],
        stop_guidance=['통증·어지럼·조절 불확실이 있으면 수행을 멈춰요.','더 가벼운 중량으로 계속해도 된다고 앱이 판단하지 않아요.','자세나 장비 사용이 불확실하면 자격 있는 지도자의 도움을 받아요.'],
        demonstration={'url':url,'section':section,'kind':'external_instruction','media_embedded':False,
                       'fallback':'자료가 열리지 않으면 안내를 확인하고, 자세가 불확실한 경우 시작하지 말고 도움을 요청해요.'},
        sources=[{'url':url,'locator':section,'role':'professional_or_public_health_instruction'}],
        limitations=['개인의 자세·가동범위·안전성을 판정하는 기능이 아니에요.','교육 요약은 루틴 연구에서 검증한 기술 교육 절차라는 뜻이 아니에요.'])
    return value

SCENARIOS = [
 ('first_load','첫 중량이 불확실해요','임의 1RM이나 빈 봉 20kg을 채우지 않아요. 입문 안내를 확인하거나 필요한 기록을 준비한 뒤 미리보기를 다시 확인해요.',['review_entry','preview']),
 ('target_missed','목표 횟수보다 적게 했어요','실제 횟수를 그대로 기록해요. 이유를 모르면 모름으로 남기며 미달을 성장 실패로 해석하지 않아요.',['set_result','reason_record']),
 ('decrease_load','중량을 줄이고 싶어요','다음 세트 전에 직접 중량과 이유를 기록해요. 자동 감량 계수는 적용하지 않아요.',['change_load']),
 ('increase_load','중량을 늘리고 싶어요','이 루틴의 계산 규칙과 현재 목표를 먼저 확인해요. 직접 변경은 원래 목표와 따로 보존돼요.',['change_load']),
 ('rest_change','휴식 시간을 바꾸고 싶어요','휴식 중 목표 시간을 바꿀 수 있어요. 원래 목표·선택 시간·실제 시간을 구분해요.',['rest_adjust','rest_end']),
 ('skip','이번 세트를 건너뛰어요','건너뛴 이유를 남겨요. 미기록과 구분하고 다음 회차에 자동 추가하지 않아요.',['skip_set']),
 ('pain','통증이나 불편함이 있어요','수행을 멈추고 기록해요. 앱은 통증 원인·안전한 재개·적정 감량을 판단하지 않아요.',['pause','finish']),
 ('interrupt','여기서 운동을 중단해요','명시적 종료와 연결 중단을 구분해요. stopped 기록은 다시 열지 않아요.',['finish','interrupt']),
 ('reconnect','연결이 끊겼어요','같은 계정에서 저장 여부와 리비전을 조회해요. 미확인 요청은 같은 ID·같은 내용으로 확인하고, 대기 기록 동기화 후 무활동 판정을 요청해요.',['reload','reconcile']),
 ('unsupported_change','종목이나 전체 일정을 바꾸고 싶어요','임의 종목 대체·전체 일정 재편성·장기 공백 자동 처방은 지원하지 않아요. 기록을 확인하고 새 루틴을 명시적으로 선택할 수 있어요.',['review_result','choose_programme']),
]

def guidance():
    return {'content_version':VERSION,'basis':'product_workflow_not_medical_or_growth_prediction',
        'scenarios':[{'id':i,'title':t,'text':s,'action_ids':a} for i,t,s,a in SCENARIOS],
        'actions':{
            **{name:{'method':'POST','path':'/v2/workouts/{workout_id}/events','event_type':name,
                     'requires':['expected_revision','event.id','event.at'],'authority':'server_state_validation'}
               for name in ['set_result','reason_record','change_load','rest_adjust','rest_end','skip_set','pause','resume','finish','interrupt']},
            'reload':{'method':'GET','path':'/v2/workouts/{workout_id}'},
            'reconcile':{'method':'POST','path':'/v2/workouts/{workout_id}/reconcile','requires':['pending_local_events_resolved']},
            'preview':{'method':'POST','path':'/v3/routines/preview'},
            'review_entry':{'method':'GET','path':'/v3/entry/learning-paths'},
            'review_result':{'method':'GET','path':'/v2/workouts/{workout_id}/result'},
            'choose_programme':{'method':'GET','path':'/v3/routines'}},
        'limitations':['상황 안내의 행동 목록은 실행 권한이 아니에요. 현재 상태의 available_action_ids와 서버 검증을 따라요.',
                       '통신 오류를 운동 실패나 저장 성공으로 간주하지 않아요.']}

def routine_content(source, option):
    from .research_charts import chart_for
    engine=source['adapter_version']
    why={
      'helms-2018-v1':'같은 스쿼트·벤치 일정에서 1RM 비율과 RPE 기반 부하 선택을 구분한 연구 구성입니다.',
      'metd-2021-v1':'숙련자의 적은 훈련량을 탐색한 연구입니다. 싱글·백오프·반복 수행의 구성을 구분하며 적은 양이 쉬운 운동을 뜻하지 않아요.',
      'petrizzo-2018-v1':'스쿼트·벤치·프레스·데드리프트를 배우고 작업 중량을 아는 성인의 기초 구성입니다. 연구의 감독 환경을 앱이 대신하지 않아요.',
      'per-source-labels-v1':'PER 보충표의 원종목과 수식을 보존한 주기화 구성입니다. 본문과 보충표의 차이 및 명시적 제품 선택을 함께 확인해요.',
      'sbd-evidence-synthesis-v1':'일반 근력훈련 근거를 참고해 SBD 반복 연습을 배치한 제품 구성입니다. 이 정확한 8주 구성 자체를 실험한 연구는 없어요.',
    }.get(engine,'원 정의와 명시된 제품 변경을 함께 확인하는 구성입니다.')
    return {'content_version':VERSION,'source_version':digest(source),'arm':option['arm'],
        'title':option['title'],'audience':option['experience_context'],'why_this_structure':why,
        'schedule':{'duration_weeks':option['duration_weeks'],'training_sessions':option['training_sessions'],
                    'sessions_reference':'sessions','basis':option['prescription_basis']},
        'setup':{'required_inputs':deepcopy(option['required_inputs']),
                 'load_rule':deepcopy(option.get('arm_prescription',{})),
                 'text':'현재 기록·직접 선택·원 연구 계산을 구분해요. 필수 입력은 input_contract와 미리보기 응답으로 확인해요.',
                 'rest_and_warmup':'표에 있는 목표와 사용자가 정해야 하는 값을 구분해요. 누락된 휴식·준비운동을 임의로 채우지 않아요.',
                 'progression':'현재 회차의 계산과 수행 기록을 확인한 뒤 다음 회차 API를 사용해요. 미완료 분량을 자동으로 더하거나 장기 공백 뒤 부하를 자동 처방하지 않아요.'},
        'exercises':[exercise_guide(e) for e in option['exercise_ids']],
        'study_context':deepcopy(source.get('study',source.get('study_context',
            {'application':source.get('application',source.get('review_status')),
             'note':'정확한 제품 구성 전체의 효과를 직접 검증한 연구로 취급하지 않아요.'}))),
        'source_evidence':deepcopy(source.get('evidence',source.get('citation',{'url':source.get('url')}))),
        'adaptations':deepcopy(option['adaptations']),'limitations':deepcopy(option['limits'])+
            ['연구 평균은 개인 예상 성장 또는 달성 기준이 아니에요.'],
        'research_chart':chart_for(source,option['arm']),
        'during_workout':guidance(),
        'completion':{'session_result':'/v2/workouts/{workout_id}/result',
                      'programme_evaluation':'/v3/programme-instances/{instance_id}/evaluations',
                      'read_order':['performed','differences','limitations','interpretation','next_actions'],
                      'effect_achievement_rate':None}}

def entry_content(source):
    return {'content_version':VERSION,'basis':'product_education_not_training_trial',
        'exercises':[exercise_guide(x['exercise_id']) for x in source['lessons']],
        'target_lift_guides':[exercise_guide(x['target_lift']) for x in source['lessons']],
        'sequence':deepcopy(source['sequence']),'first_load':deepcopy(source['first_load']),
        'research_chart':{'available':False,'reason':'EDUCATION_PATH_NOT_STRENGTH_TRIAL','points':[]},
        'limitations':deepcopy(source['limitations']),
        'actions':{'events':'/v3/entry/learning-sessions/{workout_id}/events',
                   'reload':'/v3/entry/learning-sessions/{workout_id}',
                   'reconcile':'/v3/entry/learning-sessions/{workout_id}/reconcile'},
        'next_step':'가벼운 연습 기록은 1RM·자세 인증이 아니에요. 완료한 원기록의 후보를 직접 선택하고 초급 루틴의 별도 시작 조건을 확인해요.'}

def execution_content(execution, source=None, events=None):
    state=execution['state']
    if execution.get('kind') == 'guided_education_not_training':
        # The instructor-led legacy route has no load_trial or client interrupt event.
        actions=[] if state!='active' else (['rest_end','finish'] if execution.get('active_rest') else ['practice_observation','rest_start','finish'])
        return {'content_version':VERSION,'basis':'legacy_guided_education','state':state,
                'exercise_guides':[], 'available_action_ids':actions,
                'reason_record_target_event_ids':[], 'closed_session_reopen_available':False,
                'authority':'server_revalidates_every_event',
                'event_endpoint':'/v3/entry/practices/{workout_id}/events',
                'guidance':{'lesson':deepcopy(execution.get('lesson')),
                            'safety':deepcopy((source or {}).get('safety',[])),
                            'source_url':(source or {}).get('source_url'),
                            'limitations':['지도자와 함께하는 기존 학습 기록이에요. 첫 중량 시험이나 자동 승급은 제공하지 않아요.'],
                            'actions':{'reload':'/v3/entry/practices/{workout_id}',
                                       'reconcile':'/v3/entry/practices/{workout_id}/reconcile'}}}
    entry=execution.get('kind') == 'self_guided_education_not_training'
    if entry:
        actions=[] if state!='active' else (['rest_end','finish','interrupt'] if execution.get('active_rest') else ['practice_observation','load_trial','rest_start','finish','interrupt'])
        ids=[x['exercise_id'] for x in source.get('lessons',[])] if source else []
    else:
        ids=list(dict.fromkeys(r['exercise_id'] for r in execution.get('sets',[])))
        actions={'active':['change_load','set_result','skip_set','pause','finish','interrupt'],
                 'resting':['rest_adjust','rest_end','pause','finish','interrupt'],
                 'paused':['resume','finish','interrupt']}.get(state,[])
        if state=='active' and not execution.get('next_set_id'):actions=['finish','interrupt']
        if state=='active' and execution.get('next_set_id'):
            current=next((r for r in execution['sets'] if r['id']==execution['next_set_id']),None)
            if current and current.get('selected_weight_kg') is None:actions=[a for a in actions if a!='set_result']
        # Informational actions deliberately do not recommend resumption after a pain report.
        if any(g.get('code')=='PAIN_REPORTED' for g in execution.get('guides',[])):
            actions=[a for a in actions if a not in ('resume','set_result','change_load','skip_set')]
    reason_targets=[e['id'] for e in (events or []) if e.get('type') in ('change_load','set_result','skip_set','finish')] if not entry else []
    if reason_targets:actions.append('reason_record')
    return {'content_version':VERSION,'basis':'product_workflow','state':state,
            'reason_record_target_event_ids':reason_targets,
            'exercise_guides':[exercise_guide(x) for x in ids],
            'available_action_ids':actions,'authority':'server_revalidates_every_event',
            'closed_session_reopen_available':False,
            'event_endpoint':('/v3/entry/learning-sessions/{workout_id}/events' if entry else '/v2/workouts/{workout_id}/events'),
            'guidance':entry_content(source) if entry and source and 'lessons' in source else guidance()}

def session_analysis(execution):
    if execution.get('kind') == 'guided_education_not_training':
        return {'content_version':VERSION,'basis':'user_reported_education','scope':'learning_session',
                'observations_recorded':len(execution.get('observations',[])),
                'candidate_loads':{},
                'interpretation':'지도자와 함께한 동작 연습 기록이에요. 자세 인증이나 첫 중량 평가가 아니에요.',
                'limitations':['새 독립 학습 경로의 중량 시험과 구분해요.'],
                'next_actions':deepcopy(execution.get('next_actions',[])),
                'effect_achievement_rate':None}
    if execution.get('kind') == 'self_guided_education_not_training':
        return {'content_version':VERSION,'basis':'user_reported_education','scope':'learning_session',
                'observations_recorded':len(execution.get('observations',[])),
                'candidate_loads':deepcopy(execution.get('candidate_working_loads',{})),
                'interpretation':'동작과 첫 중량의 자기보고 기록이며, 근력 향상이나 자세 합격을 뜻하지 않아요.',
                'summary':'동작과 첫 중량을 관찰한 자기보고 기록이에요. 근력 향상·자세 합격을 뜻하지 않아요.',
                'limitations':['통증·조절 불확실이 있으면 후보 중량을 다음 훈련에 가져가지 않아요.','입문 완료만으로 초급 훈련을 자동 시작하지 않아요.'],
                'next_actions':deepcopy(execution.get('next_actions',[])),
                'effect_achievement_rate':None}
    rows=execution.get('sets',[])
    recorded=[r for r in rows if r.get('actual') is not None]
    changed=[r['id'] for r in rows if r.get('changes')]
    incomplete=[r['id'] for r in rows if r.get('actual') is None]
    reps_differences=[]
    for r in recorded:
        target=r.get('reps')
        # Repetition ranges and AMRAP are not silently turned into a scalar target.
        if isinstance(target,dict):
            target=target.get('min') if target.get('min') == target.get('max') else None
        if type(target) is int and r['actual']['reps']!=target:
            reps_differences.append({'set_id':r['id'],'target':target,'actual':r['actual']['reps']})
    return {'content_version':VERSION,'basis':'recorded_performance_not_effect','scope':'workout',
            'performed':{'recorded_sets':len(recorded),'planned_sets':len(rows)},
            'differences':{'changed_load_set_ids':changed,'repetition_differences':reps_differences,
                           'unrecorded_set_ids':incomplete},
            'limitations':['미기록은 0회나 실패로 채우지 않아요.','수행량 차이만으로 성장 효과·피로 원인·다음 적정 중량을 판단하지 않아요.',
                           '실제 휴식은 확인된 타이머 구간만 비교해요.'],
            'interpretation':'오늘 기록과 목표의 차이를 확인해요. 이 결과는 개인의 성장률 또는 루틴 효과 평가가 아니에요.',
            'next_actions':[{'id':'review_sets','path':'/v2/workouts/{workout_id}/result'},
                            {'id':'check_next_session','path':'/v3/programme-instances/{instance_id}/next-session',
                             'requires':['closed_current_session','at','server_readiness']}],
            'effect_achievement_rate':None}

def programme_analysis(payload, results):
    series=[]
    for ordinal,execution in enumerate(results,1):
        groups={}
        for row in execution.get('sets',[]):
            g=groups.setdefault(row['exercise_id'],{'recorded_sets':0,'planned_sets':0,'observed_volume_kg_reps':None,'missing_sets':0})
            g['planned_sets']+=1
            actual=row.get('actual')
            if actual is None:g['missing_sets']+=1
            else:
                g['recorded_sets']+=1
                g['observed_volume_kg_reps']=(g['observed_volume_kg_reps'] or 0)+actual['weight_kg']*actual['reps']
        series.append({'session_ordinal':ordinal,'workout_id':payload['history_inputs'][ordinal-1]['workout_id'],
                       'state':execution['state'],'exercises':groups})
    return {'content_version':VERSION,'basis':'recorded_performance_not_causal_effect',
        'scope':'programme','performed':deepcopy(payload['training']),
        'charts':{'sessions':series,'x_axis':'session_ordinal','unit':'kg_repetitions',
                  'missing_value_policy':'gap_not_zero',
                  'interpretation':'기록한 세트의 중량×횟수 합만 표시해요. 누락·종목·세트 수가 다르면 단순 우열 비교를 하지 않아요.',
                  'growth_slope':None},
        'measurement_statuses':[{'exercise_id':x['exercise_id'],'status':x['status'],
            'explanation':{'comparable':'같은 조건이라는 자기보고가 있는 실측 전후 기록의 차이예요.',
              'not_measured':'사후 측정이 없어 변화량을 계산하지 않았어요.',
              'baseline_not_recorded':'시작 실측 기록이 없어 전후 비교하지 않아요.',
              'estimated':'사후 추정값은 실측 변화량으로 비교하지 않아요.',
              'baseline_estimated':'시작 추정값은 실측 변화량으로 비교하지 않아요.',
              'conditions_different':'측정 조건이 달라 변화량 비교를 보류해요.',
              'conditions_unknown':'측정 조건이 확인되지 않아 변화량 비교를 보류해요.'}.get(x['status'],'비교 조건을 확인해 주세요.')}
            for x in payload['lifts']],
        'interpretation':'관찰된 변화는 사실 비교예요. 루틴이 변화를 일으켰다는 인과 결론이나 다음 자동 증량을 제공하지 않아요.',
        'next_actions':[{'id':'review_actuals','path':'/v3/programme-instances/{instance_id}'},
                        {'id':'choose_next_programme','path':'/v3/routines','automatic':False},
                        {'id':'register_optional_post_test','path':'/v2/max-records','required':False,
                         'then':'/v3/programme-instances/{instance_id}/evaluations',
                         'requires':['same_exercise','measurement_kind','measured_at','comparison_conditions','supersedes_id']}],
        'limitations':['중단 회차와 미기록 세트를 구분해요.','자기보고된 동일 조건은 독립적으로 검증된 측정 표준화가 아니에요.',
                       '연구 집단의 결과를 개인 기록에 대한 목표선으로 사용하지 않아요.'],
        'effect_achievement_rate':None}

