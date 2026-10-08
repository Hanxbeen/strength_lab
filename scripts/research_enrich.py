#!/usr/bin/env python3
"""Open-access full text availability and conservative evidence screening."""
import argparse
import collections
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE='https://www.ebi.ac.uk/europepmc/webservices/rest/'
HEADERS={'User-Agent':'strength-lab-research/0.2 (public OA metadata)'}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=30) as r:return r.read()

def enrich(paper):
    paper=dict(paper)
    pmid=paper['pmid']
    url=BASE+'search?'+urllib.parse.urlencode({'query':'EXT_ID:'+pmid+' AND SRC:MED','format':'json','resultType':'core'})
    data=json.loads(get(url))
    hits=data.get('resultList',{}).get('result',[])
    hit=hits[0] if hits else {}
    pmcid=hit.get('pmcid')
    paper['pmcid']=pmcid
    paper['open_access_flag']=hit.get('isOpenAccess')=='Y'
    paper['full_text_url']=None
    paper['full_text_status']='not_available'
    paper['methods_keyword_hits']=[]
    paper['results_keyword_hits']=[]
    paper['screening_flags']=[]
    if pmcid and paper['open_access_flag']:
        try:
            raw=get(BASE+urllib.parse.quote(pmcid)+'/fullTextXML')
            root=ET.fromstring(raw)
            sections=root.findall('.//body//sec')
            fulltext=' '.join(root.itertext())
            if len(fulltext)<1500:raise ValueError('Full text unusually short')
            paper['full_text_status']='open_xml_accessible'
            paper['full_text_url']=BASE+pmcid+'/fullTextXML'
            method_words=['sets','repetitions','rest interval','progression','intensity','training frequency']
            result_words=['1rm','one-repetition maximum','squat','bench press','deadlift']
            paper['methods_keyword_hits']=[w for w in method_words if w in fulltext.lower()]
            paper['results_keyword_hits']=[w for w in result_words if w in fulltext.lower()]
            if not sections:paper['screening_flags'].append('No section structure found')
        except Exception as exc:
            paper['full_text_status']='xml_fetch_failed'
            paper['screening_flags'].append(type(exc).__name__)
    paper['protocol_status']='needs_human_full_text_review' if paper['full_text_status']=='open_xml_accessible' else 'blocked_no_verified_full_text'
    paper['outcome_status']='needs_numeric_source_verification' if paper['full_text_status']=='open_xml_accessible' else 'blocked_no_verified_full_text'
    paper['runnable']=False
    paper['chart_publishable']=False
    paper['relation_publishable']=False
    return paper

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',default='data/research/latest.json');p.add_argument('--output',default='data/research/enriched.json');args=p.parse_args()
    source=json.loads(Path(args.input).read_text(encoding='utf-8'))
    rows=[]
    for i,record in enumerate(source['papers'],1):
        try:row=enrich(record)
        except Exception as exc:
            row=dict(record,full_text_status='lookup_error',screening_flags=[type(exc).__name__],runnable=False,chart_publishable=False,relation_publishable=False)
        rows.append(row)
        print(f"{i:02}/{len(source['papers'])} {row['pmid']} {row['full_text_status']} runnable={row['runnable']}",flush=True)
        time.sleep(.35)
    counts=dict(collections.Counter(row['full_text_status'] for row in rows))
    result={'schema_version':2,'source_query':source['query'],'total':len(rows),'access_counts':counts,'notes':'Full text availability and keyword presence are NOT protocol verification. All outputs blocked pending manual gold review.','papers':rows}
    dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('SUMMARY',counts,flush=True)
if __name__=='__main__':main()
