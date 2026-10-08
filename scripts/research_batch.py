#!/usr/bin/env python3
"""Reproducible PubMed discovery. Metadata only; never generates prescriptions."""
import argparse
import datetime as dt
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
QUERY = '(resistance training[Title/Abstract] OR strength training[Title/Abstract] OR powerlifting[Title/Abstract]) AND (one repetition maximum[Title/Abstract] OR 1RM[Title/Abstract] OR maximal strength[Title/Abstract]) AND (randomized controlled trial[Publication Type] OR controlled clinical trial[Publication Type] OR trial[Title/Abstract]) NOT (animals[MeSH Terms] NOT humans[MeSH Terms])'

def fetch(endpoint, params):
    url = BASE + endpoint + '?' + urllib.parse.urlencode({**params, 'tool':'strength_lab_research_batch', 'email':'research@example.org'})
    req = urllib.request.Request(url, headers={'User-Agent':'strength-lab-research/0.1 (metadata discovery)'})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read()

def discover(limit):
    root = ET.fromstring(fetch('esearch.fcgi', {'db':'pubmed','term':QUERY,'retmax':str(max(limit*5,100)),'sort':'relevance','retmode':'xml'}))
    ids = [e.text for e in root.findall('./IdList/Id') if e.text]
    records=[]
    for i in range(0,len(ids),50):
        root=ET.fromstring(fetch('efetch.fcgi', {'db':'pubmed','id':','.join(ids[i:i+50]),'rettype':'xml','retmode':'xml'}))
        for article in root.findall('.//PubmedArticle'):
            pmid=article.findtext('./MedlineCitation/PMID')
            title=''.join(article.find('./MedlineCitation/Article/ArticleTitle').itertext()) if article.find('./MedlineCitation/Article/ArticleTitle') is not None else ''
            abstract=' '.join(''.join(x.itertext()) for x in article.findall('./MedlineCitation/Article/Abstract/AbstractText'))
            doi=next((x.text for x in article.findall('./PubmedData/ArticleIdList/ArticleId') if x.attrib.get('IdType')=='doi'),None)
            year=article.findtext('./MedlineCitation/Article/Journal/JournalIssue/PubDate/Year') or article.findtext('./MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate') or ''
            text=(title+' '+abstract).lower()
            relevance=sum(bool(re.search(pattern,text)) for pattern in [r'\b1\s?rm\b|one.repetition.maximum',r'squat|bench.press|deadlift',r'resistance.train|strength.train|powerlift',r'randomi[sz]|intervention|training.program'])
            # Exclude clearly off-scope topics; this is candidate screening, not scientific validation.
            excluded=bool(re.search(r'supplementation|caffeine|beetroot|cistanche|fasted.state|amphetamine|prepuber|calisthenic|push.up|running.specific|hamstring.muscle.activation',text))
            if excluded or not re.search(r'squat|bench.press|deadlift|powerlift',text):continue
            if not pmid: continue
            records.append({'pmid':pmid,'doi':doi,'title':title,'year':year,'abstract':abstract,'score':relevance,'status':'metadata_candidate','protocol_status':'not_verified','outcome_status':'not_verified','reason':'Full text, arm-specific prescription, progression and numerical outcomes not independently verified','pubmed_url':'https://pubmed.ncbi.nlm.nih.gov/'+pmid+'/'})
        time.sleep(.38)
    records.sort(key=lambda r:(-r['score'],-int(re.search(r'\d{4}',r['year']).group()) if re.search(r'\d{4}',r['year']) else 0,r['pmid']))
    seen=set(); unique=[]
    for r in records:
        key=(r['doi'] or 'pmid:'+r['pmid']).lower()
        if key not in seen:
            unique.append(r);seen.add(key)
        if len(unique)==limit:break
    return unique, len(ids)

def main():
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=20);p.add_argument('--output',default='data/research/latest.json');args=p.parse_args()
    if not 1<=args.limit<=100: p.error('--limit must be 1..100')
    rows,total=discover(args.limit)
    result={'schema_version':1,'generated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'query':QUERY,'retrieved_ids':total,'selected':len(rows),'notes':'Discovery only. No protocol, chart or paper relationship is approved. Human gold-label validation required.','papers':rows}
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Retrieved {total} PubMed IDs; selected {len(rows)}; output {path}')
    for row in rows:print(row['pmid'],row['score'],row['year'],row['title'][:95])
    if len(rows)<args.limit:raise SystemExit('FAIL: fewer results than requested')
if __name__=='__main__':main()
