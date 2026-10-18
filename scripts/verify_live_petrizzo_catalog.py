"""Real Supabase HTTPS catalogue + local API; no production user records."""
import json
import tempfile
import os
import urllib.request
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.coaching_api import catalog
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore
from research_engine import petrizzo
from research_engine.core import digest

def verify():
    current=catalog()
    request=urllib.request.Request(os.environ['SUPABASE_URL'].rstrip('/')+'/rest/v1/rpc/coaching_programme_catalog_v3',
        data=b'{}',headers={'apikey':os.environ['SUPABASE_PUBLISHABLE_KEY'],'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=15) as response:legacy=json.load(response)
    assert all(x['definition']['adapter_version']!=petrizzo.ENGINE for x in legacy['items'])
    assert len([x for x in legacy['items'] if x['status']=='research_preview'])==4
    targets=[x for x in current['items'] if x['definition']['adapter_version']==petrizzo.ENGINE]
    assert len(targets)==2
    with tempfile.TemporaryDirectory() as directory:
        db=WorkoutStore(Path(directory)/'records.sqlite')
        app.dependency_overrides[owner]=lambda:'live-catalog-local-ledger'
        app.dependency_overrides[store]=lambda:db
        try:
            with patch.dict(os.environ,COACHING_PREVIEW_OWNER_IDS='live-catalog-local-ledger'):
                client=TestClient(app)
                def post(path,value):
                    r=client.post(path,json=value)
                    assert r.status_code==200,(path,r.status_code,r.text)
                    return r.json()
                response=client.get('/v3/research-programmes')
                assert response.status_code==200,response.text
                choices=sum(len(x['routine_options']) for x in response.json()['items'])
                for target in targets:
                    source=target['definition'];days=source['protocol']['days_per_week']
                    assert source==petrizzo.definition(days) and target['version']==digest(source)
                    local=json.loads((Path(__file__).resolve().parents[1]/f'data/research/coaching/petrizzo2018-four-lift-{days}d.json').read_text())
                    assert source==local
                    at='2026-10-18T09:00:00Z';base='/v3/programme-instances/'+source['id']
                    setup=dict(mode='user_selected_source',accept_scope_limits=True,accept_adaptations=True,
                        adaptation_id=petrizzo.ADAPTATION,rest_seconds=180,between_exercise_rest_seconds=300,
                        equipment_step_kg=2.5,warmup='Known user warm-up',
                        starting_loads_kg={e:40 for e in petrizzo.EXERCISES},
                        starting_load_origins={e:'known_working_load' for e in petrizzo.EXERCISES})
                    request=dict(source_id=source['id'],source_version=target['version'],arm=petrizzo.ARM,
                        created_at=at,profile=dict(age=25,independent_sbd=True,independent_ohp=True),
                        setup=setup,max_record_ids={})
                    assert post('/v3/programme-readiness',request)['can_create_instance']
                    post('/v3/programme-instances',dict(request,id=source['id']))
                    wid='live-'+str(days)
                    ex=post(base+'/workouts',dict(workout_id=wid,week=1,day=1,started_at=at,
                        initial_loads_kg={e:40 for e in source['protocol']['sessions'][0]['exercises']}))['execution']
                    sid=ex['next_set_id']
                    events=[dict(id='change',type='change_load',at=at,set_id=sid,value=35,unit='kg',reason='fatigue'),
                        dict(id='result',type='set_result',at=at,set_id=sid,reps=4),
                        dict(id='finish',type='finish',at=at,reason='time')]
                    for event in events:
                        ex=post('/v2/workouts/'+wid+'/events',dict(expected_revision=ex['revision'],event=event))['execution']
                    ready=client.get(base+'/next-session',params={'at':'2026-10-20T09:00:00Z'})
                    assert ready.status_code==200,ready.text
                    refs=ready.json()['session_inputs']['load_selection']
                    assert refs[0]['status']=='previous_session_not_completed'
                    assert refs[1]['registered_starting_load_kg']==40
                    assert refs[1]['exercise_id']==petrizzo.EXERCISES[-1]
                    saved=db.get('live-catalog-local-ledger',wid)['execution']
                    assert saved['sets'][0]['actual']['weight_kg']==35
        finally:app.dependency_overrides.clear()
    return dict(real_https_catalog=True,legacy_v3_preserved=True,active_definitions=len(current['items']),routine_options=choices,
        added_definitions=len(targets),local_api_with_real_catalog=True,
        deployed_auth_verified=False,production_user_writes=False)
if __name__=='__main__':print(json.dumps(verify()))
