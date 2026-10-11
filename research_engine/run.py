"""Bounded non-AI batch: whitelisted sources -> checked definitions -> atomic import."""
import argparse
import json
from pathlib import Path
import urllib.request
from .adapters import SOURCES
from .batch import build
from .export import build_sql
from scripts.research_pipeline import persist

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',required=True)
    parser.add_argument('--offline',action='store_true')
    parser.add_argument('--persist',action='store_true')
    args=parser.parse_args();folder=Path(args.directory);folder.mkdir(parents=True,exist_ok=True)
    sources=folder/'sources';sources.mkdir(exist_ok=True)
    if not args.offline:
        for pmc in SOURCES:
            request=urllib.request.Request('https://www.ebi.ac.uk/europepmc/webservices/rest/'+pmc+'/fullTextXML',headers={'User-Agent':'MugeMuge-source-engine/1.0'})
            with urllib.request.urlopen(request,timeout=30) as response:raw=response.read()
            (sources/(pmc+'.xml')).write_bytes(raw)
    result=build(sources)
    if result['failures']:
        (folder/'failed-batch.json').write_text(json.dumps(result['failures'],ensure_ascii=False,indent=2))
        raise SystemExit('Source batch failed; active database edition was not changed')
    sql=build_sql(result)
    (folder/'catalog-v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    (folder/'import.sql').write_text(sql)
    if args.persist:persist(sql)
    print(json.dumps({'sources':result['source_count'],'programmes':result['programme_count'],'database_written':args.persist}))

if __name__=='__main__':main()
