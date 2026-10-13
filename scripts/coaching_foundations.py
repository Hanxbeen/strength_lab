"""Named foundational leads, separated from broad unscreened discovery."""
import datetime as dt
import json
from pathlib import Path
from scripts.coaching_corpus import fetch

SEEDS=[
 ('DOI:10.3389/fphys.2018.00247',['Q02','Q03','Q11'],'Load adjustment and prior-week history'),
 ('DOI:10.1519/JSC.0000000000001272',['Q04'],'1 vs 3 minute interset rest'),
 ('DOI:10.1186/s40798-020-00260-z',['Q01'],'1RM repeatability synthesis; not an estimation formula'),
 ('DOI:10.1136/bjsports-2023-106807',['Q02','Q06'],'Prescription synthesis; not one executable programme'),
 ('DOI:10.1519/JSC.0000000000003164',['Q03'],'RIR vs fixed loading; compare with Helms null between-group result'),
 ('DOI:10.1249/MSS.0000000000001764',['Q02','Q06'],'Volume and hypertrophy vs strength distinction'),
 ('EXT_ID:36136596 AND SRC:MED',['Q07'],'Sleep restriction experiment; not a sleep-to-load formula'),
 ('EXT_ID:38274324 AND SRC:MED',['Q08'],'Deload randomized study; counter automatic universal deload claims'),
 ('EXT_ID:37639652 AND SRC:MED',['Q09'],'2 vs 4 days cessation; strength-athlete trial'),
 ('EXT_ID:32917000 AND SRC:MED',['Q09'],'Powerlifting taper review and reference tracing'),
 ('EXT_ID:28129275 AND SRC:MED',['Q02'],'Flexible vs traditional DUP; linked erratum must be resolved'),
 ('EXT_ID:28328723 AND SRC:MED',['Q02'],'Erratum for PMID28129275; not independent efficacy evidence'),
]
def collect():
    result={'collected_at':dt.datetime.now(dt.timezone.utc).isoformat(),
            'status':'candidate_mapping','reports':[],'failures':[],
            'note':'Purposive foundational leads. No comprehensive review or clinical approval claimed.'}
    for query,questions,purpose in SEEDS:
        try:
            data,url=fetch(query,page_size=5)
            records=data.get('resultList',{}).get('result',[])
            if len(records)!=1:raise ValueError('Identity not unique')
            p=records[0]
            row={'query':query,'query_url':url,'pmid':p['id'],'pmcid':p.get('pmcid'),'doi':p.get('doi'),
                 'title':p['title'],'year':p.get('pubYear'),'publication_types':p.get('pubTypeList',{}).get('pubType',[]),
                 'question_ids':questions,'purpose':purpose,'review_status':'metadata_verified',
                 'scientific_approval':False,'correction_status':'not_yet_reviewed',
                 'source_url':'https://pubmed.ncbi.nlm.nih.gov/'+p['id']+'/'}
            result['reports'].append(row)
            print(p['id'],p.get('pmcid'),p['title'],flush=True)
        except Exception as e:result['failures'].append({'query':query,'error':type(e).__name__})
    return result
if __name__=='__main__':
    result=collect()
    Path('data/research/coaching/foundational-leads.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('verified metadata',len(result['reports']),'failures',len(result['failures']))
