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
    def test_first_load_guidance_without_max_is_not_a_prescription(self):
        self.records = []
        inputs = novice.session_inputs(self.instance(), novice.EXERCISES[:2], [])
        self.assertEqual(len(inputs['load_selection']), 2)
        for item in inputs['load_selection']:
            self.assertEqual(item['status'], 'no_history')
            self.assertIsNone(item['input']['default_value'])
            self.assertIsNone(item['recommended_load_kg'])
            self.assertFalse(item['one_rm_test_required'])
            self.assertIn('seek_load_selection_help', item['actions'])

    def test_success_does_not_create_increment_or_copy_load(self):
        before = self.completed()
        inputs = novice.session_inputs(self.instance(), novice.EXERCISES[:2], [before])
        self.assertTrue(all(x['status'] == 'selected_plan_completed' for x in inputs['load_selection']))
        for item in inputs['load_selection']:
            self.assertFalse(item['automatic_progression'])
            self.assertIsNone(item['recommended_increment_kg'])
            self.assertIsNone(item['input']['default_value'])
            self.assertEqual(item['reference_events_sha256'], digest(before['events']))

    def test_changed_sets_not_averaged_into_next_load(self):
        prior = self.completed(changed=True)
        inputs = novice.session_inputs(self.instance(), novice.EXERCISES, [prior])
        self.assertEqual([x['status'] for x in inputs['load_selection']],
                         ['changed_or_incomplete', 'selected_plan_completed', 'no_history'])
        rows = inputs['previous_exercises'][0]['sets']
        self.assertEqual([r['actual']['weight_kg'] for r in rows], [35, 40, 40])
        self.assertIsNone(inputs['load_selection'][0]['recommended_load_kg'])

    def test_stopped_and_missing_not_failure_or_completed(self):
        prior = self.completed()
        prior['execution']['state'] = 'stopped'
        prior['execution']['sets'][0]['actual'] = None
        inputs = novice.session_inputs(self.instance(), novice.EXERCISES[:2], [prior])
        self.assertEqual(inputs['load_selection'][0]['status'], 'previous_session_not_completed')
        self.assertIsNone(inputs['previous_exercises'][0]['sets'][0]['actual'])

    def test_pain_navigation_and_frozen_selection_context(self):
        prior = self.completed(pain=True)
        snap = self.snapshot(d=2, history=[prior])
        context = snap['coaching']['load_selection_context']
        item = context['load_selection'][0]
        self.assertEqual(item['status'], 'pain_context_required')
        self.assertNotIn('enter_working_load', item['actions'])
        self.assertIn('review_current_discomfort', item['actions'])
        self.assertFalse(item['current_readiness_assessed'])
        frozen = copy.deepcopy(context)
        prior['execution']['sets'][0]['actual']['weight_kg'] = 999
        self.assertEqual(context, frozen)
        self.assertEqual(snap['coaching']['decisions'][0]['basis'], 'user_choice')

    def choice(self, prior, kind='increase'):
        return {novice.EXERCISES[0]: dict(kind=kind, reference_workout_id=prior['workout_id'],
                                        reference_events_sha256=digest(prior['events']))}

    def test_explicit_increase_persists_origin_and_user_delta(self):
        prior = self.completed()
        snap = prepare(self.instance(), 1, 2, self.at, [prior],
                       {novice.EXERCISES[0]: 42.5, novice.EXERCISES[2]: 40})
        result = novice.record_load_choices(snap, self.choice(prior), [prior])
        decision = result['coaching']['decisions'][0]
        self.assertEqual(decision['reference_load_kg'], 40)
        self.assertEqual(decision['selected_kg'], 42.5)
        self.assertEqual(decision['chosen_increment_kg'], 2.5)
        self.assertEqual(decision['basis'], 'user_choice')
        self.assertFalse(decision['automatically_applied'])
        self.assertEqual(result['session']['sets'][0]['weight_kg'], 42.5)

    def test_changed_pain_missing_or_stopped_cannot_claim_completion_increase(self):
        cases = [self.completed(changed=True), self.completed(pain=True), self.completed(), self.completed()]
        cases[2]['execution']['sets'][0]['actual'] = None
        cases[3]['execution']['state'] = 'stopped'
        for prior in cases:
            with self.subTest(status=prior['execution']['state']):
                snap = self.snapshot(d=2, history=[prior])
                with self.assertRaisesRegex(InvalidProgramme, 'LOAD_CHOICE_NOT_AVAILABLE'):
                    novice.record_load_choices(snap, self.choice(prior), [prior])

    def test_stale_choice_and_mismatched_value_rejected(self):
        prior = self.completed()
        choice = self.choice(prior)
        snap = self.snapshot(d=2, history=[prior])
        with self.assertRaisesRegex(InvalidProgramme, 'LOAD_CHOICE_VALUE_MISMATCH'):
            novice.record_load_choices(snap, choice, [prior])
        prior['events'].append({'id': 'later-correction'})
        with self.assertRaisesRegex(InvalidProgramme, 'STALE_LOAD_REFERENCE'):
            novice.record_load_choices(snap, choice, [prior])

    def test_store_rechecks_reference_inside_write_transaction(self):
        from backend import coaching_store
        from backend.workout_store import Conflict
        prior = self.completed()
        with tempfile.TemporaryDirectory() as directory:
            db = WorkoutStore(Path(directory)/'records.sqlite')
            coaching_store.save_instance(db, 'owner', 'instance', self.instance())
            coaching_store.start(db, 'owner', 'instance', 'prior', 1, 1, prior['snapshot'])
            with db.connect() as c:
                c.execute('UPDATE execution_workouts SET events=? WHERE owner=? AND id=?',
                          (json.dumps(prior['events']), 'owner', 'prior'))
            snap = prepare(self.instance(), 1, 2, '2026-10-19T09:00:00Z', [prior],
                           {novice.EXERCISES[0]: 42.5, novice.EXERCISES[2]: 40})
            novice.record_load_choices(snap, self.choice(prior), [prior])
            corrected = copy.deepcopy(prior['events'])
            corrected[0]['id'] = 'changed-after-selection'
            with db.connect() as c:
                c.execute('UPDATE execution_workouts SET events=? WHERE owner=? AND id=?',
                          (json.dumps(corrected), 'owner', 'prior'))
            with self.assertRaisesRegex(Conflict, 'STALE_LOAD_REFERENCE'):
                coaching_store.start(db, 'owner', 'instance', 'second', 1, 2, snap)
            with db.connect() as c:
                self.assertIsNone(c.execute('SELECT id FROM execution_workouts WHERE id=?', ('second',)).fetchone())

    def test_explicit_repeat_and_legacy_manual_path(self):
        prior = self.completed()
        snap = novice.record_load_choices(self.snapshot(d=2, history=[prior]), self.choice(prior, 'repeat'), [prior])
        self.assertEqual(snap['coaching']['decisions'][0]['chosen_increment_kg'], 0)
        plain = novice.record_load_choices(self.snapshot(), {}, [])
        self.assertEqual(plain['coaching']['load_choices'], {})
        self.assertNotIn('choice_kind', plain['coaching']['decisions'][0])

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
                    first = client.get(base+'/next-session', params={'at': fixture.at})
                    self.assertEqual(first.status_code, 200, first.text)
                    guidance = first.json()['session_inputs']['load_selection']
                    self.assertEqual([x['status'] for x in guidance], ['no_history', 'no_history'])
                    for item in guidance:
                        self.assertIsNone(item['recommended_load_kg'])
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
                            self.assertEqual([x['status'] for x in ready.json()['session_inputs']['load_selection']],
                                             ['selected_plan_completed', 'no_history'])
                        if w == 1 and d == 2:
                            guide = ready.json()['session_inputs']['load_selection'][0]
                            payload['initial_loads_kg'][novice.EXERCISES[0]] = 42.5
                            payload['load_choices'] = {novice.EXERCISES[0]: {
                                'kind': 'increase', 'reference_workout_id': guide['reference_workout_id'],
                                'reference_events_sha256': guide['reference_events_sha256']}}
                            stale = copy.deepcopy(payload)
                            stale['load_choices'][novice.EXERCISES[0]]['reference_events_sha256'] = 'stale'
                            self.assertEqual(client.post(base+'/workouts', json=stale).status_code, 422)
                        ex = post(base+'/workouts', payload)['execution']
                        if w == 1 and d == 2:
                            stored = db.get(user, wid)['execution']['coaching']['decisions'][0]
                            self.assertEqual(stored['chosen_increment_kg'], 2.5)
                            altered = copy.deepcopy(payload); altered['load_choices'] = {}
                            self.assertEqual(client.post(base+'/workouts', json=altered).status_code, 422)
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
