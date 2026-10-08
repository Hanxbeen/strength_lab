#!/usr/bin/env python3
"""Fail-closed evidence publication gate. Source-backed signoff is mandatory."""
import argparse
import json
from pathlib import Path

REQUIRED_PROTOCOL=('study_design','population','arms','duration','frequency','session_exercises','sets_reps','intensity','rest','progression','accessories','week_by_week')
REQUIRED_CHART=('group_outcomes','uncertainty_type','outcome_units')

def validate(item,kind):
    errors=[]
    if item.get('status')!='approved':errors.append('status_not_approved')
    if not item.get('reviewer_id'):errors.append('missing_reviewer_id')
    if not item.get('reviewed_at'):errors.append('missing_review_timestamp')
    if not item.get('source_sha256') or len(item['source_sha256'])!=64:errors.append('missing_source_digest')
    if not item.get('source_url'):errors.append('missing_source_url')
    fields=item.get('fields',{})
    required=REQUIRED_PROTOCOL if kind=='protocol' else REQUIRED_CHART
    for field in required:
        evidence=fields.get(field,{})
        if evidence.get('status')!='verified':errors.append('unverified_'+field)
        if not evidence.get('source_locators'):errors.append('missing_source_'+field)
    if kind=='protocol' and not item.get('complete_arm_session_matrix'):errors.append('missing_complete_arm_session_matrix')
    if kind=='chart' and not item.get('validated_group_timepoint_mapping'):errors.append('missing_group_timepoint_mapping')
    return errors

def build(queue):
    records=[]
    for p in queue['papers']:
        protocol_errors=validate(p,'protocol')
        chart_errors=validate(p,'chart')
        records.append({'pmid':p['pmid'],'protocol_publishable':not protocol_errors,'chart_publishable':not chart_errors,'protocol_blockers':protocol_errors,'chart_blockers':chart_errors})
    return {'schema_version':1,'papers':records,'protocols_publishable':sum(p['protocol_publishable'] for p in records),'charts_publishable':sum(p['chart_publishable'] for p in records),'policy':'Default deny; human field signoff and source hash required. Approval does not automatically write to production.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='data/research/review_queue.json');ap.add_argument('--output',default='data/research/release_gate.json');a=ap.parse_args()
    result=build(json.loads(Path(a.input).read_text()))
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('RELEASE GATE',result['protocols_publishable'],'protocols',result['charts_publishable'],'charts')
if __name__=='__main__':main()
