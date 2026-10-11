"""Build one atomic, idempotent private evidence import. Never publish a routine."""
import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

FILES = ('oa_candidates_v2', 'evidence_audit', 'protocol_audit', 'review_queue', 'release_gate')

def literal(value):
    if value is None:
        return 'NULL'
    return "'" + str(value).replace("'", "''") + "'"

def json_literal(value):
    return literal(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)) + '::jsonb'

def build_sql(documents, completed_at=None):
    discovery = documents['oa_candidates_v2']
    papers = discovery['papers']
    ids = [p['pmid'] for p in papers]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r'[0-9]+', i) for i in ids):
        raise ValueError('Invalid or duplicate PMID')
    if len(ids) != discovery['selected'] or discovery['requested'] <= 0:
        raise ValueError('Discovery count mismatch')
    packets = {p['pmid']: p for p in documents['protocol_audit']['papers']}
    reviews = {p['pmid']: p for p in documents['review_queue']['papers']}
    gates = {p['pmid']: p for p in documents['release_gate']['papers']}
    if any(set(x) != set(ids) for x in (packets, reviews, gates)):
        raise ValueError('Audit, review and gate must refer to the same batch')
    if any(g.get('protocol_publishable') is not False or g.get('chart_publishable') is not False for g in gates.values()):
        raise ValueError('Use a separate reviewed release process; this importer cannot publish')
    for pmid, packet in packets.items():
        digest = packet.get('source_sha256')
        if not packet.get('error_type') and not re.fullmatch(r'[a-f0-9]{64}', digest or ''):
            raise ValueError('Missing source XML digest')
        if reviews[pmid].get('status') != 'awaiting_human_review':
            raise ValueError('Do not replace signed reviews with batch imports')
    automatic = documents.get('automatic_assessment')
    assessments = {p['pmid']: p for p in automatic['papers']} if automatic else {}
    if automatic:
        if set(assessments) != set(ids):
            raise ValueError('Automatic assessment must match the evidence batch')
        for pmid, item in assessments.items():
            if (item.get('runnable') is not False or item.get('chart_publishable') is not False
                    or item.get('decision') not in ('NOT_RUNNABLE', 'SOURCE_ERROR')
                    or not item.get('reasons') or not item.get('validator_version')
                    or item.get('source_sha256') != packets[pmid].get('source_sha256')):
                raise ValueError('Invalid automatic assessment')
    fingerprint = hashlib.sha256(json.dumps(documents, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    run_id = 'batch-' + fingerprint[:24]
    when = completed_at or dt.datetime.now(dt.timezone.utc).isoformat()
    summary = {k: discovery.get(k) for k in ('retrieved_ids','pool_candidates','title_gate_candidates','selected','requested','complete','audit')}
    summary['release_gate'] = documents['release_gate']
    summary['evidence_audit'] = documents['evidence_audit']
    queries = ['BEGIN;', 'SET LOCAL standard_conforming_strings = on;']
    queries.append('INSERT INTO research_internal.batch_runs (id,completed_at,requested,selected,artifact_sha256,summary) VALUES (' + ','.join([
        literal(run_id), literal(when), str(discovery['requested']), str(len(ids)), literal(fingerprint), json_literal(summary)
    ]) + ') ON CONFLICT (id) DO NOTHING;')
    for p in papers:
        packet, review, gate = packets[p['pmid']], reviews[p['pmid']], gates[p['pmid']]
        queries.append('INSERT INTO research_internal.papers (pmid,pmcid,title,doi,source_url,metadata) VALUES (' + ','.join([
            literal(p['pmid']),literal(p.get('pmcid')),literal(p['title']),literal(p.get('doi')),
            literal(packet.get('source_url') or p.get('full_text_url')),json_literal(p)
        ]) + ') ON CONFLICT (pmid) DO UPDATE SET pmcid=excluded.pmcid,title=excluded.title,doi=excluded.doi,source_url=excluded.source_url,metadata=excluded.metadata;')
        queries.append('INSERT INTO research_internal.protocol_candidates (run_id,pmid,source_sha256,status,evidence,review,gate) VALUES (' + ','.join([
            literal(run_id),literal(p['pmid']),literal(packet.get('source_sha256')),
            literal(('source_fetch_failed' if assessments[p['pmid']]['decision'] == 'SOURCE_ERROR' else 'auto_blocked') if automatic else ('source_fetch_failed' if packet.get('error_type') else 'awaiting_human_review')),
            json_literal(packet),json_literal(review),json_literal(gate)
        ]) + ') ON CONFLICT (run_id,pmid) DO NOTHING;')
    if automatic:
        for pmid, item in assessments.items():
            queries.append('INSERT INTO public.research_assessments (run_id,pmid,payload) VALUES (' + ','.join([
                literal(run_id),literal(pmid),json_literal(item)
            ]) + ') ON CONFLICT (run_id,pmid) DO NOTHING;')
    waiting = 0 if automatic else sum(not p.get('error_type') for p in packets.values())
    queries.append('INSERT INTO public.research_catalog_state (id,last_batch_id,checked_at,requested,candidates,awaiting_review) VALUES (true,' + ','.join([
        literal(run_id),literal(when),str(discovery['requested']),str(len(ids)),str(waiting)
    ]) + ') ON CONFLICT (id) DO UPDATE SET last_batch_id=excluded.last_batch_id,checked_at=excluded.checked_at,requested=excluded.requested,candidates=excluded.candidates,awaiting_review=excluded.awaiting_review WHERE excluded.checked_at >= research_catalog_state.checked_at;')
    queries.append('COMMIT;')
    return run_id, '\n'.join(queries) + '\n'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    documents = {name: json.loads((Path(args.directory)/(name+'.json')).read_text()) for name in FILES}
    automatic = Path(args.directory)/'automatic_assessment.json'
    if automatic.exists():
        documents['automatic_assessment'] = json.loads(automatic.read_text())
    run_id, sql = build_sql(documents)
    Path(args.output).write_text(sql)
    print('Prepared private import:', run_id, 'papers:', documents['oa_candidates_v2']['selected'])

if __name__ == '__main__':
    main()
