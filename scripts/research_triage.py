#!/usr/bin/env python3
"""Conservative access/eligibility triage: no inferred prescriptions or outcome numbers."""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

API='https://www.ebi.ac.uk/europepmc/webservices/rest/search'

def lookup(pmid):
    url=API+'?'+urllib.parse.urlencode({'query':'EXT_ID:'+pmid+' AND SRC:MED','format':'json','resultType':'core','pageSize':1})
    req=urllib.request.Request(url,headers={'User-Agent':'StrengthLabResearch/0.1'})
    with urllib.request.urlopen(req,timeout=25) as res:
        hits=json.load(res).get('resultList',{}).get('result',[])
    return hits[0] if hits else {}

def classify(paper,remote):
    abstract=paper.get('abstract',''); title=paper.get('title',''); content=(title+' '+abstract).lower()
    acute=bool(re.search(r'acute.effects|single.session|single.bout|immediate.effect|post.activation|one.session',content))
    review=bool(re.search(r'meta.analysis|systematic.review',content))
    duration=bool(re.search(r'\b\d+[- ]?week|\b\d+[- ]?month',content))
    sbd=bool(re.search(r'squat|bench.press|deadlift|powerlift',content))
    return {'pmid':paper['pmid'],'title':title,'doi':paper.get('doi'), 'full_text_access':'open_full_text_reported' if remote.get('isOpenAccess')=='Y' and remote.get('pmcid') else 'not_confirmed_open', 'pmcid':remote.get('pmcid'), 'full_text_url':('https://europepmc.org/articles/'+remote['pmcid']) if remote.get('pmcid') else None,'study_type_hint':'review' if review else 'acute' if acute else 'longitudinal_possible' if duration else 'unclear','sbd_mentioned':sbd,'runnable':'blocked_pending_full_text_and_manual_validation','chart':'blocked_pending_numeric_source_validation','relationships':'not_assessed','review_reason':'Source-level exercise schedule, arms, progression and results must be verified against full text and supplements.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='data/research/latest.json');p.add_argument('--output',default='data/research/triage.json');args=p.parse_args()
    data=json.loads(Path(args.input).read_text());out=[]
    for paper in data['papers']:
        try:out.append(classify(paper,lookup(paper['pmid'])))
        except Exception as e:
            item=classify(paper,{});item['full_text_access']='lookup_failed';item['lookup_error']=str(e);out.append(item)
        time.sleep(.2)
    counts={k:sum(x['full_text_access']==k for x in out) for k in sorted(set(x['full_text_access'] for x in out))}
    result={'schema_version':1,'total':len(out),'access_counts':counts,'warning':'Access flag is metadata only. No PDF/XML has been independently read; no protocols or outcome charts approved.','papers':out}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Triage:',len(out),'papers; access:',counts)
    for row in out:print(row['pmid'],row['full_text_access'],row['study_type_hint'])
if __name__=='__main__':main()
