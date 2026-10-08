#!/usr/bin/env python3
"""Source-located evidence audit. No auto-generated workouts or effect sizes."""
import argparse
import json
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from scripts.research_enrich import get, BASE

SBD=re.compile(r'\b(?:back squat|front squat|half squat|squats?|bench press|deadlifts?|powerlift\w*)\b',re.I)
DURATION=re.compile(r'\b(?:(?:\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|twelve)[ -]weeks?|\d{1,2}[ -]months?|week(?:ly)?\s*\d{1,2})\b',re.I)
PROGRAM=re.compile(r'\b(?:sets?|repetitions?|reps?|training sessions?|training frequency|rest intervals?|progression|training load)\b',re.I)
RESULT=re.compile(r'\b(?:1\s?RM|one.repetition maximum|maximum strength|strength gains?)\b',re.I)
ACUTE=re.compile(r'\b(?:acute|single.session|single.bout|immediate)\b',re.I)

def sections(root):
    body=root.find('.//body')
    if body is None:return []
    found=[]
    for i,sec in enumerate(body.findall('.//sec')):
        title=sec.find('title')
        heading=' '.join(title.itertext()).strip() if title is not None else ''
        # Direct paragraphs only: do not misattribute nested child sections.
        parts=[' '.join(el.itertext()) for el in sec if el.tag in ('p','list','table-wrap')]
        text=' '.join(parts)
        if text.strip():found.append({'section':heading or f'section_{i+1}','text':re.sub(r'\s+',' ',text).strip()})
    return found

def citations(items,pattern,limit=3):
    out=[]
    for item in items:
        match=pattern.search(item['text'])
        if match:
            a=max(0,match.start()-100);b=min(len(item['text']),match.end()+150)
            out.append({'section':item['section'],'excerpt':item['text'][a:b],'matched_term':match.group()})
        if len(out)>=limit:break
    return out

def evaluate(paper,xml):
    root=ET.fromstring(xml)
    parts=sections(root)
    methods=[s for s in parts if re.search(r'method|protocol|training|intervention|exercise',s['section'],re.I)]
    results=[s for s in parts if re.search(r'result|outcome',s['section'],re.I)]
    # Avoid claiming actual protocol completeness from keyword matches.
    hints={'sbd_methods':citations(methods,SBD),'duration_methods':citations(methods,DURATION),'program_methods':citations(methods,PROGRAM),'one_rm_results':citations(results,RESULT),'acute_title':bool(ACUTE.search(paper['title']))}
    if hints['acute_title']:tier='exclude_acute_title'
    elif hints['sbd_methods'] and hints['duration_methods']:tier='direct_sbd_longitudinal_candidate'
    elif hints['sbd_methods']:tier='sbd_methods_duration_unverified'
    else:tier='supporting_or_unverified'
    return {'pmid':paper['pmid'],'pmcid':paper['pmcid'],'title':paper['title'],'tier':tier,'evidence_hints':hints,'methods_sections':len(methods),'results_sections':len(results),'runnable':False,'chart_publishable':False,'relation_publishable':False,'protocol_gate':'blocked_missing_field_level_verification','outcome_gate':'blocked_missing_arm_level_numeric_verification','source_url':BASE+paper['pmcid']+'/fullTextXML'}

def run(source):
    out=[]
    for p in source['papers']:
        try:row=evaluate(p,get(BASE+p['pmcid']+'/fullTextXML'))
        except Exception as exc:row={'pmid':p['pmid'],'pmcid':p['pmcid'],'tier':'fetch_or_parse_error','error_type':type(exc).__name__,'runnable':False,'chart_publishable':False,'relation_publishable':False}
        out.append(row);print(p['pmid'],row['tier'],flush=True);time.sleep(.35)
    return {'schema_version':1,'count':len(out),'warning':'Excerpts are search hints, not verified prescriptions, group outcomes or numeric source provenance. Human review mandatory.','papers':out}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',default='data/research/oa_candidates_v2.json');ap.add_argument('--output',default='data/research/evidence_audit.json');a=ap.parse_args()
    result=run(json.loads(Path(a.input).read_text()))
    path=Path(a.output);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('SUMMARY',result['count'])
if __name__=='__main__':main()
