import copy
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore
from backend.programme_readiness import preview
from research_engine import novice
from research_engine.core import digest, InvalidProgramme
from research_engine.programme_dispatch import make_instance, prepare
from research_engine.workout import replay


class NoviceTests(unittest.TestCase):
    def setUp(self):
        self.source = novice.definition()
        self.at = '2026-10-16T09:00:00Z'
        self.profile = {'age': 25, 'independent_sbd': True}
        self.setup = {'mode': 'user_selected_source', 'accept_scope_limits': True, 'accept_adaptations': True,
            'adaptation_id': novice.ADAPTATION, 'rest_seconds': 180, 'between_exercise_rest_seconds': 300,
            'equipment_step_kg': 2.5, 'warmup': 'Explicit progressive warm-up chosen outside the app'}
        self.records = [dict(id=e, exercise_id=e, value=v, unit='kg', kind='estimated', measured_at=self.at)
                        for e, v in zip(novice.EXERCISES, (100, 60, 140))]
    def request(self):
        return dict(source_id=self.source['id'], source_version=digest(self.source), arm=novice.ARM,
            created_at=self.at, profile=self.profile, setup=self.setup,
            max_record_ids={r['exercise_id']: r['id'] for r in self.records})
    def instance(self):
        return make_instance(self.source, novice.ARM, self.profile, self.records, self.setup, self.at)
    def snapshot(self, w=1, d=1, history=None):
        eids = self.source['protocol']['sessions'][(w-1)*2+d-1]['exercises']
        return prepare(self.instance(), w, d, self.at, history or [], {e: 40 for e in eids})
    def completed(self, changed=False, pain=False):
        snap = self.snapshot(); events = []; at = datetime.fromisoformat(self.at.replace('Z', '+00:00'))
        def send(kind, **data):
            nonlocal at
            at += timedelta(seconds=300)
            events.append(dict(id=str(len(events)), type=kind, at=at.isoformat(), **data))
        for n, row in enumerate(snap['session']['sets']):
            if n: send('rest_end', outcome='completed')
            if n == 0 and (changed or pain):
                send('change_load', set_id=row['id'], value=35, unit='kg', reason='pain' if pain else 'fatigue')
                if pain: send('resume')
            send('set_result', set_id=row['id'], reps=5)
        send('finish')
        return dict(workout_id='prior', week=1, day=1, snapshot=snap, execution=replay(snap, events), events=events)
    def test_definition_counts_and_no_ohp_substitution(self):
        novice.validate_source(self.source)
        self.assertEqual(len(self.source['protocol']['sessions']), 24)
        counts = {e: 0 for e in novice.EXERCISES}
        for w in range(1, 13):
            for d in (1, 2):
                for r in self.snapshot(w, d)['session']['sets']: counts[r['exercise_id']] += 1
        self.assertEqual(list(counts.values()), [72, 36, 12])
        candidate = json.loads((Path(__file__).resolve().parents[1]/'data/research/coaching/novice-sbd-choice.json').read_text())
        self.assertEqual(candidate, self.source)
    def test_no_inferred_load_from_max_or_history(self):
        with self.assertRaisesRegex(InvalidProgramme, 'EXPLICIT_SESSION_LOADS_REQUIRED'):
            prepare(self.instance(), 1, 1, self.at, [], {})
        original = self.snapshot()
        self.records[0]['value'] = 200
        self.assertEqual(self.snapshot()['session'], original['session'])
        with self.assertRaisesRegex(InvalidProgramme, 'EXPLICIT_SESSION_LOADS_REQUIRED'):
            prepare(self.instance(), 1, 2, self.at, [self.completed()], {})
    def test_no_max_registration_required_for_manual_loads(self):
        self.records = []
        request = self.request()
        result = preview(self.source, request, [], True)
        self.assertEqual(result['input_status'], 'ready')
        self.assertEqual(self.instance()['max_records'], [])
        self.assertEqual(self.snapshot()['session']['sets'][0]['weight_kg'], 40)
    def test_previous_exercise_not_same_weekday_and_reasons_preserved(self):
        prior = self.completed(changed=True)
        snap = self.snapshot(d=2, history=[prior])
        refs = snap['coaching']['previous_exercises']
        self.assertEqual(refs[0]['status'], 'changed_or_incomplete')
        self.assertEqual(refs[0]['sets'][0]['actual']['weight_kg'], 35)
        self.assertEqual(refs[0]['sets'][0]['weight_kg'], 40)
        self.assertEqual(refs[1]['status'], 'no_history')
        self.assertIsNone(refs[0]['automatic_load_kg'])
        prior['events'].append({'id': 'audit-only'})
        self.assertNotEqual(novice.previous_reference([prior], novice.EXERCISES[0])['history_events_sha256'], refs[0]['history_events_sha256'])
    def test_completion_is_not_progression_approval(self):
        prior = self.completed()
        r = novice.previous_reference([prior], novice.EXERCISES[0])
        self.assertEqual(r['status'], 'selected_plan_completed'); self.assertIsNone(r['automatic_load_kg'])
        prior['execution']['sets'][1]['actual'] = None
        self.assertEqual(novice.previous_reference([prior], novice.EXERCISES[0])['status'], 'changed_or_incomplete')
    def test_pain_blocks_completion_label(self):
        prior = self.completed(pain=True)
        self.assertEqual(novice.previous_reference([prior], novice.EXERCISES[0])['status'], 'pain_context_required')
    def test_no_release_or_mutated_source(self):
        r = preview(self.source, self.request(), self.records, False)
        self.assertFalse(r['can_create_instance']); self.assertEqual(r['recommendation_status'], 'not_assessed')
        self.assertEqual(r['session_start_inputs'], ['initial_loads_kg_for_session_exercises'])
        self.source['publication_status'] = 'published'
        with self.assertRaises(InvalidProgramme): self.instance()
    def test_invalid_scope_and_loads_are_rejected(self):
        for loads in ({novice.EXERCISES[0]: -1, novice.EXERCISES[1]: 40},
                      {novice.EXERCISES[0]: 41, novice.EXERCISES[1]: 40}):
            with self.assertRaises(InvalidProgramme): prepare(self.instance(), 1, 1, self.at, [], loads)
        with self.assertRaises(InvalidProgramme): self.snapshot(d=3)
        self.profile['independent_sbd'] = False
        with self.assertRaises(InvalidProgramme): self.instance()


