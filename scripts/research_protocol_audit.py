#!/usr/bin/env python3
"""Source-linked arm/protocol/outcome review packets; never auto-publish."""
import argparse
import collections
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from scripts.research_enrich import get,BASE

FIELD_PATTERNS={
 'duration':r'\b\d+\s*(?:weeks?|months?)\b',
 'frequency':r'\b(?:twice|three times|\d+\s*times|two days|three days)\s+(?:a|per)\s+week\b',
 'exercises':r'\b(?:squat|deadlift|bench press|split squat|hip.thrust|leg press|military press)\b',
 'sets':r'\b(?:\d+|four|three|five)\s+sets?\b',
 'reps':r'\b(?:\d+|four|eight|ten)\s+repetitions?\b',
 'intensity':r'(?:\d+\s*%\s*(?:of\s*)?(?:pre.test\s*)?1RM|repetitions in reserve|\b\d+\s*RIR\b)',
 'rest':r'\b(?:\d+\s*(?:min(?:utes?)?|s(?:econds?)?)\s*(?:of\s*)?rest|rest\s*(?:for|of|between)|rest intervals?)\b',
 'progression':r'\b(?:increase the load|progressive overload|progression|weight was lowered|load was increased)\b',
 'weekly_schedule':r'\b(?:week\s*\d+|weeks?\s*\d+\s*(?:to|–|-)\s*\d+)\b'
}

def clean(text):return re.sub(r'\s+',' ',text).strip()

def table_rows(table):
    out=[]
    for tr in table.findall('.//tr'):
        cells=[clean(' '.join(c.itertext())) for c in tr if c.tag in ('th','td')]
        if any(cells):out.append(cells)
    return out

def review_packet(p,xml):
    root=ET.fromstring(xml)
    source=BASE+p['pmcid']+'/fullTextXML'
    relevant=[]
    for sec in root.findall('.//body//sec'):
        title=sec.find('title');heading=clean(' '.join(title.itertext())) if title is not None else ''
        if not re.search(r'train|protocol|intervention|method|exercise',heading,re.I):continue
        for j,para in enumerate(sec.findall('p'),1):
            relevant.append({'locator':{'pmcid':p['pmcid'],'section_id':sec.get('id'),'section':heading,'paragraph':j},'text':clean(' '.join(para.itertext()))})
    tables=[]
    for tab in root.findall('.//body//table-wrap'):
        caption=tab.find('caption');name=clean(' '.join(caption.itertext())) if caption is not None else ''
        if re.search(r'train|protocol|1RMs?|strength|performance',name,re.I):
            rows=table_rows(tab)
            tables.append({'table_id':tab.get('id'),'caption':name,'row_count':len(rows),'rows':rows})
    fields={}
    for field,pattern in FIELD_PATTERNS.items():
        refs=[]
        for item in relevant:
            m=re.search(pattern,item['text'],re.I)
            if m:refs.append({'source':item['locator'],'matched':m.group(0),'context':item['text'][max(0,m.start()-55):m.end()+90]})
        for table in tables:
            if field in ('weekly_schedule','intensity','sets','reps','rest') and re.search(r'train|protocol',table['caption'],re.I):
                refs.append({'source':{'pmcid':p['pmcid'],'table_id':table['table_id']},'matched':'training table present; individual cells require review'})
        fields[field]={'status':'candidate_found_not_verified' if refs else 'not_found','evidence':refs[:4]}
    # Numeric outcome cells are transcribed with exact row and column positions, never inferred group mapping.
    outcomes=[]
    for table in tables:
        if not re.search(r'1RM|strength|performance',table['caption'],re.I):continue
        for index,row in enumerate(table['rows']):
            if re.search(r'\b1\s?RM\b',row[0] if row else '',re.I) and re.search(r'\b(?:kg|BP|BS|DL|squat|deadlift)\b',row[0],re.I):
                outcomes.append({'source':{'pmcid':p['pmcid'],'table_id':table['table_id'],'row_index_zero_based':index},'cells':row,'numeric_verification':'pending_group_header_and_uncertainty_review'})
    missing=[key for key,val in fields.items() if val['status']=='not_found']
    return {'pmid':p['pmid'],'pmcid':p['pmcid'],'title':p['title'],'source_url':source,'field_evidence':fields,'missing_evidence_fields':missing,'tables':tables,'candidate_outcome_rows':outcomes,'runnable':False,'chart_publishable':False,'human_review_required':True,'protocol_decision':'BLOCKED','chart_decision':'BLOCKED','reason':'Keyword/table evidence is not complete per-arm, per-session verified prescription or chart-safe outcome mapping.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='data/research/oa_candidates_v2.json');ap.add_argument('--output',default='data/research/protocol_audit.json');a=ap.parse_args()
    source=json.loads(Path(a.input).read_text());papers=[]
    for p in source['papers']:
        try:row=review_packet(p,get(BASE+p['pmcid']+'/fullTextXML'))
        except Exception as exc:row={'pmid':p['pmid'],'error_type':type(exc).__name__,'runnable':False,'chart_publishable':False,'protocol_decision':'BLOCKED','chart_decision':'BLOCKED'}
        papers.append(row);print(p['pmid'],row['protocol_decision'],'fields',len(row.get('field_evidence',{})),'outcome_rows',len(row.get('candidate_outcome_rows',[])),flush=True);time.sleep(.35)
    result={'schema_version':1,'total':len(papers),'runnable_count':sum(p['runnable'] for p in papers),'chart_count':sum(p['chart_publishable'] for p in papers),'notes':'Review packet only. Exact original table cells retained for human mapping, no inferred outcomes or prescriptions.','papers':papers}
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('COMPLETE',len(papers),'runnable',result['runnable_count'],'charts',result['chart_count'],flush=True)
if __name__=='__main__':main()
