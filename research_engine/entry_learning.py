"""Self-paced introductory learning and explicit first-load observations."""
import copy
from .core import digest,number
from .workout import require,timestamp
POLICY='entry-learning-v2'
ID='mugemuge-entry-learning-v2'
SBD=('barbell_back_squat','barbell_bench_press','barbell_deadlift')
NSCA='https://www.nsca.com/education/articles/ptq/teaching-resistance-training-movement-patterns/'
NHS='https://www.nhs.uk/live-well/exercise/strength-exercises/'
MANUAL='https://www.nsca.com/contentassets/48a12160221541acbdc048498d77192d/basics_of_strength_and_conditioning_manual.pdf'
def definition():
    lessons=[
        dict(id='squat',exercise_id='sit_to_stand',target_lift=SBD[0],title='의자에서 일어나기',
            equipment=['움직이지 않는 의자','미끄럽지 않은 바닥'],
            steps=['발바닥이 바닥에 닿는 의자 가장자리에 앉아요.','몸을 조금 앞으로 기울이고 다리로 천천히 일어나요.','균형을 잡고 천천히 다시 앉아요.'],
            practice_reps=5,rep_basis='NHS sit-to-stand example; may stop earlier',
            demonstration=dict(url=NHS,section='Sit-to-stand',kind='external_illustrated_instruction'),
            barbell_demonstration='https://www.nsca.com/education/videos/exercise-technique-high-bar-back-squat/'),
        dict(id='push',exercise_id='wall_press_up',target_lift=SBD[1],title='벽 밀기',
            equipment=['움직이지 않는 벽','미끄럽지 않은 바닥'],
            steps=['벽에서 팔 길이 정도 떨어져 서서 가슴 높이에 손을 대요.','몸을 곧게 유지하며 팔꿈치를 굽혀 벽 쪽으로 가까워져요.','천천히 벽을 밀고 돌아와요.'],
            practice_reps=5,rep_basis='Product single practice set; NHS describes 3 sets of 5–10',
            demonstration=dict(url=NHS,section='Wall press-up',kind='external_illustrated_instruction'),
            barbell_demonstration=MANUAL),
        dict(id='hinge',exercise_id='wall_hip_hinge',target_lift=SBD[2],title='엉덩이 뒤로 보내기',
            equipment=['벽 앞의 빈 공간'],
            steps=['벽을 등지고 서서 무릎을 가볍게 풀어요.','엉덩이를 뒤로 보내 벽에 가볍게 닿게 해요.','허리를 억지로 굽히지 않고 편한 범위에서 돌아와요.'],
            practice_reps=5,rep_basis='Product familiarization example, not source training dose',
            demonstration=dict(url=NSCA,section='Figure 2; linked professional teaching material',kind='external_instruction'),
            barbell_demonstration='https://www.nsca.com/education/videos/exercise-technique-deadlift/')]
    return dict(id=ID,adapter_version=POLICY,kind='self_guided_education_not_training',
        review_status='reviewed_product_synthesis',scientific_approval=False,
        title='처음 시작하기 · 동작과 첫 중량',lessons=lessons,
        evidence=[dict(url=NHS,kind='public_health_instruction',role='self-directed low-load movement examples'),
                  dict(url=NSCA,kind='professional_instruction',role='movement learning sequence; self-guided adaptation is a product choice'),
                  dict(url='https://pmc.ncbi.nlm.nih.gov/articles/PMC12965823/',kind='overview_of_reviews',role='starting simply and avoiding required failure; not first-load algorithm validation')],
        sequence=['check_environment','read_and_view','practice','record_control_and_effort','optional_first_load','review_next_step'],
        practice=dict(external_load_kg=0,sets=1,rest_seconds=None,basis='product_introductory_practice_not_strength_dose'),
        first_load=dict(optional=True,reps=5,max_trials_per_lift=3,
            load_choice='user selects an available light training implement; never default a bar to 20 kg',
            required=['lift_instruction_reviewed','equipment_checked','safety_support_ready'],
            success='five controlled easy repetitions reported by user; observation only',
            next='record the candidate or choose lighter; no automatic increase',
            stop='pain, uncertain control or inability to use the lightest available implement: stop and seek qualified help',
            basis='product familiarization workflow; not a validated RM test'),
        automatic_mastery=False,automatic_training_unlock=False,one_rm_required=False,
        limitations=['앱은 자세를 판정하지 않아요. 불확실하면 중량을 들기 전에 도움을 요청해 주세요.',
                     '가벼운 연습 기록은 1RM이나 5RM 측정값이 아니에요.',
                     '시연은 원 제공기관의 페이지에서 열어요. 영상 재생 환경에 따라 접근이 달라질 수 있어요.'])
def validate_source(source):require(source==definition(),'ENTRY_DEFINITION_UNAVAILABLE')
def create(source,version,profile,setup,at):
    validate_source(source);require(digest(source)==version,'ENTRY_VERSION_UNAVAILABLE');timestamp(at)
    require(number(profile.get('age'),18,100),'ENTRY_ADULT_SCOPE')
    require(profile.get('current_pain') is False and profile.get('exercise_restriction') is False,'ENTRY_HEALTH_CHECK_REQUIRED')
    require(setup.get('equipment_checked') is True,'ENTRY_EQUIPMENT_CHECK_REQUIRED')
    require(setup.get('accept_self_report_limits') is True,'ENTRY_LIMITS_REQUIRED')
    return dict(policy_version=POLICY,programme_id=ID,programme_version=version,source=copy.deepcopy(source),
        profile=copy.deepcopy(profile),setup=copy.deepcopy(setup),started_at=at)
