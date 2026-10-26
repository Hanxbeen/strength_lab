"""Explicit finite schedule contracts. No inferred rescheduling or catch-up load."""
import copy
from datetime import timedelta
from .workout import require,timestamp

VERSION='programme-schedule-v1'
SUPPORTED=('helms-2018-v1','sbd-template-v1','per-source-labels-v1','metd-2021-v1','novice-sbd-choice-v1','petrizzo-2018-v1')

def policy(source):
    require(source.get('adapter_version') in SUPPORTED,'UNSUPPORTED_SCHEDULE_ADAPTER')
    protocol=source['protocol']
    if 'sessions' in protocol:
        sessions=[{'week':s['week'],'day':s['day']} for s in protocol['sessions']]
    else:
        sessions=[{'week':wi,'day':di} for wi,w in enumerate(protocol['weeks'],1)
                  for di,d in enumerate(w['days'],1) if d.get('kind')!='post_test']
    require(all(s['day'] in (1,2,3) for s in sessions),'UNSUPPORTED_SCHEDULE_DAYS')
    return {'version':VERSION,'sessions':sessions,'day_offsets':{'1':0,'2':2,'3':4},
        'minimum_start_interval_seconds':172800,'interval_basis':'product_policy_not_research_safety_threshold',
        'sequence_basis':'source_session_order','delay_policy':'allow_delay_preserve_order',
        'missed_session_policy':'no_automatic_skip_or_catch_up','long_gap_policy':'no_validated_reentry_load',
        'calendar_basis':'relative_offsets_not_enforced_weekday_names'}

def selected(source,frozen=None):
    expected=policy(source)
    require(frozen is None or frozen==expected,'SCHEDULE_POLICY_MISMATCH')
    return copy.deepcopy(expected if frozen is None else frozen)

def index(schedule,week,day):
    position=next((i for i,s in enumerate(schedule['sessions']) if s=={'week':week,'day':day}),None)
    require(position is not None,'INVALID_SESSION')
    return position

def earliest(schedule,week,day,first_started_at,last_started_at,last_event_at):
    nominal=(week-1)*7+schedule['day_offsets'][str(day)]
    return max(timestamp(first_started_at)+timedelta(days=nominal),
               timestamp(last_started_at)+timedelta(seconds=schedule['minimum_start_interval_seconds']),
               timestamp(last_event_at))
