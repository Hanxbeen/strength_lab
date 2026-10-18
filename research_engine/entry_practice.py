"""Guided movement learning, not an SBD prescription or technique certificate."""
import copy
from .core import digest, number
from .workout import require, timestamp

POLICY='entry-practice-v1'
SOURCE_URL='https://www.nsca.com/education/articles/ptq/teaching-resistance-training-movement-patterns/'
LESSONS=[
    {'id':'squat-pattern','lift':'squat','title':'앉았다 일어나는 동작 배우기',
     'exercise_id':'touch_and_go_box_squat','equipment':['stable_box_or_bench'],
     'source_locator':'Figure 1 A-B',
     'cues':['안정된 박스 앞에서 발바닥을 바닥에 둬요.','엉덩이를 박스에 가볍게 닿게 한 뒤 일어나요.']},
    {'id':'push-pattern','lift':'bench_press','title':'밀어내는 동작 배우기',
     'exercise_id':'elevated_push_up','equipment':['stable_elevated_support'],
     'source_locator':'Figure 3 A-B',
     'cues':['지도자와 함께 움직이지 않는 지지대 높이와 손 위치를 정해요.','몸을 지지대 쪽으로 내리고 밀어내는 동작을 배워요.']},
    {'id':'hinge-pattern','lift':'deadlift','title':'엉덩이를 뒤로 보내는 동작 배우기',
     'exercise_id':'wall_hip_hinge','equipment':['clear_wall_space'],
     'source_locator':'Figure 2 A-B',
     'cues':['벽 앞에 서서 무릎을 살짝 풀어요.','엉덩이를 뒤로 보내 벽을 가볍게 터치하고 돌아와요.']},
]

def catalogue():
    definition={'id':POLICY,'kind':'guided_education_not_training',
        'scientific_approval':False,'evidence_type':'professional_instruction_not_intervention_trial',
        'source_url':SOURCE_URL,'lessons':copy.deepcopy(LESSONS),
        'dose':{'sets':None,'reps':None,'load_kg':None,'rest_seconds':None},
        'dose_reason':'교육 자료는 이 앱의 보편적인 훈련량을 정하지 않아요.',
        'requirements':['adult','in_person_instructor','equipment_checked','no_current_pain'],
        'safety':['지도자가 먼저 준비 자세와 동작을 보여주고 수행을 확인해요.',
                  '통증이 생기면 연습을 멈추고 도움을 요청해요. 앱은 원인을 판정하지 않아요.'],
        'automatic_mastery':False,'automatic_training_unlock':False,
        'limitations':['혼자 하는 바벨 첫 중량 처방이 아니에요.','원문의 시연 이미지는 재배포하지 않아요.',
                       '지도자가 없는 사용자의 독립 입문 경로는 아직 준비되지 않았어요.'],
        'policy_basis':'Source-informed product learning and recording workflow; not trial replication.'}
    return {**definition,'version':digest(definition)}

def create(lesson_id,version,profile,setup,at):
    definition=catalogue()
    require(version==definition['version'],'ENTRY_VERSION_UNAVAILABLE')
    lesson=next((x for x in definition['lessons'] if x['id']==lesson_id),None)
    require(lesson is not None,'ENTRY_LESSON_UNKNOWN');timestamp(at)
    require(number(profile.get('age'),18,100),'ENTRY_ADULT_SCOPE')
    require(profile.get('current_pain') is False,'ENTRY_PAIN_CHECK_REQUIRED')
    require(setup.get('in_person_instructor') is True,'ENTRY_INSTRUCTOR_REQUIRED')
    require(setup.get('equipment_checked') is True,'ENTRY_EQUIPMENT_CHECK_REQUIRED')
    return dict(policy_version=POLICY,programme_id=POLICY,programme_version=version,
        source=definition,lesson=copy.deepcopy(lesson),profile=copy.deepcopy(profile),
        setup=copy.deepcopy(setup),started_at=at)

