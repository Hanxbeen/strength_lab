#!/usr/bin/env python3
"""Produce explicit human-review queue and source-integrity checks from evidence packets."""
import argparse
import json
import re
from pathlib import Path

REQUIRED=('study_design','population','arms','duration','frequency','session_exercises','sets_reps','intensity','rest','progression','accessories','week_by_week','group_outcomes','uncertainty_type','outcome_units')

def review_item(p):
    tables=p.get('tables',[])
    training=[t for t in tables if re.search(r'train|protocol',t['caption'],re.I)]
    outcomes=p.get('candidate_outcome_rows',[])
    integrity=[]
    for t in tables:
        if t['row_count']!=len(t['rows']):integrity.append({'table_id':t['table_id'],'issue':'row_count_mismatch'})
        if len(set(tuple(r) for r in t['rows']))<len(t['rows']) and re.search(r'1RM|strength',t['caption'],re.I):integrity.append({'table_id':t['table_id'],'issue':'duplicate_result_row'})
    weeks=[]
    for t in training:
        for index,row in enumerate(t['rows']):
            if row and re.fullmatch(r'(?:[1-9]|1[0-9]|2[0-9])',row[0]):
                weeks.append({'week':int(row[0]),'table_id':t['table_id'],'row_index_zero_based':index})
    return {'pmid':p['pmid'],'pmcid':p.get('pmcid'),'title':p.get('title'),'status':'awaiting_human_review','fields':{k:{'status':'unverified','reviewer':None,'source_locators':[],'notes':None} for k in REQUIRED},'source_hints_present':{k:bool(v['evidence']) for k,v in p.get('field_evidence',{}).items()},'training_table_ids':[t['table_id'] for t in training],'week_row_locators':weeks,'numeric_outcome_row_count':len(outcomes),'integrity_issues':integrity,'runnable':False,'chart_publishable':False,'blocking_reasons':['No signed field-level human verification','No verified arm-by-arm complete prescription','No verified group/timepoint/uncertainty mapping for numerical outcomes']}

def create(data):
    items=[review_item(p) for p in data['papers']]
    return {'schema_version':1,'total':len(items),'approved_protocols':0,'approved_charts':0,'required_review_fields':list(REQUIRED),'papers':items}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='data/research/protocol_audit.json');ap.add_argument('--output',default='data/research/review_queue.json');a=ap.parse_args()
    result=create(json.loads(Path(a.input).read_text()))
    p=Path(a.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('REVIEW QUEUE',result['total'],'approved',result['approved_protocols'],'charts',result['approved_charts'])
    for r in result['papers']:print(r['pmid'],'week rows',len(r['week_row_locators']),'outcome rows',r['numeric_outcome_row_count'],'integrity issues',len(r['integrity_issues']))
if __name__=='__main__':main()
