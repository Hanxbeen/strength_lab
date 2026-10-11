"""Explicit, source-version-pinned adapters. Unrecognised text is never inferred."""
import copy
import hashlib
import re
import xml.etree.ElementTree as ET
from .core import InvalidProgramme, digest

SOURCES = {
 'PMC11140948': {'pmid':'38816857','sha256':'d2cca85b325acd35a02d6292e1b15b2f91aa8a69c57b97099884622e75208f2f','section':'Sec10','population':'Sec4','license':'CC-BY-4.0'},
 'PMC5003312': {'pmid':'27625750','sha256':'dd55276e3ec14ae5d6b62872d9fbf5e62bd3b804e123c49eff66d95f2c649f74','section':'sec172223','population':'sec172222','license':'CC-BY-NC-4.0'},
 'PMC6974452': {'pmid':'32009980','sha256':'53086cee6dfa9229cec15ea7f408dbe8ac73e20b5b02ce89fb7170ca96c2a829','section':'S2.SS2','population':'S2.SS1','license':'CC-BY-4.0'},
}

def norm(s):
    return re.sub(r'\s+',' ',s).replace('–','-').replace('−','-').strip()

class Source:
    def __init__(self, pmc, raw):
        if pmc not in SOURCES: raise InvalidProgramme('UNSUPPORTED_SOURCE')
        self.pmc=pmc;self.contract=SOURCES[pmc]
        if hashlib.sha256(raw).hexdigest()!=self.contract['sha256']: raise InvalidProgramme('SOURCE_CHANGED')
        self.root=ET.fromstring(raw)
        ids=[x.text for x in self.root.findall('.//article-meta/article-id')]
        if self.contract['pmid'] not in ids or pmc not in ids: raise InvalidProgramme('SOURCE_IDENTITY')
    def paragraphs(self, section):
        nodes=self.root.findall('.//body//sec[@id="'+section+'"]')
        if len(nodes)!=1: raise InvalidProgramme('AMBIGUOUS_SECTION')
        return [norm(' '.join(p.itertext())) for p in nodes[0].findall('p')]
    def match(self, pattern, section=None):
        section=section or self.contract['section']
        hits=[]
        for i,text in enumerate(self.paragraphs(section),1):
            m=re.search(pattern,text,re.I)
            if m: hits.append((m,{'section_id':section,'paragraph':i,'matched_text_sha256':hashlib.sha256(m.group().encode()).hexdigest()}))
        if len(hits)!=1: raise InvalidProgramme('MISSING_OR_AMBIGUOUS_EVIDENCE: '+pattern)
        return hits[0]
    def evidence(self, pattern, section=None):
        return self.match(pattern,section)[1]
    def metadata(self):
        title=self.root.find('.//article-meta/title-group/article-title')
        return {'pmcid':self.pmc,'pmid':self.contract['pmid'],'sha256':self.contract['sha256'],
                'url':'https://pmc.ncbi.nlm.nih.gov/articles/'+self.pmc+'/',
                'title':norm(' '.join(title.itertext())), 'license':self.contract['license'],
                'raw_text_redistributed':False,'adapter_version':'1','cohort_deduplication':'not_independently_assessed'}

def add_proof(p, key, value, locator=None, kind='source_reported', policy_id=None):
    p['provenance'][key]={'kind':kind,'source_sha256':p['source']['sha256'],
                          'locator':locator,'policy_id':policy_id,'value_sha256':digest(value)}

def base(src, arm, label, weeks, frequency, population, context, progression, spacing, order, locations):
    p={'schema_version':2,'id':src.pmc+'-'+arm,'arm':arm,'title':label,'source':src.metadata(),
       'weeks':weeks,'sessions_per_week':frequency,'population':population,'context':context,
       'progression':progression,'spacing':spacing,'order':order,'exercises':[], 'provenance':{},
       'applicability':'Recorded study population; not an individual outcome guarantee',
       'independent_expert_review':False}
    for k in ('weeks','sessions_per_week','population','context','progression','spacing','order'):
        kind='source_reported' if locations.get(k) else 'not_reported'
        add_proof(p,k,p[k],locations.get(k),kind)
    return p

