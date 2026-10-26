import copy,unittest
from research_engine import entry_learning as e
from research_engine.core import digest,InvalidProgramme
class EntryLearningTests(unittest.TestCase):
    def setUp(self):
        self.at='2026-10-26T09:00:00Z';self.source=e.definition()
        self.snapshot=e.create(self.source,digest(self.source),dict(age=25,current_pain=False,exercise_restriction=False),
            dict(equipment_checked=True,accept_self_report_limits=True),self.at)
    def observation(self,lid):
        return dict(id=lid,type='practice_observation',at=self.at,lesson_id=lid,reps=5,control='controlled',effort='easy',pain=False)
    def trial(self,lid='squat'):
        return dict(self.observation(lid),id='load-'+lid,type='load_trial',value=10,unit='kg',
            lift_instruction_reviewed=True,equipment_checked=True,safety_support_ready=True,light_implement_selected=True)
    def test_completed_learning_preserves_candidate_not_rm_or_mastery(self):
        events=[self.observation(lid) for lid in ('squat','push','hinge')]
        events+=[self.trial(),dict(id='finish',type='finish',at=self.at,outcome='completed')]
        result=e.replay(self.snapshot,events)
        self.assertEqual(result['state'],'completed')
        self.assertEqual(result['candidate_working_loads'][e.SBD[0]]['weight_kg'],10)
        self.assertEqual(result['max_records'],[]);self.assertFalse(result['training_unlocked'])
        self.assertFalse(result['technique_verified']);self.assertIsNone(result['assessment'])
    def test_pain_or_uncertain_control_stops_and_invalidates_candidates(self):
        for change in (dict(pain=True),dict(control='uncertain')):
            events=[self.observation('squat'),self.trial()]
            events.append(dict(self.observation('push'),**change))
            result=e.replay(self.snapshot,events)
            self.assertEqual(result['state'],'stopped');self.assertEqual(result['candidate_working_loads'],{})
            with self.assertRaises(InvalidProgramme):e.replay(self.snapshot,events+[self.observation('hinge')])
    def test_missing_setup_and_incomplete_practice_are_not_success(self):
        with self.assertRaises(InvalidProgramme):e.replay(self.snapshot,[self.trial()])
        trial=self.trial();trial.pop('safety_support_ready')
        with self.assertRaises(InvalidProgramme):e.replay(self.snapshot,[self.observation('squat'),trial])
        with self.assertRaises(InvalidProgramme):e.replay(self.snapshot,[dict(id='f',type='finish',at=self.at,outcome='completed')])
    def test_open_rest_interrupted_is_unknown_not_hour_of_recovery(self):
        events=[dict(id='r',type='rest_start',at=self.at),dict(id='i',type='interrupt',at='2026-10-26T10:01:00Z')]
        result=e.replay(self.snapshot,events)
        self.assertEqual(result['state'],'stopped');self.assertIsNone(result['rests'][0]['elapsed_seconds'])
    def test_later_hard_trial_invalidates_earlier_easy_candidate(self):
        events=[self.observation('squat'),self.trial(),dict(self.trial(),id='hard',effort='hard')]
        self.assertEqual(e.replay(self.snapshot,events)['candidate_working_loads'],{})
    def test_lb_and_idempotent_replay(self):
        trial=dict(self.trial(),unit='lb',value=20)
        events=[self.observation('squat'),trial,trial]
        result=e.replay(self.snapshot,events)
        self.assertEqual(result['revision'],2)
        self.assertAlmostEqual(result['load_trials'][0]['weight_kg'],9.0718474)
    def test_source_tamper_rejected(self):
        changed=copy.deepcopy(self.source);changed['first_load']['max_trials_per_lift']=99
        with self.assertRaises(InvalidProgramme):e.create(changed,digest(changed),{}, {},self.at)

class EntryLearningApiTests(unittest.TestCase):
    def test_owner_scoped_learning_record_and_catalogue_discovery(self):
        from tests.test_routine_selection import RoutineSelectionTests
        from unittest.mock import patch
        case=RoutineSelectionTests();case.setUp()
        source=e.definition()
        item=dict(source_id=e.ID,version=digest(source),status='research_preview',definition=source)
        try:
            with patch('backend.entry_learning_api.catalogue',return_value=dict(items=[item])):
                data=case.client.get('/v3/routines').json()
                self.assertEqual(data['coverage']['entry']['state'],'self_guided_learning')
                self.assertTrue(data['supply_audit']['all_levels_data_ready'])
                self.assertFalse(data['supply_audit']['all_levels_complete'])
                self.assertEqual(data['coverage']['entry']['option_count'],0)
                at='2026-10-26T09:00:00Z'
                payload=dict(id='learn',source_id=e.ID,source_version=digest(source),started_at=at,
                    profile=dict(age=25,current_pain=False,exercise_restriction=False),
                    setup=dict(equipment_checked=True,accept_self_report_limits=True))
                result=case.post('/v3/entry/learning-sessions',payload)
                self.assertEqual(result['execution']['state'],'active')
                event=dict(id='squat',type='practice_observation',at=at,lesson_id='squat',reps=5,
                           control='controlled',effort='easy',pain=False)
                case.post('/v3/entry/learning-sessions/learn/events',dict(expected_revision=0,event=event))
                case.post('/v3/entry/learning-sessions/learn/events',dict(expected_revision=0,event=dict(event,id='stale')),409)
                case.user='other'
                self.assertEqual(case.client.get('/v3/entry/learning-sessions/learn').status_code,404)
                case.user='normal'
                self.assertEqual(case.client.get('/v3/entry/learning-sessions/learn').json()['execution']['revision'],1)
                result=case.db.reconcile_inactivity('normal','learn',now=__import__('datetime').datetime(2026,10,26,11,tzinfo=__import__('datetime').timezone.utc))
                self.assertEqual(result['execution']['state'],'stopped')
                case.post('/v3/entry/learning-sessions/learn/events',dict(expected_revision=2,event=dict(event,id='resume')),422)
        finally:case.tearDown()

    def test_intro_load_reference_requires_matching_owner_event_and_mass(self):
        from tests.test_routine_selection import RoutineSelectionTests
        from backend.entry_load_reference import validate
        case=RoutineSelectionTests();case.setUp()
        try:
            f=EntryLearningTests();f.setUp()
            events=[f.observation(lid) for lid in ('squat','push','hinge')]
            events+=[f.trial(),dict(id='finish',type='finish',at=f.at,outcome='completed')]
            case.db.create('normal','intro',f.snapshot)
            for index,event in enumerate(events):case.db.append('normal','intro',index,event)
            source=dict(adapter_version='sbd-evidence-synthesis-v1')
            setup=dict(starting_load_origins={e.SBD[0]:'self_reported_intro_trial'},
                starting_loads_kg={e.SBD[0]:10},
                entry_trial_references={e.SBD[0]:dict(workout_id='intro',event_id='load-squat')})
            validate(case.db,'normal',source,setup,f.at)
            bad=copy.deepcopy(setup);bad['starting_loads_kg'][e.SBD[0]]=20
            with self.assertRaises(InvalidProgramme):validate(case.db,'normal',source,bad,f.at)
            bad=copy.deepcopy(setup);bad['entry_trial_references']={}
            with self.assertRaises(InvalidProgramme):validate(case.db,'normal',source,bad,f.at)
            with self.assertRaises(KeyError):validate(case.db,'other',source,setup,f.at)
        finally:case.tearDown()
