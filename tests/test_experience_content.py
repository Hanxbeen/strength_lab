"""Adversarial content contracts: no source mutation, invented measurements or unsafe actions."""
import copy
import json
import unittest
from unittest.mock import patch
from backend.experience_content import exercise_guide, guidance, session_analysis, programme_analysis
from backend.workout_result import project
from backend.workout_store import replay
from research_engine.core import digest
from tests import test_routine_selection as routine_fixtures
from tests import test_entry_learning as learning_fixtures

class ExperienceContentTests(unittest.TestCase):
    def setUp(self):
        self.fixture=routine_fixtures.RoutineSelectionTests()
        self.fixture.setUp()
    def tearDown(self):
        self.fixture.tearDown()
    def test_all_catalogue_content_has_no_source_mutation(self):
        before=copy.deepcopy(self.fixture.items)
        rows=self.fixture.client.get('/v3/routines').json()['routines']
        self.assertEqual(len(rows),10)
        guide_ids=set()
        for row in rows:
            content=row['experience']
            self.assertEqual(content['source_version'],row['source_version'])
            self.assertEqual(content['arm'],row['arm'])
            self.assertEqual([x['exercise_id'] for x in content['exercises']],row['exercise_ids'])
            guide_ids.update(row['exercise_ids'])
            for guide in content['exercises']:
                self.assertTrue(guide['available'])
                for key in ['setup','steps','mistakes','breathing_and_bracing','stop_guidance','sources']:
                    self.assertTrue(guide[key])
                self.assertTrue(guide['demonstration']['url'].startswith('https://'))
            chart=content['research_chart']
            if not chart['available']:
                self.assertTrue(chart['reason'])
                self.assertEqual(chart['points'],[])
            self.assertIsNone(content['completion']['effect_achievement_rate'])
        self.assertEqual(len(guide_ids),5)
        self.assertEqual(before,self.fixture.items)

    def test_guidance_actions_resolve_but_do_not_authorize_state(self):
        content=guidance()
        self.assertEqual(len(content['scenarios']),10)
        for scenario in content['scenarios']:
            for action in scenario['action_ids']:
                self.assertIn(action,content['actions'])
        content['scenarios'][0]['text']='mutated'
        self.assertNotEqual(guidance()['scenarios'][0]['text'],'mutated')
        self.assertFalse(exercise_guide('unknown_lift')['available'])

    def test_no_reopen_or_pain_resume_recommendation(self):
        rows=self.fixture.client.get('/v3/routines').json()['routines']
        row=next(x for x in rows if x['arm']=='FOUR_LIFT')
        req,daily=self.fixture.request_for(row['definition'],row['arm'])
        self.fixture.post('/v3/programme-instances',dict(req,id='pain'))
        ex=self.fixture.post('/v3/programme-instances/pain/workouts',dict(
            workout_id='pain',week=1,day=1,started_at=req['created_at'],**daily))['execution']
        self.assertIn('set_result',ex['experience']['available_action_ids'])
        event=dict(id='p',type='change_load',at=req['created_at'],set_id=ex['next_set_id'],value=30,unit='kg',reason='pain')
        ex=self.fixture.post('/v2/workouts/pain/events',dict(expected_revision=0,event=event))['execution']
        self.assertEqual(ex['state'],'paused')
        self.assertNotIn('resume',ex['experience']['available_action_ids'])
        ex=self.fixture.post('/v2/workouts/pain/events',dict(expected_revision=1,
            event=dict(id='stop',type='interrupt',at=req['created_at'],reason='user_interruption')))['execution']
        self.assertEqual(ex['experience']['available_action_ids'],['reason_record'])
        self.assertFalse(ex['experience']['closed_session_reopen_available'])
        result=self.fixture.client.get('/v2/workouts/pain/result').json()
        self.assertEqual(result['analysis']['performed']['recorded_sets'],0)
        self.assertTrue(result['analysis']['differences']['unrecorded_set_ids'])

    def test_entry_completed_and_pain_have_analysis_without_mastery(self):
        f=learning_fixtures.EntryLearningTests();f.setUp()
        events=[f.observation(lid) for lid in ('squat','push','hinge')]
        events += [f.trial(),dict(id='finish',type='finish',at=f.at,outcome='completed')]
        complete=project(dict(workout_id='learn',execution=replay(f.snapshot,events),events=events))
        self.assertEqual(complete['analysis']['scope'],'learning_session')
        self.assertEqual(complete['analysis']['candidate_loads']['barbell_back_squat']['weight_kg'],10)
        self.assertFalse(complete['technique_verified'])
        painful=[f.observation('squat'),f.trial(),dict(f.observation('push'),pain=True)]
        stopped=project(dict(workout_id='learn',execution=replay(f.snapshot,painful),events=painful))
        self.assertEqual(stopped['analysis']['candidate_loads'],{})
        self.assertEqual(stopped['experience']['available_action_ids'],[])
        self.assertIn('seek_qualified_help',stopped['analysis']['next_actions'])

    def test_entry_catalogue_enriched_even_when_raw_provider_is_replaced(self):
        f=learning_fixtures.EntryLearningTests();f.setUp()
        item=dict(source_id=f.source['id'],version=digest(f.source),status='research_preview',definition=f.source)
        original=copy.deepcopy(item)
        with patch('backend.entry_learning_api.catalogue',return_value=dict(items=[item])):
            direct=self.fixture.client.get('/v3/entry/learning-paths').json()['items'][0]
            listed=self.fixture.client.get('/v3/routines').json()['learning_paths'][0]
            self.assertEqual(direct['experience'],listed['experience'])
            self.assertEqual(len(direct['experience']['exercises']),3)
        self.assertEqual(item,original)

    def test_actual_repetitions_ranges_and_missing_data_are_not_effect(self):
        execution={'state':'stopped','sets':[
            {'id':'fixed','reps':{'min':5,'max':5},'actual':{'weight_kg':40,'reps':3},'changes':[]},
            {'id':'amrap','reps':{'min':None,'max':None},'actual':{'weight_kg':40,'reps':3},'changes':[]},
            {'id':'missing','reps':{'min':5,'max':5},'actual':None,'changes':[]} ]}
        result=session_analysis(execution)
        self.assertEqual(result['differences']['repetition_differences'],[{'set_id':'fixed','target':5,'actual':3}])
        self.assertEqual(result['differences']['unrecorded_set_ids'],['missing'])
        self.assertIsNone(result['effect_achievement_rate'])

    def test_programme_series_missing_is_gap_and_zero_is_observation(self):
        results=[{'state':'stopped','sets':[
            {'exercise_id':'squat','actual':None},
            {'exercise_id':'bench','actual':{'weight_kg':50,'reps':0}}]}]
        payload={'history_inputs':[{'workout_id':'w1'}],'training':{},'lifts':[
            {'exercise_id':'squat','status':'not_measured'},{'exercise_id':'bench','status':'conditions_unknown'}]}
        out=programme_analysis(payload,results)
        groups=out['charts']['sessions'][0]['exercises']
        self.assertIsNone(groups['squat']['observed_volume_kg_reps'])
        self.assertEqual(groups['bench']['observed_volume_kg_reps'],0)
        self.assertEqual(groups['squat']['missing_sets'],1)
        self.assertIsNone(out['charts']['growth_slope'])
        self.assertTrue(all(x['explanation'] for x in out['measurement_statuses']))


    def test_closed_reason_record_and_historical_evaluation_revision(self):
        row=next(x for x in self.fixture.client.get('/v3/routines').json()['routines'] if x['arm']=='FOUR_LIFT')
        req,daily=self.fixture.request_for(row['definition'],row['arm'])
        self.fixture.post('/v3/programme-instances',dict(req,id='history'))
        ex=self.fixture.post('/v3/programme-instances/history/workouts',dict(
            workout_id='history',week=1,day=1,started_at=req['created_at'],**daily))['execution']
        sid=ex['next_set_id']
        for event in [dict(id='actual',type='set_result',at=req['created_at'],set_id=sid,reps=3),
                      dict(id='finish',type='finish',at=req['created_at'],reason='time')]:
            ex=self.fixture.post('/v2/workouts/history/events',dict(expected_revision=ex['revision'],event=event))['execution']
        first=self.fixture.post('/v3/programme-instances/history/evaluations',
            dict(id='first',at=req['created_at'],outcome='stopped'))
        event=dict(id='why',type='reason_record',at='2026-10-28T09:00:00Z',target_event_id='actual',
            response=dict(schema_version=1,response_status='unknown',reason_codes=[]))
        self.assertIn('actual',ex['experience']['reason_record_target_event_ids'])
        self.assertIn('reason_record',ex['experience']['available_action_ids'])
        after=self.fixture.post('/v2/workouts/history/events',dict(expected_revision=ex['revision'],event=event))['execution']
        self.assertEqual(after['state'],'stopped')
        self.assertNotIn('resume',after['experience']['available_action_ids'])
        reloaded=self.fixture.client.get('/v3/programme-instances/history').json()['evaluations'][0]
        self.assertEqual(first,reloaded)
        with self.fixture.db.connect() as connection:
            stored=json.loads(connection.execute("SELECT payload FROM coaching_evaluations WHERE id='first'").fetchone()[0])
        self.assertNotIn('analysis',stored)
        # Repeating the original evaluation returns its original revision, not the current event list.
        retried=self.fixture.post('/v3/programme-instances/history/evaluations',
            dict(id='first',at=req['created_at'],outcome='stopped'))
        self.assertEqual(retried,first)


    def test_legacy_education_uses_its_own_endpoint_and_supported_events(self):
        from research_engine import entry_practice
        source=entry_practice.catalogue()
        snapshot=entry_practice.create('squat-pattern',source['version'],
            {'age':25,'current_pain':False},{'in_person_instructor':True,'equipment_checked':True},
            '2026-10-18T09:00:00Z')
        result=replay(snapshot,[])
        content=result['experience']
        self.assertEqual(content['event_endpoint'],'/v3/entry/practices/{workout_id}/events')
        self.assertEqual(content['guidance']['lesson']['id'],'squat-pattern')
        self.assertNotIn('load_trial',content['available_action_ids'])
        self.assertNotIn('interrupt',content['available_action_ids'])
        self.assertEqual(session_analysis(result)['candidate_loads'],{})

if __name__=='__main__':
    unittest.main()

