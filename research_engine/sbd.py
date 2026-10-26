"""Internal SBD adaptation, with source rows and product choices kept separate."""
import copy
from .core import digest,number
from .workout import require,timestamp,max_record,POLICY
from .coaching import rounded
from .execution_facts import pain_reported
from .per_provenance import row_mapping, mapping_review, SOURCE_IDS, source_labels

ENGINE='sbd-template-v1'
EXERCISES=('barbell_back_squat','barbell_bench_press','barbell_deadlift')

def validate_source(source):
    require(source.get('id') in ('pilot2018-per-template-v1','pilot2018-per-source-labels-v1') and source.get('adapter_version')==('per-source-labels-v1' if source_labels(source) else ENGINE),'UNSUPPORTED_SOURCE')
    require(source.get('scientific_approval') is False and source.get('review_status')=='source_extracted','UNSUPPORTED_REVIEW_STATE')
    require(source.get('publication_status')=='internal_preview','SOURCE_SUSPENDED')
    protocol=source.get('protocol',{})
    require(digest(protocol)==source.get('protocol_sha256'),'PROTOCOL_HASH_MISMATCH')
    require(protocol.get('weeks')==10 and protocol.get('days_per_week')==3,'INVALID_SCHEDULE')
    require(source.get('exercises')==(list(EXERCISES)+['barbell_front_squat'] if source_labels(source) else list(EXERCISES)) and bool(source.get('adaptations')),'PROVENANCE_REQUIRED')
    if source_labels(source):
        require(source.get('max_reference_exercises')==list(EXERCISES),'INVALID_MAX_REFERENCE_EXERCISES')
    sessions=protocol.get('sessions',[])
    require([(s['week'],s['day']) for s in sessions]==[(w,d) for w in range(1,11) for d in range(1,4)],'INCOMPLETE_SCHEDULE')
    for session in sessions:
        require(bool(session['rows']),'EMPTY_SESSION')
        for row in session['rows']:
            require(row.get('numbered_sbd_anchor') in EXERCISES,'EXERCISE_OUT_OF_SCOPE')
            require(row.get('source_exercise') in ('Squat','Front squat','Bench press','Deadlift'),'UNKNOWN_SOURCE_EXERCISE')
            require(number(row.get('percent_1rm'),1,100),'INVALID_PERCENT')
            require(type(row.get('reps')) is int and 1<=row['reps']<=20,'INVALID_REPS')
            require(type(row.get('sets')) is int and 1<=row['sets']<=10,'INVALID_SETS')
            require(bool(row.get('source',{}).get('cells')),'SOURCE_LOCATOR_REQUIRED')
            if source_labels(source):
                require(row.get('exercise_id')==SOURCE_IDS[row['source_exercise']],'SOURCE_LABEL_MISMATCH')
                ref=row.get('load_reference',{})
                require(ref.get('exercise_id')==row['numbered_sbd_anchor'] and ref.get('basis')=='verified_xls_formula','SOURCE_FORMULA_REQUIRED')
                require(ref.get('source_sha256')==source['source_sha256'] and bool(ref.get('formula')),'SOURCE_FORMULA_REQUIRED')

def make_instance(source,arm,profile,records,setup,at):
    validate_source(source);timestamp(at)
    labelled=source_labels(source)
    require(arm==('PER_SOURCE_LABELS' if labelled else 'PER_ADAPTED'),'UNKNOWN_ARM')
    require(setup.get('mode')=='user_selected_source' and setup.get('accept_scope_limits') is True,'SCOPE_ACKNOWLEDGEMENT_REQUIRED')
    require(setup.get('exercise_mapping')==('source_labels_verified_formula_v1' if labelled else 'numbered_sbd_adaptation_v1') and setup.get('accept_adaptations') is True,'EXPLICIT_SBD_ADAPTATION_REQUIRED')
    require(number(profile.get('age'),18,100) and profile.get('independent_sbd') is True,'EXPERIENCED_ADULT_REVIEW_SCOPE_REQUIRED')
    if labelled:
        require(profile.get('sex')=='male' and number(profile.get('training_years'),2,80)
                and number(profile.get('powerlifting_years'),1,80)
                and profile.get('independent_front_squat') is True
                and profile.get('rpe_familiarized') is True
                and profile.get('prior_moderate_high_load_training') is True,'PER_EXPERIENCE_SCOPE_REQUIRED')
        require(setup.get('accept_source_discrepancy') is True,'SOURCE_DISCREPANCY_ACKNOWLEDGEMENT_REQUIRED')
    values=[max_record(r) for r in records]
    require(len(values)==3 and {r['exercise_id'] for r in values}==set(EXERCISES),'SBD_MAX_REFERENCES_REQUIRED')
    for r in values:require(r['kind']=='measured' and timestamp(r['measured_at'])<=timestamp(at),'MEASURED_BASELINE_REQUIRED')
    for key in ('rest_seconds','between_exercise_rest_seconds'):
        require(type(setup.get(key)) is int and 1<=setup[key]<=3600,'EXPLICIT_REST_REQUIRED')
    require(isinstance(setup.get('warmup'),str) and bool(setup['warmup'].strip()),'EXPLICIT_WARMUP_REQUIRED')
    rounded(100,setup.get('equipment_step_kg'))
    return {'engine_version':source['adapter_version'],'source':copy.deepcopy(source),'arm':arm,'profile':copy.deepcopy(profile),
        'max_records':values,'setup':copy.deepcopy(setup),'created_at':at,
        'programme_version':digest({'source':source,'arm':arm,'engine':ENGINE}),'adaptations':copy.deepcopy(source['adaptations'])}

