"""Report supply gaps separately from executable option counts."""
SBD={'barbell_back_squat','barbell_bench_press','barbell_deadlift'}
FAMILIES={'petrizzo-2018-v1':'petrizzo2018','helms-2018-v1':'helms2018','metd-2021-v1':'metd2021'}

def report(rows):
    result={}
    for level in ('entry','foundation','trained','experienced'):
        selected=[r for r in rows if r['availability']['experience_context']==level]
        families=sorted({FAMILIES.get(r['definition']['adapter_version'],r['source_id']) for r in selected})
        complete=sum(SBD<=set(r['exercise_ids']) for r in selected)
        gaps=[]
        if level=='entry':gaps=['INDEPENDENT_TEACHING_MEDIA','FIRST_BARBELL_LOAD_PATH','ENTRY_TO_FOUNDATION_VALIDATION']
        elif not selected:gaps=['NO_EXECUTABLE_OPTION']
        elif not complete:gaps=['NO_COMPLETE_SBD_OPTION']
        if level!='entry' and len(families)<2:gaps.append('LIMITED_PROGRAMME_DIVERSITY')
        result[level]={'option_count':len(selected),'evidence_family_count':len(families),
            'evidence_families':families,'complete_sbd_option_count':complete,
            'supply_complete':False,'gaps':gaps,
            'effectiveness_validated':False,'deployed_execution_verified':False}
    result['entry']['guided_learning']={'endpoint':'/v3/entry/pathway','lesson_count':3,
        'in_person_instructor_required':True,'counted_as_training_routines':False}
    return {'scope':'current_product_supply_not_individual_suitability',
            'all_levels_complete':False,'levels':result}
