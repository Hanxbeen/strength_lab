"""Deterministic source/runner compatibility checks, not scientific peer review.

Never turn keyword hits into an executable prescription. The current runner has
one fixed reps/rest value per exercise and no week/arm/load/cluster model. Report
these concrete failures automatically instead of an indefinite human queue.
"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = 'runner-compatibility-v1'
MESSAGES = {
    'SOURCE_UNAVAILABLE': '논문 원문을 불러오지 못했어요.',
    'SOURCE_CHANGED': '원문이 바뀌어 운동 구성을 다시 추출해야 해요.',
    'SOURCE_MISMATCH': '논문 식별자와 원문이 일치하지 않아요.',
    'NOT_TRAINING_PROGRAM': '장기 운동 루틴이 아닌 측정 조건을 비교한 연구예요.',
    'UNSUPPORTED_EXERCISES': '이 연구에 포함된 보조 운동을 아직 지원하지 않아요.',
    'VARIABLE_SET_PRESCRIPTION': '세트별로 다른 횟수와 중량을 아직 실행기에 반영할 수 없어요.',
    'CLUSTER_REST': '세트 안에서 나누어 쉬는 운동 방식을 아직 지원하지 않아요.',
    'MISSING_PRESCRIPTION': '주차·운동·중량·휴식의 전체 구성을 원문에서 확정하지 못했어요.',
}

def assess(packet, raw=None):
    pmid = packet['pmid']
    if not re.fullmatch(r'[0-9]+', pmid):
        raise ValueError('Invalid PMID')
    pmcid = packet.get('pmcid') or ''
    result = {
        'pmid': pmid, 'pmcid': pmcid, 'title': packet.get('title') or '논문 ' + pmid,
        'source_url': 'https://pubmed.ncbi.nlm.nih.gov/' + pmid + '/',
        'source_sha256': packet.get('source_sha256'),
        'validator_version': VERSION, 'decision': 'NOT_RUNNABLE',
        'runnable': False, 'chart_publishable': False, 'reasons': [],
    }
    codes = []
    if raw is None or packet.get('error_type'):
        codes.append('SOURCE_UNAVAILABLE')
    elif hashlib.sha256(raw).hexdigest() != packet.get('source_sha256'):
        codes.append('SOURCE_CHANGED')
    else:
        root = ET.fromstring(raw)
        identifiers = [n.text or '' for n in root.findall('.//article-meta/article-id')]
        if pmid not in identifiers or not any(v.removeprefix('PMC') == pmcid.removeprefix('PMC') for v in identifiers):
            codes.append('SOURCE_MISMATCH')
        else:
            # Only protocol tables, never outcome or hypothetical examples.
            tables = [t for t in packet.get('tables', [])
                      if re.search(r'(?:training (?:program|protocol)|resistance training protocol)', t['caption'], re.I)
                      and not re.search(r'hypothetical|changes in|response to', t['caption'], re.I)]
            cells = ' '.join(c for t in tables for row in t['rows'] for c in row)
            title = packet.get('title', '').lower()
            missing = packet.get('missing_evidence_fields', [])
            if not tables and 'tempo' in title and 'duration' in missing and 'frequency' in missing:
                codes.append('NOT_TRAINING_PROGRAM')
            else:
                if re.search(r'trap.bar|split squat|hip.thrust', cells, re.I):
                    codes.append('UNSUPPORTED_EXERCISES')
                if re.search(r'Set 1.*Set 2', cells, re.I):
                    codes.append('VARIABLE_SET_PRESCRIPTION')
                if re.search(r'Cluster rest', cells, re.I):
                    codes.append('CLUSTER_REST')
                # This is a real remaining extraction boundary, not a human approval requirement.
                codes.append('MISSING_PRESCRIPTION')
    if codes[0].startswith('SOURCE_'):
        result['decision'] = 'SOURCE_ERROR'
    result['reasons'] = [{'code': code, 'message': MESSAGES[code]} for code in codes]
    return result

def build(audit, source_dir):
    items = []
    for packet in audit['papers']:
        pmcid = packet.get('pmcid', '')
        if pmcid and not re.fullmatch(r'PMC[0-9]+', pmcid):
            raise ValueError('Invalid PMCID')
        path = Path(source_dir) / (pmcid + '.xml')
        raw = path.read_bytes() if pmcid and path.exists() else None
        items.append(assess(packet, raw))
    return {'schema_version': 1, 'validator_version': VERSION, 'papers': items,
            'automatically_checked': len(items), 'runnable_count': 0,
            'scope': 'Source integrity and current app compatibility. Not scientific validity or automatic prescription extraction.'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    args = parser.parse_args()
    folder = Path(args.directory)
    value = build(json.loads((folder/'protocol_audit.json').read_text()), folder/'sources')
    (folder/'automatic_assessment.json').write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    for item in value['papers']:
        print(item['pmid'], item['decision'], ','.join(r['code'] for r in item['reasons']))

if __name__ == '__main__':
    main()