def prepare(instance,week,day,at,history,initial_loads=None):
    require(type(week) is int and type(day) is int and 1<=week<=10 and 1<=day<=3,'INVALID_SESSION')
    require(timestamp(at)>=timestamp(instance['created_at']),'BEFORE_INSTANCE')
    require(not initial_loads,'PERCENTAGE_TEMPLATE_REQUIRES_NO_RPE_START_LOADS')
    target=instance['source']['protocol']['sessions'][(week-1)*3+day-1]
    maxima={r['exercise_id']:r for r in instance['max_records']};setup=instance['setup'];rows=[]
    for group,r in enumerate(target['rows'],1):
        labelled=source_labels(instance['source'])
        eid=r['exercise_id'] if labelled else r['numbered_sbd_anchor']
        reference=r['load_reference']['exercise_id'] if labelled else eid
        maximum=maxima[reference];raw=maximum['weight_kg']*r['percent_1rm']/100
        weight=rounded(raw,setup['equipment_step_kg']);require(weight<=2000,'INVALID_MASS')
        for n in range(1,r['sets']+1):
            rows.append({'id':f'{eid}:r{group}:s{n}','exercise_id':eid,'set':len(rows)+1,
                'reps':{'min':r['reps'],'max':r['reps']},'load':{'kind':'percentage_1rm','percent':r['percent_1rm'],
                'baseline_max_kg':maximum['weight_kg'],'max_record_id':maximum['id']},'weight_kg':weight,'unrounded_weight_kg':raw,
                'tempo':{'kind':'not_encoded'},'rest_after':{'operator':'eq','seconds':setup['rest_seconds'],'basis':'user_choice'},
                'source_exercise':r['source_exercise'],'source_row':copy.deepcopy(r['source']),'set_role':r['role'],
                'exercise_mapping':setup['exercise_mapping'],
                'source_mapping':row_mapping(r, source_labels(instance['source']))})
    rows[-1]['rest_after']=None
    previous=next((h for h in reversed(history) if h['day']==day),None)
    reference=None
    if previous:
        reference={'workout_id':previous['workout_id'],'week':previous['week'],
            'sets':[{k:copy.deepcopy(r.get(k)) for k in ('id','exercise_id','weight_kg','reps','actual','status','changes','reason_reports')}
                    for r in previous['execution']['sets']], 'rests':copy.deepcopy(previous['execution']['rests']),
            'limitation':'Previous same programme day; intensity, repetitions and set count can differ. Not an automatic load recommendation.'}
    return {'schema_version':2,'policy_version':POLICY,'programme_id':instance['source']['id'],
        'programme_version':instance['programme_version'],'source':copy.deepcopy(instance['source']),
        'definition':{'progression':{'kind':'coaching_source'},'provenance':{}},
        'session':{'sets':rows,'user_choices':{'between_exercise_rest_seconds':setup['between_exercise_rest_seconds']}},
        'max_records':copy.deepcopy(instance['max_records']),'started_at':at,
        'coaching':{'engine':instance['source']['adapter_version'],'week':week,'day':day,'arm':instance['arm'],'target':copy.deepcopy(target),
            'guidance':copy.deepcopy(instance['source'].get('guidance',{})),
            'adaptations':copy.deepcopy(instance['adaptations']),'previous_same_day':reference,'decisions':[],
            'source_mapping_review':mapping_review(instance['source']),
            'equipment_step_kg':setup['equipment_step_kg'],'setup':copy.deepcopy(setup),'instance_created_at':instance['created_at']}}

def enrich(snapshot,result):
    result=copy.deepcopy(result)
    result['coaching']={**copy.deepcopy(snapshot['coaching']),'scientific_approval':False,
        'application':'source_template_with_explicit_product_adaptation','growth_prediction':None,
        'next_set_decision':{'status':'pain_context_required' if pain_reported(result['sets']) else 'user_choice',
            'factor':None,'automatically_applied':False,'basis':'product_policy'}}
    result['summary']['growth_prediction']=None
    result['summary']['volume_load_kg_reps']=sum(r['actual']['reps']*r['actual']['weight_kg'] for r in result['sets'] if r['actual'])
    result['summary']['source_comparison']='Actual vs selected adapted plan; not research-effect attainment.'
    return result
