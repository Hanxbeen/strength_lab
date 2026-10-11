"""Export verified v2 definitions, not repeated materialized sessions or raw articles."""
import argparse
import json
from pathlib import Path
from .core import compile_programme, digest, ENGINE_VERSION, InvalidProgramme
from scripts.research_store import literal, json_literal

def build_sql(catalog):
    if catalog.get('failures') or not catalog.get('programmes'): raise InvalidProgramme('Incomplete source batch')
    records=[]
    for p in catalog['programmes']:
        rebuilt=compile_programme(p['definition'])
        if rebuilt != p: raise InvalidProgramme('Compiler output mismatch')
        records.append({k:p[k] for k in ('schema_version','engine_version','programme_id','programme_version','definition','session_count','working_set_count','evidence_status','scientific_approval','client_contract','chart_publishable','readiness','required_setup','explanation')})
    edition=digest(records)
    sql=['BEGIN;','SET LOCAL standard_conforming_strings=on;']
    for row in records:
        sql.append('INSERT INTO public.source_programme_versions (id,version,payload) VALUES ('+','.join([literal(row['programme_id']),literal(row['programme_version']),json_literal(row)])+') ON CONFLICT (id,version) DO NOTHING;')
    index=[{'id':r['programme_id'],'version':r['programme_version']} for r in records]
    sql.append('INSERT INTO public.source_programme_editions (id,members) VALUES ('+literal(edition)+','+json_literal(index)+') ON CONFLICT (id) DO NOTHING;')
    sql.append('INSERT INTO public.source_programme_state (id,edition_id) VALUES (true,'+literal(edition)+') ON CONFLICT (id) DO UPDATE SET edition_id=excluded.edition_id;')
    sql.append('COMMIT;')
    return '\n'.join(sql)+'\n'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
    sql=build_sql(json.loads(Path(args.input).read_text()))
    Path(args.output).write_text(sql)
    print('Prepared atomic v2 definition import')

if __name__=='__main__':main()
