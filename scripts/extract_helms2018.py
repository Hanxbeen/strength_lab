"""Reproducible extraction from the CC-BY article, including table footnotes."""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from research_engine.core import digest

def extract(content):
    root=ET.fromstring(content)
    doi=next(x.text for x in root.findall('.//article-id') if x.get('pub-id-type')=='doi')
    if doi!='10.3389/fphys.2018.00247':raise ValueError('Wrong article')
    tables={t.get('id'):t for t in root.findall('.//table-wrap')}
    weeks=[]
    for row in tables['T2'].findall('.//tbody/tr'):
        cells=[''.join(x.itertext()) for x in row.findall('td')]
        week=int(cells[0])
        if week==0:continue
        days=[]
        for d in range(3):
            if 'Testing' in cells[d+1]:
                days.append({'kind':'post_test'});continue
            numbers=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',cells[d+1])]
            effort=[float(x) for x in re.findall(r'\d+(?:\.\d+)?',cells[d+4])]
            if len(numbers)!=3 or len(effort)!=4:raise ValueError('Table layout changed')
            days.append({'sets':int(numbers[0]),'reps':int(numbers[1]),'percent_1rm':numbers[2],
                         'rpe_range':effort[2:4],'conditional_progression':week in (3,5,7)})
        weeks.append({'week':week,'days':days})
    if len(weeks)!=8:raise ValueError('Missing weeks')
    method=next(s for s in root.findall('.//sec') if s.find('title') is not None and ''.join(s.find('title').itertext())=='Training protocol')
    method_text=' '.join(''.join(p.itertext()) for p in method.findall('p'))
    # Fail if the source no longer contains the currently interpreted operational rules.
    for phrase in ['load was reduced 4%', 'for every 0.5 RPE','5–7 min','10 min rest']:
        if phrase not in method_text:raise ValueError('Method changed: '+phrase)
    protocol={'weeks':weeks,'exercises':['barbell_back_squat','barbell_bench_press'],
              'rest_between_sets_seconds':[300,420],'rest_between_exercises_seconds':600,
              'load_adjustment_per_missed_rep_percent':4,'rpe_adjustment_per_half_point_percent':2,
              'spacing':'nonconsecutive days','prior_history':'same day of prior week',
              'locators':['Table 2 including TN1','Table 3','Training protocol','Participants']}
    return {'id':doi,'pmid':'29628895','pmcid':'PMC5877330',
       'title':'RPE vs. Percentage 1RM Loading in Periodized Programs Matched for Sets and Repetitions',
       'year':2018,'authors':'Helms et al.','url':'https://pmc.ncbi.nlm.nih.gov/articles/PMC5877330/',
       'publisher_url':'https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00247/full',
       'license':'CC BY, attribution retained in source snapshot','source_sha256':hashlib.sha256(content).hexdigest(),
       'adapter_version':'helms-2018-v1','protocol':protocol,'protocol_sha256':digest(protocol),
       'review_status':'source_extracted','publication_status':'research_preview','scientific_approval':False,
       'independent_domain_review':None,'correction_review':'not_yet_completed',
       'question_ids':['Q02','Q03','Q04','Q11','Q12'],
       'study':{'design':'parallel groups counterbalanced by strength; do not label randomized',
                'started':24,'completed':21,'arms':{'1RMG':11,'RPEG':10},
                'dropout':{'minor_injury_or_discomfort':2,'family_emergency':1},
                'cohort_id':'helms2018-21-completers','cohort_overlap_review':'not_yet_completed',
                'population':'Resistance-trained men, 19–35; >=2 years, squat >=1.5 and bench >=1.25 times body mass'},
       'outcomes':{'locator':'Abstract; Table 4','timepoint_weeks':8,
            'between_group_p':{'squat_1rm':.32,'bench_1rm':.52},
            'interpretation':'Both groups improved; no statistically significant between-group difference. Not equivalence proof.',
            'individual_growth_forecast':None},
       'limitations':['No deadlift programme or effect tested','Small male completer sample; supervised setting',
           'RPEG first week used researcher-selected loads; app user selection is an adaptation',
           'No validated long-term plateau, pain, sleep or missed-session prescription',
           'Do not interpret magnitude-based inference percentages as individual success probabilities',
           'Full evidence synthesis and independent domain review remain incomplete']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--xml',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();data=extract(Path(a.xml).read_bytes())
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('Extracted', len(data['protocol']['weeks']), 'weeks; scientific_approval=false')
