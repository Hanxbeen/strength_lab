#!/usr/bin/env python3
"""Compare curated reference cells with extracted JATS cells; never mistake this for independent human review."""
import argparse
import json
import re
from pathlib import Path


def norm(s):
    return re.sub(r'\s+',' ',str(s)).replace('−','-').replace('–','-').replace(' ',' ').strip()


def evaluate(packets, reference):
    indexed={p['pmid']:p for p in packets['papers']}
    comparisons=[]
    for case in reference['cases']:
        paper=indexed.get(case['pmid'])
        table=next((t for t in paper.get('tables',[]) if t['table_id']==case['table_id']),None) if paper else None
        row=table['rows'][case['row_index_zero_based']] if table and 0<=case['row_index_zero_based']<len(table['rows']) else None
        expected=case['expected_cells']
        # All expected cells, including group columns, must match exactly after whitespace normalization.
        actual=row[:len(expected)] if row else []
        passed=len(actual)==len(expected) and all(norm(a)==norm(b) for a,b in zip(actual,expected))
        comparisons.append({'case_id':case['case_id'],'pmid':case['pmid'],'table_id':case['table_id'],'row_index_zero_based':case['row_index_zero_based'],'passed':passed,'expected_cells':expected,'actual_cells':actual})
    n=len(comparisons);correct=sum(c['passed'] for c in comparisons)
    return {'schema_version':1,'reference_status':reference['reference_status'],'total_cases':n,'matched_cases':correct,'failed_cases':n-correct,'exact_row_accuracy':correct/n if n else None,'comparisons':comparisons,'publication_approved':False,'limitations':'Curated reference is not independently double-annotated. Cell-level match cannot establish protocol completeness, scientific validity or group header correctness.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--packets',default='data/research/protocol_audit.json');ap.add_argument('--reference',default='data/research/gold_reference.json');ap.add_argument('--output',default='data/research/gold_eval.json');a=ap.parse_args()
    result=evaluate(json.loads(Path(a.packets).read_text()),json.loads(Path(a.reference).read_text()))
    Path(a.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('GOLD EVAL',result['matched_cases'],'/',result['total_cases'],'failed',result['failed_cases'])
    if result['failed_cases']:raise SystemExit(1)
if __name__=='__main__':main()