def exercise(p, id, sets, reps, load, rest, tempo, proof):
    x={'id':id,'sets':sets,'reps':reps,'load':load,'rest':rest,'tempo':tempo}
    i=len(p['exercises']);p['exercises'].append(x)
    for key,value in x.items():
        add_proof(p,'exercises.'+str(i)+'.'+key,value,proof.get(key), 'source_reported' if proof.get(key) else 'not_reported')

def lower_body(src):
    m, schedule=src.match(r'twice a week for (\d+) weeks')
    initial, load_proof=src.match(r'initially set at (\d+)% of pre-test 1RM')
    rest, rest_proof=src.match(r'Each set was separated by ≥\s*(\d+) min of rest for all exercises')
    sets=src.evidence(r'four sets of four repetitions of trap bar deadlifts')
    main_squat=src.evidence(r'same number of sets and repetitions with barbell half squats')
    accessories=src.evidence(r'3 sets of 8 repetitions of both Bulgarian split squats using dumbbells and barbell hip-thrusts')
    effort=src.evidence(r'two repetitions in reserve')
    up, progression_proof=src.match(r'increase the load by ([\d.]+) kg to ([\d.]+) kg if they could complete more than four repetitions')
    down,_=src.match(r'weight was lowered by ([\d.]+) kg to ([\d.]+) kg on the next set')
    pop=src.evidence(r'RT 2-3 days per week for the last 6 months',src.contract['population'])
    src.evidence(r'females;\s*>\s*18 years',src.contract['population'])
    order=src.evidence(r'start every training session with their specific group target exercise')
    src.evidence(r'hip thrusts in whatever order they preferred')
    context_proof=src.evidence(r'refrain from any other lower-body strength and/or power training')
    tempo=src.evidence(r'maximal intended velocity in the concentric phase')
    out=[]
    for arm,id,label,main_ref in [('SG','barbell_half_squat','하프 스쿼트 · 8주',main_squat),('DG','trap_bar_deadlift','트랩바 데드리프트 · 8주',sets)]:
        p=base(src,arm,label,int(m.group(1)),2,
          {'sex':'female','min_age':18,'age_min_exclusive':True,'max_age':None,'training_months':6,'healthy':True},
          {'other_lower_body_training':'excluded','other_training':'upper_body_and_endurance_permitted','supervision':'unsupervised','between_exercise_rest':{'seconds':int(rest.group(1))*60,'operator':'gte','status':'source_reported'},'warmup':{'status':'not_reported'},'accessory_per_leg_counting':'not_reported'},
          {'kind':'bounded_load_adjustment','target_reps':4,'increase_kg':[float(up.group(1)),float(up.group(2))],'decrease_kg':[float(down.group(1)),float(down.group(2))],'increase_timing':'not_reported','decrease_timing':'next_set'},
          {'min_day_difference':None,'status':'not_reported'},
          {'first':id,'accessory_order':'user_choice'},
          dict(weeks=schedule,sessions_per_week=schedule,population=pop,context=context_proof,progression=progression_proof,order=order))
        exercise(p,id,4,{'min':4,'max':4},{'kind':'initial_percent_1rm','percent':int(initial.group(1)),'reference_exercise':id,'ongoing_intensity':'adjusted_by_source_rule'},
          {'seconds':int(rest.group(1))*60,'operator':'gte'}, {'concentric':'maximal_intended_velocity','eccentric':'not_reported'},
          dict(id=main_ref,sets=sets,reps=sets,load=load_proof,rest=rest_proof,tempo=tempo))
        for id in ('dumbbell_bulgarian_split_squat','barbell_hip_thrust'):
            exercise(p,id,3,{'min':8,'max':8},{'kind':'rir','target':2},{'seconds':int(rest.group(1))*60,'operator':'gte'},
              {'concentric':'maximal_intended_velocity','eccentric':'not_reported'},
              dict(id=accessories,sets=accessories,reps=accessories,load=effort,rest=rest_proof,tempo=tempo))
        out.append(p)
    return out

