"""Version-pinned product availability; independent from research approval and auth."""
import copy
from fastapi import HTTPException
from research_engine.core import digest

VERSION = 'explicit-source-selection-20261018-v1'
# Changing a source hash requires a new product-scope review.
RELEASES = {
 'petrizzo2018-four-lift-2d-v1': ('cb4fa8fcaa9e5417c72fb7c4a87bed4868f725c5d1003962745ffb1e966035aa','foundation'),
 'petrizzo2018-four-lift-3d-v1': ('2ffb984866484e669cf39fa669cec0b23fd03d024863140bd3d01af06edd47c9','foundation'),
 '10.3389/fphys.2018.00247': ('9d6b5123ca6b04e524d44b95c7e81a48838de4354036c1cd889825a7e8ba32e0','trained'),
 'metd2021-sbd-v1': ('a8bfc16b0837b9a2da1db853951231b4ed29bf1c414693fb49fee1f9b09550e6','experienced'),
}

def availability(source, internal=False):
    release=RELEASES.get(source['id'])
    public=bool(release and release[0]==digest(source))
    return dict(policy_version=VERSION,source_version=digest(source),
        access='explicit_selection' if public else 'internal_preview' if internal else 'not_released',
        can_request_start=public or internal,public_selection=public,
        experience_context=release[1] if public else 'unreviewed_adaptation',
        classification_basis='navigation_not_personal_suitability',
        scientific_approval=False,independent_expert_review=False,
        reason=None if public or internal else 'PRODUCT_ADAPTATION_NOT_RELEASED',
        review_reference='docs/coaching-specs/22_EXPLICIT_SELECTION_RELEASE.md')

def extra_fields(source):
    if source['adapter_version']=='metd-2021-v1':
        return ['sex','raw_powerlifting','daily_max_training_last_12_weeks']
    return []

def scope_issues(source, profile):
    issues=[]
    if source['adapter_version']=='metd-2021-v1':
        expected={'sex':'male','raw_powerlifting':True,'daily_max_training_last_12_weeks':False}
        for key,value in expected.items():
            if key not in profile or profile[key] is None:
                issues.append(dict(field='profile.'+key,code='INPUT_REQUIRED'))
            elif type(profile[key]) is not type(value) or profile[key]!=value:
                issues.append(dict(field='profile.'+key,code='OUTSIDE_PRODUCT_SCOPE'))
    return issues

def authorize(source, profile, internal=False):
    decision=availability(source,internal)
    if not decision['can_request_start']:
        raise HTTPException(403,detail='RESEARCH_PREVIEW_NOT_RELEASED')
    # Preserve internal research fixtures; normal selection observes the additional source conditions.
    if not internal:
        issues=scope_issues(source,profile)
        if issues:raise HTTPException(422,detail={'code':'PRODUCT_SCOPE_INPUTS','issues':issues})
    return copy.deepcopy(decision)

def apply_to_readiness(result, source, profile, internal=False):
    decision=availability(source,internal)
    result=copy.deepcopy(result)
    result['availability']=decision
    result['access_status']=decision['access']
    if not internal:
        for issue in scope_issues(source,profile):
            if issue['code']=='INPUT_REQUIRED':
                result['missing_inputs'].append(dict(field=issue['field'],action='provide_input'))
            else:
                result['input_status']='outside_supported_scope'
                result['blocking_code']='PRODUCT_SCOPE_INPUTS'
        if result['missing_inputs'] and result['input_status']!='outside_supported_scope':
            result['input_status']='needs_input'
    result['can_create_instance']=result['input_status']=='ready' and decision['can_request_start']
    if result['can_create_instance']:
        result['next_actions']=['select_and_create_programme']
        result['message']='입력이 준비됐어요. 구성과 적용 조건을 확인하고 선택할 수 있어요.'
    elif result['input_status']=='needs_input':
        result['next_actions']=['provide_input'];result['message']='시작 전에 필요한 정보를 입력해 주세요.'
    elif result['input_status']=='outside_supported_scope':
        result['next_actions']=['review_scope_limits'];result['message']='현재 제공 조건과 달라요. 다른 구성을 확인해 주세요.'
    elif not decision['can_request_start']:
        result['next_actions']=['choose_available_programme'];result['message']='아직 제공하지 않는 조정안이에요.'
    return result
