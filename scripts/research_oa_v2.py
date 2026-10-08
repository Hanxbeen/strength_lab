#!/usr/bin/env python3
"""Batch OA metadata prefilter, conservative SBD title gate, verify XML. Never publish."""
import argparse
import json
import re
import time
import urllib.parse
from pathlib import Path
from scripts.research_batch import discover
from scripts.research_enrich import get, BASE
import xml.etree.ElementTree as ET

DIRECT=re.compile(r'\b(squat|bench press|deadlift|powerlift)',re.I)
EXCLUDED=re.compile(r'acute|immediate|single.session|post.activation|preconditioning|sprint|jump|supplement|capsaicin|mood|intestinal|swimming|throwing|systematic.review|meta.analysis',re.I)

def classify(p):
    title=p.get('title','')
    if EXCLUDED.search(title):return 'excluded_off_topic_or_acute'
    if not DIRECT.search(title):return 'insufficient_title_specificity'
    return 'direct_sbd_candidate'

def lookup_batch(pmids):
    term='('+' OR '.join('EXT_ID:'+str(p) for p in pmids)+') AND SRC:MED'
    url=BASE+'search?'+urllib.parse.urlencode({'query':term,'format':'json','pageSize':len(pmids)})
    data=json.loads(get(url))
    return {str(x.get('id')):x for x in data.get('resultList',{}).get('result',[])}

def execute(pool,limit):
    papers,total=discover(pool)
    eligible=[p for p in papers if classify(p)=='direct_sbd_candidate']
    meta={}
    for i in range(0,len(eligible),10):
        meta.update(lookup_batch([p['pmid'] for p in eligible[i:i+10]]));time.sleep(.3)
    out=[];audit=[]
    for p in papers:
        reason=classify(p)
        if reason!='direct_sbd_candidate':audit.append({'pmid':p['pmid'],'decision':reason});continue
        hit=meta.get(p['pmid'],{})
        pmcid=hit.get('pmcid')
        if hit.get('isOpenAccess')!='Y' or not pmcid:
            audit.append({'pmid':p['pmid'],'decision':'no_open_xml_metadata'});continue
        if len(out)>=limit:
            audit.append({'pmid':p['pmid'],'decision':'quota_reached'});continue
        try:
            xml=get(BASE+pmcid+'/fullTextXML');root=ET.fromstring(xml)
            if root.find('.//body') is None:raise ValueError('missing body')
            item=dict(p,pmcid=pmcid,full_text_url=BASE+pmcid+'/fullTextXML',full_text_status='open_xml_accessible',runnable=False,chart_publishable=False,relation_publishable=False,protocol_status='pending_manual_review',outcome_status='pending_manual_review')
            out.append(item)
            audit.append({'pmid':p['pmid'],'decision':'open_xml_verified'})
            print('VERIFIED',len(out),pmcid,p['title'][:65],flush=True)
        except Exception as exc:audit.append({'pmid':p['pmid'],'decision':'xml_unavailable','error_type':type(exc).__name__})
        time.sleep(.3)
    return {'schema_version':2,'retrieved_ids':total,'pool_candidates':len(papers),'title_gate_candidates':len(eligible),'selected':len(out),'requested':limit,'complete':len(out)==limit,'warning':'Title gate is conservative and misses relevant papers. No source-level training prescription or result has been approved.','audit':audit,'papers':out}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--pool',type=int,default=100);ap.add_argument('--limit',type=int,default=20);ap.add_argument('--output',default='data/research/oa_candidates_v2.json');a=ap.parse_args()
    if not 1<=a.limit<=a.pool<=100:ap.error('1 <= limit <= pool <= 100')
    result=execute(a.pool,a.limit)
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('SUMMARY',result['selected'],'/',a.limit,'title candidates',result['title_gate_candidates'],'complete',result['complete'])
if __name__=='__main__':main()