class NoviceAPITests(unittest.TestCase):
    def test_optional_baseline_early_close_has_no_growth_claim(self):
        f = NoviceTests(); f.setUp(); f.records = []
        with tempfile.TemporaryDirectory() as directory:
            db = WorkoutStore(Path(directory)/'records.sqlite')
            app.dependency_overrides[owner] = lambda: 'internal'
            app.dependency_overrides[store] = lambda: db
            try:
                entry = dict(source_id=f.source['id'], version=digest(f.source), status='research_preview', definition=f.source)
                with patch('backend.coaching_api.catalog', return_value={'schema_version': 3, 'items': [entry]}), patch.dict(os.environ, COACHING_PREVIEW_OWNER_IDS='internal'):
                    client = TestClient(app)
                    def post(url, data):
                        r=client.post(url,json=data);self.assertEqual(r.status_code,200,r.text);return r.json()
                    post('/v3/programme-instances', dict(f.request(), id='no-max'))
                    post('/v3/programme-instances/no-max/workouts',dict(workout_id='one',week=1,day=1,started_at=f.at,
                        initial_loads_kg={e:40 for e in novice.EXERCISES[:2]}))
                    post('/v2/workouts/one/events',dict(expected_revision=0,event=dict(id='stop',type='finish',at=f.at,reason='time')))
                    eid=novice.EXERCISES[0]
                    db.register_max('internal',dict(id='after',exercise_id=eid,value=100,unit='kg',kind='measured',measured_at=f.at))
                    result=post('/v3/programme-instances/no-max/evaluations',dict(id='end',at=f.at,outcome='stopped',
                        post_max_record_ids={eid:'after'},comparison_conditions={eid:'same'}))
                    self.assertEqual(result['lifts'][0]['status'],'baseline_not_recorded')
                    self.assertIsNone(result['lifts'][0]['baseline']);self.assertIsNone(result['total_delta_kg'])
            finally:app.dependency_overrides.clear()
    def test_full_lifecycle_retries_scope_and_estimated_baseline(self):
        fixture = NoviceTests(); fixture.setUp()
        source = fixture.source; user = 'novice-internal'
        with tempfile.TemporaryDirectory() as directory:
            db = WorkoutStore(Path(directory)/'records.sqlite')
            app.dependency_overrides[owner] = lambda: user
            app.dependency_overrides[store] = lambda: db
            try:
                entry = dict(source_id=source['id'], version=digest(source), status='research_preview', definition=source)
                with patch('backend.coaching_api.catalog', return_value={'schema_version': 3, 'items': [entry]}), patch.dict(os.environ, COACHING_PREVIEW_OWNER_IDS=user):
                    client = TestClient(app)
                    for r in fixture.records: db.register_max(user, r)
                    def post(url, data):
                        r = client.post(url, json=data); self.assertEqual(r.status_code, 200, r.text); return r.json()
                    request = dict(fixture.request(), id='prototype')
                    with patch.dict(os.environ, COACHING_PREVIEW_OWNER_IDS=''):
                        self.assertEqual(client.post('/v3/programme-instances', json=request).status_code, 403)
                    post('/v3/programme-instances', request)
                    base = '/v3/programme-instances/prototype'
                    for session in source['protocol']['sessions']:
                        w, d = session['week'], session['day']
                        at = datetime.fromisoformat(fixture.at.replace('Z', '+00:00')) + timedelta(days=(w-1)*7+(d-1)*2)
                        wid = 'w'+str(w)+'d'+str(d)
                        payload = dict(workout_id=wid, week=w, day=d, started_at=at.isoformat(),
                                       initial_loads_kg={e: 40 for e in session['exercises']})
                        if w == 1 and d == 2:
                            ready = client.get(base+'/next-session', params={'at': at.isoformat()})
                            self.assertEqual(ready.status_code, 200, ready.text)
                            self.assertEqual(ready.json()['session_inputs']['previous_exercises'][0]['workout_id'], 'w1d1')
                            self.assertEqual(ready.json()['session_inputs']['required_field'], 'initial_loads_kg')
                        ex = post(base+'/workouts', payload)['execution']
                        self.assertEqual(post(base+'/workouts', payload)['execution'], ex)
                        bad = copy.deepcopy(payload); bad['initial_loads_kg'][novice.EXERCISES[0]] = 45
                        self.assertEqual(client.post(base+'/workouts', json=bad).status_code, 422)
                        bad = dict(payload, initial_rpe_loads_kg={novice.EXERCISES[0]: 40})
                        self.assertEqual(client.post(base+'/workouts', json=bad).status_code, 422)
                        if w == 1 and d == 2:
                            self.assertEqual(ex['coaching']['previous_exercises'][0]['workout_id'], 'w1d1')
                        def send(kind, **data):
                            nonlocal at, ex
                            at += timedelta(seconds=300)
                            ex = post('/v2/workouts/'+wid+'/events', dict(expected_revision=ex['revision'],
                                event=dict(id=str(ex['revision']), type=kind, at=at.isoformat(), **data)))['execution']
                        while ex['next_set_id']:
                            if ex['state'] == 'resting': send('rest_end', outcome='completed')
                            send('set_result', set_id=ex['next_set_id'], reps=5)
                        send('finish')
                    at += timedelta(days=1)
                    eid = novice.EXERCISES[0]
                    db.register_max(user, dict(id='post', exercise_id=eid, value=120, unit='kg', kind='measured', measured_at=at.isoformat()))
                    result = post(base+'/evaluations', dict(id='end', at=at.isoformat(), outcome='completed',
                        post_max_record_ids={eid: 'post'}, comparison_conditions={eid: 'same'}))
                    self.assertEqual(result['training']['closed_sessions'], 24)
                    self.assertEqual(result['training']['recorded_sets'], 120)
                    self.assertEqual(result['lifts'][0]['status'], 'baseline_estimated')
                    self.assertIsNone(result['total_delta_kg'])
            finally:
                app.dependency_overrides.clear()
