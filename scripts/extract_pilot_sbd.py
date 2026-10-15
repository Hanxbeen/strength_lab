"""Extract source cells without executing formulas; create no public prescription."""
import hashlib
import json
from pathlib import Path
import xlrd
from research_engine.core import digest

ROOT=Path(__file__).resolve().parents[1]
FILE='AEK PL research traditional periodized template.xls'
LIFTS={'Squat':'barbell_back_squat','Bench press':'barbell_bench_press','Deadlift':'barbell_deadlift'}

def stable_numbers(value):
    # JSON transports may rewrite 75.0 as 75; normalize new manifests only.
    if isinstance(value,float) and value.is_integer():return int(value)
    if isinstance(value,list):return [stable_numbers(x) for x in value]
    if isinstance(value,dict):return {k:stable_numbers(v) for k,v in value.items()}
    return value

def extract(path):
    raw=path.read_bytes();book=xlrd.open_workbook(file_contents=raw);sessions=[]
    for name,offset in [('high volume mesocycle 4w',0),('transitional 4w',4),('Peaking phase 2w',8)]:
        sheet=book.sheet_by_name(name);week=None;session=None;anchor=None;literal=None
        for index in range(sheet.nrows):
            row=sheet.row_values(index);first=str(row[0]).strip()
            if first.lower().startswith('week '):week=int(first.split()[1])+offset;session=None
            elif first.startswith('Day '):
                session={'week':week,'day':int(first.split()[1]),'day_label':first,'phase':name,'rows':[]}
                sessions.append(session);anchor=None;literal=None
            elif session and all(isinstance(row[c],(float,int)) for c in [2,3,4]):
                label=str(row[1]).strip()
                if isinstance(row[0],(float,int)):
                    anchor=LIFTS[label];literal=label
                if label:literal=label
                if anchor is None:raise ValueError('Unanchored exercise')
                session['rows'].append({'numbered_sbd_anchor':anchor,'source_exercise':literal,
                    'percent_1rm':round(row[2]*100,6),'reps':int(row[3]),'sets':int(row[4]),
                    'role':'unspecified','source':{'file':FILE,'sheet':name,'cells':f'A{index+1}:F{index+1}',
                        'literal_label':row[1],'cached_example_kg':row[5]}})
    assert [(s['week'],s['day']) for s in sessions]==[(w,d) for w in range(1,11) for d in range(1,4)]
    protocol=stable_numbers({'weeks':10,'days_per_week':3,'sessions':sessions})
    return {'id':'pilot2018-per-template-v1','adapter_version':'sbd-template-v1','title':'SBD 10주 주기화 · 내부 조정안',
        'review_status':'source_extracted','scientific_approval':False,'publication_status':'internal_preview',
        'application':'source_template_with_explicit_product_adaptation','exercises':list(LIFTS.values()),
        'protocol':protocol,'protocol_sha256':digest(protocol),'source_sha256':hashlib.sha256(raw).hexdigest(),
        'evidence':{'doi':'10.3390/sports6030086','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC6162635/',
            'locator':'PER training methods, Table 1, supplementary PER XLS','license':'CC-BY-4.0',
            'attribution':'Androulakis-Korakakis et al., Sports 2018, 6(3), 86',
            'limitations':['Nonrandomized pilot; PER 5 enrolled, 3 analyzed; two injury withdrawals, one training-related.',
                'National competition outcome is not an individual gym forecast.',
                'Spreadsheet Front squat labels conflict with manuscript SBD description. Original labels remain unchanged.']},
        'adaptations':{'numbered_sbd_adaptation_v1':'Explicit user selection uses numbered SBD block instead of Front squat labels. This is a product substitution, not a verified source correction.',
            'load':'Frozen lift-specific measured 1RM × source percentage; nearest half-up equipment increment. Cached kg and Excel formula logic are not reused.',
            'rest':'User selects inter-set and inter-exercise durations; source duration not established.',
            'schedule':'Sequential three-day weeks, 48-hour minimum between sessions; product spacing rule, delays allowed.',
            'roles':'All numeric rows retained; no guessed warmup/work-set classification.',
            'assessment':'Optional measured post-tests, with same/different/unknown conditions recorded separately.'},
        'guidance':{'working_set_rpe_ceiling':9,'locator':'PER training methods','load_adjustment_formula':None,
                    'plateau_formula':None,'accessory_exercises':[]},
        'release_limit':'Internal allowlisted engineering review only; not a general user recommendation.'}

if __name__=='__main__':
    source=ROOT/'data/research/coaching/sources/pilot2018-supplement'/FILE
    (ROOT/'data/research/coaching/pilot2018-sbd.json').write_text(json.dumps(extract(source),ensure_ascii=False,indent=2)+'\n')
