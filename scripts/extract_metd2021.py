"""Curated source extraction, not an automatic scientific approval pipeline."""
import hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from research_engine.core import digest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/research/coaching/sources/PMC8435792.xml'
OUTPUT=ROOT/'data/research/coaching/metd2021.json'
EXERCISES=['barbell_back_squat','barbell_bench_press','barbell_deadlift']

def extract(path=SOURCE):
    raw=path.read_bytes();root=ET.fromstring(raw)
    assert root.findtext(".//article-id[@pub-id-type='doi']")=='10.3389/fspor.2021.713655'
    sections={s.get('id'):{'title':s.findtext('title'),'text':' '.join(' '.join(p.itertext()) for p in s.findall('p'))}
              for s in root.findall('.//sec') if s.get('id') in ['sec32','sec33','sec34','sec35','sec36','sec37','sec38','sec39','sec40','sec41','sec42','sec43','sec44','sec45']}
    # Fail on unexpected source revisions rather than silently keeping hand-coded parameters.
    checks={'sec36':['6-week','2-3-1','40, 50, and 60%','70%'],
            'sec37':['single repetition','9–9.5'],'sec38':['two','three repetitions','80%'],
            'sec39':['70%','9–9.5']}
    for sid,terms in checks.items():
        for term in terms:assert term.replace('–','-') in sections[sid]['text'].replace('–','-'),(sid,term)
    protocol={'weeks':6,'days_per_week':3,'weekly_days':['Monday','Wednesday','Friday'],
        'sessions':[{'week':w,'day':d,'exercises':EXERCISES[:2] if d!=2 else EXERCISES[1:],
                     'locator':'sec36'} for w in range(1,7) for d in range(1,4)],
        'arms':{
            'MAX':{'studies':[3],'working_sets':1,'reps':{'kind':'fixed','value':1},
                'load':{'kind':'self_selected_rpe','rpe':[9,9.5]},'locator':'sec37'},
            'MAX_BOFF':{'studies':[3,4],'working_sets':3,'reps':{'kind':'fixed','value':1},
                'load':{'kind':'self_selected_rpe','rpe':[9,9.5]},
                'backoff':{'sets':2,'reps':3,'percent_actual_single_load':80,'rpe_target':None},'locator':'sec38'},
            'AMRAP':{'studies':[4],'working_sets':1,'reps':{'kind':'until_rpe','rpe':[9,9.5]},
                'load':{'kind':'percentage_1rm','percent':70},
                'warmup':{'sets':[{'percent':p,'reps':5} for p in (40,50,60)],'locator':'sec36'},'locator':'sec39'}},
        'training_rest_seconds':None,'rest_status':'not_specified_in_retrieved_training_methods',
        'accessory_exercises':[],'automatic_progression':None,'failure_load_formula':None,
        'testing':{'pre_days_before_training':7,'post_days_after_training':5,'attempts_per_lift':3,
                   'between_attempts_seconds_approx':300,'between_lifts_seconds_approx':[900,1200],
                   'locator':'sec35','not_training_rest':True}}
    return {'id':'metd2021-sbd-v1','adapter_version':'metd-2021-v1',
        'title':'SBD 6주 저용량 훈련 · 연구 미리보기','review_status':'source_extracted',
        'scientific_approval':False,'publication_status':'internal_preview','exercises':EXERCISES,
        'citation':{'doi':'10.3389/fspor.2021.713655','pmcid':'PMC8435792','pmid':'34527944',
            'title':root.findtext('.//article-title'),'url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC8435792/',
            'license':'CC BY','attribution':'Androulakis-Korakakis et al., Frontiers in Sports and Active Living (2021)',
            'source_sha256':hashlib.sha256(raw).hexdigest()},
        'protocol':protocol,'protocol_sha256':digest(protocol),'source_sections':sections,
        'study_context':{'design':'two small quasi-randomized exploratory interventions; not preregistered',
            'recruited':32,'analyzed':25,'withdrawals':{'count':7,'reason':'COVID-19 facility closures in study 4'},
            'study3':{'MAX':8,'MAX_BOFF':8},'study4':{'MAX_BOFF':5,'AMRAP':4},
            'population':{'sex':'male','resistance_training_years_min':4,'powerlifting_years_min':2,
                'rpe_training_years_min':1,'raw_powerlifting':True,'no_daily_max_previous_weeks':12},
            'supervision':'researcher supervision or video submission of working sets',
            'rpe_recorded':'all working sets including backoff','soreness':'24 h later; six-point scale; not a load-adjustment rule',
            'result_interpretation':'Exploratory model favored additional backoff work; single-only gains were less likely to meet elicited meaningful-change criteria. Not individual success probabilities or proof of an optimal minimum dose.',
            'limits':['Small convenience samples','No usual-training control','Survey-derived meaningful-change thresholds',
                      'Study 4 uses study 3 results as prior: not independent confirmation',
                      'High effort and experienced participants: not a beginner default'],
            'correction_check':'not_independently_completed'},
        'adaptations':['User-selected training rest: testing rest is not copied into training',
            'User-selected progressive warmup for MAX arms; exact warmup loads not reported',
            'Equipment rounding is product policy','Calendar shifts and minimum 48 h spacing are product policy',
            'No researcher supervision or soreness questionnaire reproduced',
            'AMRAP 70% uses frozen baseline: no unreported recalibration',
            'Backoff target resolves from recorded completed single; missing single requires explicit user load or skipping'],
        'not_supported':['Automatic RPE-to-load prediction','Automatic plateau or pain prescription','Unreviewed public release']}

if __name__=='__main__':
    value=extract();OUTPUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'id':value['id'],'version':digest(value),'arms':list(value['protocol']['arms']),'sessions_per_arm':18}))
