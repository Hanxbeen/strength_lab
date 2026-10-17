"""Read real RPC data, then exercise local API against a disposable ledger.

Needs SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY. Never mutates remote DB or
claims deployed-server authentication verification. No keys are printed.
"""
import json
import os
import tempfile
import urllib.request
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.coaching_api import catalog
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore
from research_engine.core import digest
from research_engine.novice import ARM, ADAPTATION, EXERCISES, validate_source


def verify():
    current = catalog()  # Real HTTP RPC, including source hash and adapter validation.
    item = next(x for x in current['items'] if x['source_id'] == 'novice-sbd-choice-v1')
    expected = json.loads((Path(__file__).resolve().parents[1]/'data/research/coaching/novice-sbd-choice.json').read_text())
    assert item['definition'] == expected and item['version'] == digest(expected)
    validate_source(item['definition'])
    legacy_counts = {}
    for name in ('coaching_source_catalog', 'coaching_programme_catalog', 'coaching_programme_catalog_v2'):
        request = urllib.request.Request(os.environ['SUPABASE_URL'].rstrip('/')+'/rest/v1/rpc/'+name,
            data=b'{}', headers={'apikey': os.environ['SUPABASE_PUBLISHABLE_KEY'], 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=15) as response:
            result = json.load(response)
        assert all(x['source_id'] != item['source_id'] for x in result['items'])
        legacy_counts[name] = len(result['items'])
    with tempfile.TemporaryDirectory() as directory:
        db = WorkoutStore(Path(directory)/'verification.sqlite')
        user = 'catalog-verification-local-only'
        app.dependency_overrides[owner] = lambda: user
        app.dependency_overrides[store] = lambda: db
        try:
            with patch.dict(os.environ, COACHING_PREVIEW_OWNER_IDS=user):
                client = TestClient(app)
                def post(path, value):
                    response = client.post(path, json=value)
                    assert response.status_code == 200, (path, response.status_code, response.text)
                    return response.json()
                at = '2026-10-16T09:00:00Z'
                setup = dict(mode='user_selected_source', accept_scope_limits=True, accept_adaptations=True,
                    adaptation_id=ADAPTATION, rest_seconds=180, between_exercise_rest_seconds=300,
                    equipment_step_kg=2.5, warmup='Explicit user choice')
                create = dict(id='live-definition', source_id=item['source_id'], source_version=item['version'], arm=ARM,
                    created_at=at, profile=dict(age=25, independent_sbd=True), setup=setup, max_record_ids={})
                with patch.dict(os.environ, COACHING_PREVIEW_OWNER_IDS=''):
                    assert client.post('/v3/programme-instances', json=create).status_code == 403
                ready = post('/v3/programme-readiness', {k:v for k,v in create.items() if k!='id'})
                assert ready['can_create_instance'] and ready['recommendation_status']=='not_assessed'
                post('/v3/programme-instances', create)
                base = '/v3/programme-instances/live-definition'
                ex = post(base+'/workouts', dict(workout_id='first', week=1, day=1, started_at=at,
                    initial_loads_kg={e:40 for e in EXERCISES[:2]}))['execution']
                sid = ex['next_set_id']
                for event in [dict(id='change',type='change_load',at=at,set_id=sid,value=35,unit='kg',reason='fatigue'),
                              dict(id='result',type='set_result',at='2026-10-16T09:01:00Z',set_id=sid,reps=4),
                              dict(id='end',type='finish',at='2026-10-16T09:02:00Z',reason='time')]:
                    ex = post('/v2/workouts/first/events', dict(expected_revision=ex['revision'],event=event))['execution']
                response = client.get(base+'/next-session', params={'at':'2026-10-18T09:00:00Z'})
                assert response.status_code == 200, response.text
                ref = response.json()['session_inputs']['previous_exercises'][0]
                assert ref['sets'][0]['weight_kg']==40 and ref['sets'][0]['actual']['weight_kg']==35
                assert ref['sets'][0]['actual']['reps']==4 and ref['automatic_load_kg'] is None
                assert ref['status']=='previous_session_not_completed'
        finally:
            app.dependency_overrides.clear()
    return dict(active_definitions=len(current['items']), source_version=item['version'],
                legacy_rpc_row_counts=legacy_counts, real_rpc_definition_match=True,
                local_api_with_real_catalogue=True, remote_user_records_written=False,
                deployed_server_verified=False)


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False))