def replay(snapshot,events):
    require(snapshot.get('policy_version')==POLICY,'ENTRY_POLICY_UNSUPPORTED')
    require(len(events)<=2000,'EVENT_LIMIT')
    state='active';observations=[];rests=[];rest=None;seen={};last=timestamp(snapshot['started_at'])
    help_required=False;termination=None
    for event in events:
        require(isinstance(event,dict),'INVALID_EVENT')
        eid=event.get('id');require(isinstance(eid,str) and 0<len(eid)<=100,'EVENT_ID_REQUIRED')
        if eid in seen:
            require(seen[eid]==digest(event),'EVENT_ID_CONFLICT');continue
        seen[eid]=digest(event);at=timestamp(event.get('at'))
        require(at>=last,'EVENT_TIME_ORDER');last=at
        require(state=='active','ENTRY_PRACTICE_CLOSED')
        kind=event.get('type')
        if kind=='practice_observation':
            require(rest is None,'ENTRY_REST_OPEN')
            outcome=event.get('outcome')
            require(outcome in ('tried','not_tried','needs_help','pain'),'ENTRY_OUTCOME_REQUIRED')
            reps=event.get('reps')
            require(reps is None or type(reps) is int and 0<=reps<=1000,'INVALID_REPS')
            require(outcome=='tried' or reps is None,'ENTRY_NONPERFORMANCE_REPS')
            require('weight_kg' not in event and 'load' not in event,'ENTRY_NO_LOAD_PRESCRIPTION')
            observations.append({'event_id':eid,'at':event['at'],'outcome':outcome,'reps':reps,
                'basis':'user_report','technique_verified':False})
            if outcome in ('needs_help','pain'):
                help_required=True;state='stopped';termination=copy.deepcopy(event)
        elif kind=='rest_start':
            require(rest is None,'ENTRY_REST_ALREADY_OPEN')
            rest={'started_at':event['at'],'planned_seconds':None}
        elif kind=='rest_end':
            require(rest is not None,'ENTRY_REST_NOT_OPEN')
            rests.append({**rest,'ended_at':event['at'],
                'elapsed_seconds':(at-timestamp(rest['started_at'])).total_seconds(),
                'measurement_status':'timer_confirmed'})
            rest=None
        elif kind in ('finish','interrupt'):
            if kind=='finish':
                require(event.get('outcome') in ('completed','stopped'),'ENTRY_FINISH_OUTCOME_REQUIRED')
                require(event['outcome']!='completed' or any(o['outcome']=='tried' for o in observations),
                        'ENTRY_NO_PRACTICE_RECORDED')
                state=event['outcome']
            else:
                require(event.get('reason')=='inactivity','ENTRY_INTERRUPT_UNSUPPORTED')
                state='stopped'
            termination=copy.deepcopy(event)
            if rest:
                rests.append({**rest,'ended_at':event['at'],'elapsed_seconds':None,
                              'measurement_status':'unconfirmed'})
                rest=None
        else:require(False,'ENTRY_EVENT_UNSUPPORTED')
    return {'kind':'guided_education_not_training','policy_version':POLICY,
        'programme_id':snapshot['programme_id'],'programme_version':snapshot['programme_version'],
        'lesson':copy.deepcopy(snapshot['lesson']),'state':state,'revision':len(seen),
        'observations':observations,'rests':rests,'active_rest':rest,'termination':termination,
        'sets':[],'max_records':[],'assessment':None,'technique_verified':False,
        'training_unlocked':False,'next_actions':['ask_instructor_for_help'] if help_required else
            ['review_learning_or_repeat'] if state in ('completed','stopped') else ['record_practice','rest','stop'],
        'training_transition':{'automatic':False,'requirements':['lift_specific_instruction',
            'independent_execution_check','known_working_load','programme_scope_check']},
        'research_growth_comparison':None}
