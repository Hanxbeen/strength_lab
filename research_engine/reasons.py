"""Versioned self-report, never a diagnosis or inferred failure label."""
from .workout import require

CODES = {'effort_insufficient','pain_discomfort','technique','equipment',
         'plan_change','time','effort_available','planned_progression','other'}
STATUSES = {'answered','unknown','declined','not_asked'}

def validate(value):
    require(isinstance(value,dict) and value.get('schema_version') == 1, 'REASON_SCHEMA')
    codes=value.get('reason_codes')
    require(isinstance(codes,list) and all(isinstance(c,str) and c in CODES for c in codes)
            and len(codes)==len(set(codes)), 'REASON_CODES')
    status=value.get('response_status')
    require(isinstance(status,str) and status in STATUSES, 'REASON_STATUS')
    require(bool(codes) == (status == 'answered'), 'REASON_RESPONSE_CONFLICT')
    note=value.get('note')
    require(note is None or (isinstance(note,str) and len(note)<=500), 'REASON_NOTE')
    return {'schema_version':1,'reason_codes':list(codes),'response_status':status,
            'reported_by':'user','note':note}