def replay(snapshot,events):
    require(snapshot.get('policy_version')==POLICY,'ENTRY_POLICY_UNSUPPORTED')
    require(len(events)<=2000,'EVENT_LIMIT')
    source=snapshot['source'];state='active';observations=[];trials=[];rests=[];rest=None;seen={};termination=None
    last=timestamp(snapshot['started_at']);lessons={x['id']:x for x in source['lessons']}
    for event in events:
        eid=event.get('id');require(isinstance(eid,str) and 0<len(eid)<=100,'EVENT_ID_REQUIRED')
        if eid in seen:
            require(seen[eid]==digest(event),'EVENT_ID_CONFLICT');continue
        seen[eid]=digest(event);at=timestamp(event.get('at'));require(at>=last,'EVENT_TIME_ORDER');last=at
        require(state=='active','ENTRY_PRACTICE_CLOSED');kind=event.get('type')
        if kind in ('practice_observation','load_trial'):
            require(rest is None,'ENTRY_REST_OPEN')
            lid=event.get('lesson_id');require(lid in lessons,'ENTRY_LESSON_UNKNOWN')
            reps=event.get('reps');require(type(reps) is int and 0<=reps<=100,'INVALID_REPS')
            control=event.get('control');effort=event.get('effort');pain=event.get('pain')
            require(control in ('controlled','uncertain','lost') and effort in ('easy','moderate','hard','unknown')
                    and type(pain) is bool,'ENTRY_FEEDBACK_REQUIRED')
            fact=dict(event_id=eid,lesson_id=lid,at=event['at'],reps=reps,control=control,effort=effort,
                pain=pain,basis='user_report',technique_verified=False)
            if kind=='load_trial':
                require(any(o['lesson_id']==lid and o['control']=='controlled' and o['reps']>0 and not o['pain'] for o in observations),'ENTRY_PRACTICE_FIRST')
                require(all(event.get(k) is True for k in ('lift_instruction_reviewed','equipment_checked','safety_support_ready')),'ENTRY_LOAD_SETUP_REQUIRED')
                value=event.get('value');unit=event.get('unit')
                require(number(value,.1,2000) and unit in ('kg','lb'),'INVALID_MASS')
                kg=value*(.45359237 if unit=='lb' else 1)
                require(kg<=2000,'INVALID_MASS')
                require(sum(t['lesson_id']==lid for t in trials)<source['first_load']['max_trials_per_lift'],'ENTRY_TRIAL_LIMIT')
                require(event.get('light_implement_selected') is True,'ENTRY_LIGHT_IMPLEMENT_REQUIRED')
                fact.update(exercise_id=lessons[lid]['target_lift'],weight_kg=kg,original_value=value,original_unit=unit,
                    candidate_only=reps==5 and control=='controlled' and effort=='easy' and not pain)
                trials.append(fact)
            else:
                require(not any(k in event for k in ('weight_kg','value','load')),'ENTRY_PRACTICE_IS_UNLOADED')
                observations.append(fact)
            if pain or control in ('uncertain','lost'):
                state='stopped';termination=copy.deepcopy(event)
        elif kind=='rest_start':
            require(rest is None,'ENTRY_REST_ALREADY_OPEN');rest=dict(started_at=event['at'],planned_seconds=None)
        elif kind=='rest_end':
            require(rest is not None,'ENTRY_REST_NOT_OPEN')
            rests.append(dict(rest,ended_at=event['at'],elapsed_seconds=(at-timestamp(rest['started_at'])).total_seconds(),measurement_status='timer_confirmed'));rest=None
        elif kind in ('finish','interrupt'):
            if kind=='finish':
                outcome=event.get('outcome');require(outcome in ('completed','stopped'),'ENTRY_FINISH_OUTCOME_REQUIRED')
                if outcome=='completed':
                    require(all(any(o['lesson_id']==lid and o['reps']>0 and o['control']=='controlled' for o in observations) for lid in lessons),'ENTRY_LESSONS_INCOMPLETE')
                state=outcome
            else:state='stopped'
            termination=copy.deepcopy(event)
            if rest:
                rests.append(dict(rest,ended_at=event['at'],elapsed_seconds=None,measurement_status='unconfirmed'));rest=None
        else:require(False,'ENTRY_EVENT_UNSUPPORTED')
    candidates={}
    for trial in trials:
        # Later difficult trials invalidate an earlier candidate in this session.
        candidates.pop(trial['exercise_id'],None)
        if trial['candidate_only']:candidates[trial['exercise_id']]=copy.deepcopy(trial)
    help_required=any(x['pain'] or x['control']!='controlled' for x in observations+trials)
    if help_required:candidates={}
    return dict(kind='self_guided_education_not_training',policy_version=POLICY,programme_id=ID,
        programme_version=snapshot['programme_version'],state=state,revision=len(seen),observations=observations,
        load_trials=trials,candidate_working_loads=candidates,rests=rests,active_rest=rest,termination=termination,
        sets=[],max_records=[],technique_verified=False,training_unlocked=False,assessment=None,
        next_actions=['seek_qualified_help'] if help_required else ['review_stopped_session'] if state=='stopped' else ['review_foundation_requirements','confirm_working_loads'] if state=='completed' else ['practice','rest','stop'],
        training_transition=dict(automatic=False,requirements=['independent_sbd_self_report','confirm_current_state','explicit_working_load_selection','programme_scope_check']),
        research_growth_comparison=None)
