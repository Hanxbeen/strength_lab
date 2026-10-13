"""Question-oriented evidence discovery. Collection never approves a prescription."""
import argparse
import datetime as dt
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

QUESTIONS = {
 'Q01': ('1RM measurement', '(TITLE_ABS:"one repetition maximum" OR TITLE_ABS:1RM) AND (TITLE_ABS:reliability OR TITLE_ABS:prediction)'),
 'Q02': ('Load, volume and frequency', '(TITLE_ABS:"resistance training") AND (TITLE_ABS:strength) AND (TITLE_ABS:"network meta-analysis" OR TITLE_ABS:"dose response" OR TITLE_ABS:periodization)'),
 'Q03': ('Autoregulation and failed repetitions', '(TITLE_ABS:powerlifting OR TITLE_ABS:"resistance training") AND (TITLE_ABS:autoregulation OR TITLE_ABS:"repetitions in reserve" OR TITLE_ABS:"RPE")'),
 'Q04': ('Rest intervals', '(TITLE_ABS:"resistance training" OR TITLE_ABS:"strength training") AND (TITLE_ABS:"rest interval" OR TITLE_ABS:"interset rest")'),
 'Q05': ('Assistance transfer', '(TITLE_ABS:squat OR TITLE_ABS:"bench press" OR TITLE_ABS:deadlift) AND (TITLE_ABS:"exercise variation" OR TITLE_ABS:"exercise selection" OR TITLE_ABS:transfer)'),
 'Q06': ('Hypertrophy and strength', 'TITLE_ABS:"resistance training" AND TITLE_ABS:hypertrophy AND (TITLE_ABS:load OR TITLE_ABS:volume)'),
 'Q07': ('Sleep recovery and fatigue', '(TITLE_ABS:"resistance training" OR TITLE_ABS:"resistance exercise" OR TITLE_ABS:powerlifting) AND (TITLE_ABS:"sleep restriction" OR TITLE_ABS:recovery OR TITLE_ABS:fatigue)'),
 'Q08': ('Plateau and deload', '(TITLE_ABS:"resistance training" OR TITLE_ABS:powerlifting) AND (TITLE_ABS:deload OR TITLE_ABS:plateau OR TITLE_ABS:overreaching)'),
 'Q09': ('Peaking and taper', 'TITLE_ABS:powerlifting AND (TITLE_ABS:taper OR TITLE_ABS:peaking OR TITLE_ABS:cessation)'),
 'Q10': ('Time frequency and missed sessions', 'TITLE_ABS:"resistance training" AND (TITLE_ABS:"time efficient" OR TITLE_ABS:"reduced frequency" OR TITLE_ABS:detraining)'),
 'Q11': ('History and load selection', '(TITLE_ABS:"resistance training" OR TITLE_ABS:powerlifting) AND (TITLE_ABS:"load selection" OR TITLE_ABS:"RPE" OR TITLE_ABS:"repetitions in reserve")'),
 'Q12': ('Adherence and adverse events', '(TITLE_ABS:powerlifting OR TITLE_ABS:"resistance training") AND (TITLE_ABS:adherence OR TITLE_ABS:"adverse events" OR TITLE_ABS:dropout)'),
}

def fetch(query, cursor='*', page_size=20):
    params = urllib.parse.urlencode({'query': query, 'format':'json', 'resultType':'core',
                                    'pageSize':page_size, 'cursorMark':cursor})
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + params
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response), url
        except (OSError, ValueError):
            if attempt == 2: raise
            time.sleep(1 + attempt)

def collect(page_size=20, pages=1):
    started=dt.datetime.now(dt.timezone.utc).isoformat()
    records={}; runs=[]
    for qid,(title,query) in QUESTIONS.items():
        run={'question_id':qid,'question':title,'query':query,'provider':'Europe PMC',
             'pages':[],'status':'running','coverage_status':'in_review'}
        cursor='*'
        try:
            for _ in range(pages):
                data,url=fetch(query,cursor,page_size)
                found=data.get('resultList',{}).get('result',[])
                next_cursor=data.get('nextCursorMark')
                run['pages'].append({'url':url,'cursor':cursor,'next_cursor':next_cursor,
                                     'hit_count':data.get('hitCount'),'returned':len(found)})
                for p in found:
                    key=p.get('doi','').lower() or p.get('source','')+':'+p['id']
                    if key not in records:
                        records[key]={'id':key,'pmid':p['id'] if p.get('source')=='MED' else None,
                          'pmcid':p.get('pmcid'),'doi':p.get('doi'),'title':p.get('title'),
                          'year':p.get('pubYear'),'publication_types':p.get('pubTypeList',{}).get('pubType',[]),
                          'authors':p.get('authorString'),'abstract_available':bool(p.get('abstractText')),
                          'abstract_sha256':hashlib.sha256(p.get('abstractText','').encode()).hexdigest(),
                          'question_ids':[],'review_status':'candidate',
                          'scientific_approval':False,'correction_review':'not_yet_reviewed',
                          'cohort_deduplication':'not_yet_reviewed',
                          'fulltext_access':{'is_open_access':p.get('isOpenAccess'),'urls':p.get('fullTextUrlList',{})}}
                    if qid not in records[key]['question_ids']:records[key]['question_ids'].append(qid)
                if not found or not next_cursor or next_cursor==cursor:
                    run['search_exhausted']=True;break
                cursor=next_cursor
                time.sleep(.25)
            run['status']='succeeded'
            run.setdefault('search_exhausted',False)
        except Exception as error:
            run.update(status='failed',error=type(error).__name__,coverage_status='unsearched')
        runs.append(run)
        print(qid, run['status'], sum(p['returned'] for p in run['pages']), flush=True)
    return {'schema_version':1,'started_at':started,'finished_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'purpose':'Foundational candidate collection, not publication or completed evidence review',
            'status':'partial' if any(r['status']!='succeeded' for r in runs) else 'succeeded',
            'search_scope':'Bounded initial Europe PMC search; synthesis and non-OA reports retained',
            'search_runs':runs,'reports':list(records.values()),'unique_reports':len(records)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--pages',type=int,default=1)
    args=p.parse_args()
    if not 1 <= args.pages <= 10: p.error('pages must be between 1 and 10')
    result=collect(pages=args.pages)
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'unique_reports':result['unique_reports']}))