def rm_programmes(src):
    is_low=src.pmc=='PMC5003312'
    popsec=src.contract['population']
    pop=src.evidence(r'(?:between the ages of|between the ages|between) 18 (?:-|and) 35',popsec)
    src.evidence(r'at least (?:3|three) times per week',popsec)
    src.evidence(r'(?:minimum of|at least) 1 year',popsec)
    schedule=src.evidence(r'three weekly sessions')
    src.evidence(r'(?:eight|8) weeks')
    interval=src.evidence(r'non-consecutive days')
    rests, rest_proof=src.match(r'(90 seconds|2 min) rest between sets')
    seconds=90 if rests.group(1).startswith('90') else 120
    movement=src.evidence(r'barbell military press, wide grip lat pulldown, seated cable row, barbell back squat, and?\s*machine leg press' if not is_low else r'barbell military press, wide grip lat pulldown, seated cable row, barbell back squat, machine leg press, and machine leg extension')
    sets=src.evidence(r'three sets' if is_low else r'Three sets of 8-12 repetition maximum')
    progression_proof=src.evidence(r'load was (?:subjectively )?adjusted for each exercise as needed on successive sets')
    failure=src.evidence(r'momentary concentric muscular failure')
    tempo=src.evidence(r'concentric action of approximately (?:one second|1 s) and an eccentric action of approximately (?:two seconds|2 s)')
    context=src.evidence(r'refrain from performing any additional resistance-type or high-intensity anaerobic training')
    ids=['barbell_bench_press','barbell_military_press','wide_grip_lat_pulldown','seated_cable_row','barbell_back_squat','machine_leg_press']
    if is_low: ids.append('machine_leg_extension')
    out=[]
    arms=[('LOW',25,35,30),('HIGH',8,12,10)] if is_low else [('TRAD',8,12,10)]
    for arm,minimum,maximum,initial_rm in arms:
        reps=src.evidence(str(minimum)+r'\s*-\s*'+str(maximum)+r' repetitions',popsec) if is_low else src.evidence(r'8-12 repetition maximum')
        initial=src.evidence(r'30-RM testing' if initial_rm==30 else r'10\s*-?\s*RM testing')
        p=base(src,arm,('낮은 부하' if arm=='LOW' else '전신 반복 최대 중량')+' · 8주',8,3,
          {'sex':'male','min_age':18,'max_age':35,'training_months':12,'healthy':True},
          {'other_resistance_or_high_intensity_anaerobic':'excluded','supervision':'directly_supervised','between_exercise_rest':{'status':'not_reported'},'warmup':{'status':'not_reported'},'initial_load':{'measurement':'exercise_specific_rm','reps':initial_rm}},
          {'kind':'adjust_to_rm_range','target':{'min':minimum,'max':maximum},'kg_step':None,'weekly_intent':'progressive_increase_within_target'},
          {'min_day_difference':2,'basis':'non_consecutive_days','minimum_hours':48 if not is_low else None},
          {'source_order':'not_explicitly_prescribed','presentation_order':'listed_order','user_choice_required':True},
          dict(weeks=schedule,sessions_per_week=schedule,population=pop,context=context,progression=progression_proof,spacing=interval))
        for id in ids:
            exercise(p,id,3,{'min':minimum,'max':maximum},
              {'kind':'repetition_maximum','failure':'momentary_concentric','initial_rm_test_reps':initial_rm},
              {'seconds':seconds,'operator':'eq'}, {'concentric_seconds':1,'eccentric_seconds':2,'approximate':True},
              dict(id=movement,sets=sets,reps=reps,load=initial,rest=rest_proof,tempo=tempo))
        # No unreported warm-up, between-exercise rest or exact kg increments are invented.
        out.append(p)
    return out

def extract(pmc, raw):
    src=Source(pmc,raw)
    return lower_body(src) if pmc=='PMC11140948' else rm_programmes(src)
