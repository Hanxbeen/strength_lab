"""Read-only preflight: execution prerequisites are not scientific suitability."""
from research_engine.core import digest,InvalidProgramme
from research_engine.programme_dispatch import make_instance,exercises
from research_engine.programme_schedule import policy
from research_engine.programme_schedule import selected,earliest
from research_engine.workout import timestamp

CONTRACT='programme-readiness-v1'

def required_fields(source,arm):
    engine=source['adapter_version']
    profile=(['body_mass_kg','sex','age','training_months','lifts_weekly_last_6_months','healthy']
             if engine=='helms-2018-v1' else ['age','independent_sbd'])
    setup=['mode','accept_scope_limits','rest_seconds','equipment_step_kg']
    if engine!='helms-2018-v1':setup+=['accept_adaptations','between_exercise_rest_seconds']
    if engine=='sbd-template-v1':setup+=['exercise_mapping']
    if engine=='novice-sbd-choice-v1':setup+=['adaptation_id']
    if engine=='metd-2021-v1':profile+=['training_years','powerlifting_years','rpe_training_years']
    if not (engine=='metd-2021-v1' and arm=='AMRAP'):setup+=['warmup']
    return [('profile',f) for f in profile]+[('setup',f) for f in setup]

def preview(source,request,records,internal_access):
    missing=[{'field':group+'.'+field,'action':'provide_input'} for group,field in required_fields(source,request['arm'])
             if request[group].get(field) is None]
    refs=request['max_record_ids'];chosen=[]
    optional_maxes=source['adapter_version']=='novice-sbd-choice-v1'
    expected=tuple(refs) if optional_maxes else exercises(source)
    for eid in expected:
        r=next((r for r in records if r['id']==refs.get(eid) and r['exercise_id']==eid),None)
        if r is None:missing.append({'field':'max_record_ids.'+eid,'action':
            'register_or_select_max_reference' if source['adapter_version']=='novice-sbd-choice-v1' else 'register_or_select_measured_max'})
        else:chosen.append(r)
    code=None;status='needs_input' if missing else 'ready';instance=None
    if not missing:
        try:
            if (not set(refs)<=set(exercises(source)) if optional_maxes else set(refs)!=set(expected)):
                raise InvalidProgramme('MAX_REFERENCES_REQUIRED')
            instance=make_instance(source,request['arm'],request['profile'],chosen,request['setup'],request['created_at'])
        except InvalidProgramme as error:
            code=str(error)
            status='outside_supported_scope' if any(s in code for s in ('OUTSIDE_STUDY_SCOPE','EXPERIENCE_SCOPE','HEALTH_SCOPE','EXPERIENCED_ADULT')) else 'invalid_input'
        except (ValueError,TypeError,KeyError,AttributeError):status='invalid_input';code='INVALID_INPUT'
    engine=source['adapter_version'];arm=request['arm']
    daily_loads=(engine=='helms-2018-v1' and arm=='RPEG') or (engine=='metd-2021-v1' and arm in ('MAX','MAX_BOFF'))
    actions=sorted({m['action'] for m in missing})
    if code:actions+=['review_scope_limits' if status=='outside_supported_scope' else 'correct_input']
    if status=='ready':actions+=['create_internal_instance'] if internal_access else ['view_research_only']
    message={'needs_input':'시작 전에 필요한 정보를 확인해 주세요.',
        'invalid_input':'입력값을 확인해 주세요.',
        'outside_supported_scope':'현재 구현이 지원하는 연구 재현 범위와 달라요. 위험하거나 효과가 없다는 판정은 아니에요.',
        'ready':'내부 실행에 필요한 입력이 갖춰졌어요. 개인에게 적합한 프로그램이라는 판정은 아니에요.' if internal_access else
                '입력은 갖춰졌지만 아직 일반 사용자에게 공개하지 않은 연구 구성이에요.'}[status]
    return {'contract_version':CONTRACT,'source_id':source['id'],'source_version':digest(source),'arm':arm,
        'message':message,
        'input_status':status,'missing_inputs':missing,'blocking_code':code,
        'access_status':'internal_preview_allowed' if internal_access else 'not_released',
        'can_create_instance':status=='ready' and internal_access,
        'recommendation_status':'not_assessed','scientific_approval':False,
        'decision_basis':'existing_adapter_validation_not_clinical_or_effectiveness_assessment',
        'next_actions':actions,'schedule_policy':policy(source),
        'session_start_inputs':['initial_loads_kg_for_session_exercises'] if engine=='novice-sbd-choice-v1' else
                               ['initial_rpe_loads_kg_for_session_exercises'] if daily_loads else [],
        'adaptations':source.get('adaptations',[]) if instance is None else instance.get('adaptations',[]),
        'not_assessed':['individual_effectiveness','current_pain_or_readiness','equipment_availability','personal_calendar_fit','long_gap_reentry'],
        'revalidation_required_at_create':True,'persisted':False}

def next_session(instance,history,evaluations,at):
    now=timestamp(at);schedule=selected(instance['source'],instance.get('schedule_policy'))
    result={'contract_version':CONTRACT,'programme_version':instance['programme_version'],
        'schedule_policy':schedule,'checked_at':at,'basis':'schedule_policy_only',
        'scientific_approval':False,'automatic_load_adjustment':None,
        'not_assessed':['current_pain_or_readiness','long_gap_reentry'],'revalidation_required_at_start':True}
    if evaluations:return {**result,'state':'programme_closed','next_actions':['review_evaluation','choose_next_programme'],'next_session':None}
    opened=next((h for h in history if h['execution']['state'] not in ('completed','stopped')),None)
    if opened:return {**result,'state':'workout_open','workout_id':opened['workout_id'],
                      'next_actions':['return_to_workout'],'next_session':None}
    if len(history)>=len(schedule['sessions']):
        return {**result,'state':'awaiting_evaluation','next_actions':['evaluate_programme'],'next_session':None}
    target=schedule['sessions'][len(history)]
    if instance['source'].get('adapter_version')=='novice-sbd-choice-v1':
        from research_engine.novice import session_inputs
        source_session=instance['source']['protocol']['sessions'][len(history)]
        result['session_inputs']=session_inputs(instance,source_session['exercises'],history)
    available=timestamp(instance['created_at'])
    elapsed=None
    if history:
        first,last=history[0],history[-1]
        available=earliest(schedule,target['week'],target['day'],first['snapshot']['started_at'],
                           last['snapshot']['started_at'],last['events'][-1]['at'])
        elapsed=(now-timestamp(last['snapshot']['started_at'])).total_seconds()/86400
    state='schedule_available' if now>=available else 'waiting_for_schedule'
    return {**result,'state':state,'next_session':target,'earliest_start_at':available.isoformat(),
            'days_since_previous_start':elapsed,'next_actions':['review_session_inputs'] if now>=available else ['wait_or_review_plan'],
            'missed_work_automatically_carried':False}
