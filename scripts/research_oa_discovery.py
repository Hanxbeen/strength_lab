#!/usr/bin/env python3
"""Discover accessible primary SBD studies before selecting 20. No auto-prescriptions."""
import argparse
import datetime as dt
import json
import re
import time
from pathlib import Path
from scripts.research_batch import discover
from scripts.research_enrich import enrich

EXCLUDE=re.compile(r'acute.effects|single.session|single.bout|post.activation|systematic.review|meta.analysis|cross.sectional|case.report',re.I)

def eligible(p):
    text=p.get('title','')+' '+p.get('abstract','')
    return not EXCLUDE.search(text) and bool(re.search(r'squat|bench.press|deadlift|powerlift',text,re.I))

def run(limit,pool):
    # Larger pool is essential: don't truncate to 20 before checking access.
    candidates,total=discover(pool)
    selected=[]; reviewed=[]
    for index,p in enumerate(candidates,1):
        if not eligible(p):continue
        try:row=enrich(p)
        except Exception as exc:row=dict(p,full_text_status='lookup_error',screening_flags=[type(exc).__name__],runnable=False,chart_publishable=False,relation_publishable=False)
        reviewed.append({'pmid':p['pmid'],'full_text_status':row['full_text_status']})
        if row['full_text_status']=='open_xml_accessible':
            selected.append(row)
            print(f'OPEN {len(selected):02}/{limit} {p["pmid"]} {p["title"][:70]}',flush=True)
        if len(selected)>=limit:break
        if index%10==0:print(f'Screened {index}/{len(candidates)}; open {len(selected)}',flush=True)
        time.sleep(.25)
    return {'schema_version':1,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'requested':limit,'retrieved_ids':total,'pool_candidates':len(candidates),'checked':len(reviewed),'selected':len(selected),'complete':len(selected)>=limit,'notes':'Only verified accessible XML, NOT verified study protocols or numerical outcomes. Human review required.','screening_log':reviewed,'papers':selected}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=20);ap.add_argument('--pool',type=int,default=100);ap.add_argument('--output',default='data/research/oa_candidates.json');args=ap.parse_args()
    if not 1<=args.limit<=100 or not args.limit<=args.pool<=100:ap.error('require 1 <= limit <= pool <= 100')
    result=run(args.limit,args.pool)
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f"RESULT selected={result['selected']}/{args.limit} checked={result['checked']} complete={result['complete']}",flush=True)
if __name__=='__main__':main()
