"""Bind introductory load claims to the same owner's immutable observations."""
from research_engine.entry_learning import POLICY
from research_engine.workout import require,timestamp
def validate(db,user,source,setup,at):
    if source.get('adapter_version')!='sbd-evidence-synthesis-v1':return
    origins=setup.get('starting_load_origins',{})
    requested={e for e,origin in origins.items() if origin=='self_reported_intro_trial'}
    refs=setup.get('entry_trial_references',{})
    require(isinstance(refs,dict) and set(refs)==requested,'ENTRY_LOAD_REFERENCES_REQUIRED')
    for exercise in requested:
        ref=refs[exercise]
        require(isinstance(ref,dict) and isinstance(ref.get('workout_id'),str) and isinstance(ref.get('event_id'),str),'ENTRY_LOAD_REFERENCE_INVALID')
        stored=db.get(user,ref['workout_id'])
        execution=stored['execution']
        require(execution.get('policy_version')==POLICY and execution['state']=='completed','ENTRY_LOAD_SESSION_NOT_COMPLETED')
        candidate=execution.get('candidate_working_loads',{}).get(exercise)
        require(candidate is not None and candidate['event_id']==ref['event_id'],'ENTRY_LOAD_CANDIDATE_UNAVAILABLE')
        require(timestamp(candidate['at'])<=timestamp(at),'ENTRY_LOAD_REFERENCE_FROM_FUTURE')
        require(timestamp(execution['termination']['at'])<=timestamp(at),'ENTRY_LOAD_REFERENCE_FROM_FUTURE')
        selected=setup['starting_loads_kg'][exercise]
        require(abs(candidate['weight_kg']-selected)<1e-8,'ENTRY_LOAD_REFERENCE_MISMATCH')
