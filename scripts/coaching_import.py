"""Atomic evidence import. Does not change the existing source catalogue or approve research."""
import argparse
import json
from pathlib import Path
from research_engine.core import digest
from research_engine.coaching import validate_source
from scripts.research_store import literal,json_literal

def build(discovery,source):
    validate_source(source)
    if discovery.get('schema_version')!=1:raise ValueError('Unsupported discovery')
    records=discovery['reports']
    if len(records)!=discovery['unique_reports'] or len({r['id'] for r in records})!=len(records):raise ValueError('Count mismatch')
    sql=['BEGIN;','SET LOCAL standard_conforming_strings=on;']
    run={k:v for k,v in discovery.items() if k!='reports'}
    sql.append('INSERT INTO research_internal.coaching_search_runs(id,payload) VALUES('+literal(digest(discovery))+','+json_literal(run)+') ON CONFLICT DO NOTHING;')
    for r in records:
        if r['review_status']!='candidate' or r['scientific_approval'] is not False:raise ValueError('Collector cannot approve')
        sql.append('INSERT INTO research_internal.coaching_report_versions(report_id,version,payload) VALUES('+','.join([literal(r['id']),literal(digest(r)),json_literal(r)])+') ON CONFLICT DO NOTHING;')
    sql.append('INSERT INTO public.coaching_source_versions(source_id,version,payload) VALUES('+','.join([literal(source['id']),literal(digest(source)),json_literal(source)])+') ON CONFLICT DO NOTHING;')
    sql.append('COMMIT;')
    return '\n'.join(sql)+'\n'

def build_foundations(foundations):
    if foundations.get('failures'):raise ValueError('Incomplete identity verification')
    sql=['BEGIN;','SET LOCAL standard_conforming_strings=on;']
    for report in foundations['reports']:
        if report['scientific_approval'] is not False:raise ValueError('Cannot approve in importer')
        key=(report.get('doi') or ('MED:'+report['pmid'])).lower()
        row={**report,'id':key,'review_status':'candidate','identity_verification':'metadata_verified'}
        sql.append('INSERT INTO research_internal.coaching_report_versions(report_id,version,payload) VALUES('+','.join([literal(key),literal(digest(row)),json_literal(row)])+') ON CONFLICT DO NOTHING;')
    sql.append('COMMIT;')
    return '\n'.join(sql)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--discovery',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    a=p.parse_args()
    Path(a.output).write_text(build(json.loads(Path(a.discovery).read_text()),json.loads(Path(a.source).read_text())))
    print('Atomic candidate and source import prepared; no approval or release changes')
