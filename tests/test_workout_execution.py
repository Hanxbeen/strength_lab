import copy
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from research_engine.core import compile_programme, InvalidProgramme
from research_engine.workout import create_workout, replay, kg
from backend.workout_store import WorkoutStore, Conflict

ROOT = Path(__file__).resolve().parents[1]

class WorkoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads((ROOT/'data/research/engine/seed-definitions.json').read_text())
        cls.bundle = compile_programme(next(p for p in catalog['programmes'] if p['programme_id']=='PMC11140948-SG')['definition'])

    def setUp(self):
        self.profile = {'sex':'female','age':25,'training_months':12,'healthy':True}
        self.setup = {'exercise_order':['barbell_half_squat','dumbbell_bulgarian_split_squat','barbell_hip_thrust'],
                      'warmup':'user choice','between_exercise_rest_seconds':180,'split_squat_reps':'per_leg',
                      'max_record_ids':{'barbell_half_squat':'max1'},
                      'working_loads_kg':{'dumbbell_bulgarian_split_squat':10,'barbell_hip_thrust':40}}
        self.record = {'id':'max1','exercise_id':'barbell_half_squat','value':100,'unit':'kg',
                       'kind':'measured','measured_at':'2026-10-10T10:00:00Z'}
        self.snapshot = self.create()
        self.first = self.snapshot['session']['sets'][0]['id']

    def create(self):
        return create_workout(self.bundle, self.bundle['sessions'][0]['id'], self.profile, self.setup,
                              [self.record], '2026-10-11T10:00:00Z')

    def event(self, kind, second=0, **kw):
        at = datetime(2026,10,11,10,tzinfo=timezone.utc)+timedelta(seconds=second)
        return {'id':kind+str(second),'type':kind,'at':at.isoformat(),**kw}

    def result(self, second=10, **kw):
        return self.event('set_result',second,set_id=self.first,reps=kw.pop('reps',4),**kw)

    def test_pain_change_pauses_until_explicit_resume(self):
        change=self.event('change_load',1,set_id=self.first,value=80,unit='kg',reason='pain')
        value=replay(self.snapshot,[change])
        self.assertEqual(value['state'],'paused')
        self.assertIn('PAIN_REPORTED',[g['code'] for g in value['guides']])
        self.assertNotIn('NEXT_SET',[g['code'] for g in value['guides']])
        with self.assertRaisesRegex(InvalidProgramme,'SET_NOT_AVAILABLE'):
            replay(self.snapshot,[change,self.result()])
        value=replay(self.snapshot,[change,self.event('resume',2),self.result(reps=2,reason='fatigue')])
        self.assertNotIn('SOURCE_DECREASE_RANGE',[g['code'] for g in value['guides']])

    def test_interrupted_rest_is_not_interset_shortfall(self):
        value=replay(self.snapshot,[self.result(),self.event('finish',20,reason='time')])
        self.assertEqual(value['summary']['rest_shortfall_seconds'],0)
        self.assertNotIn('REST_SHORTFALL',[g['code'] for g in value['guides']])
        self.assertGreater(value['rests'][0]['shortfall_seconds'],0)

    def test_pending_is_unknown_and_finish_is_confirmed(self):
        summary=replay(self.snapshot,[])['summary']
        self.assertIsNone(summary['minimum_reps_completion_percent'])
        self.assertEqual(summary['minimum_reps_completion_bounds_percent'],[0,100])
        summary=replay(self.snapshot,[self.event('finish',1,reason='time')])['summary']
        self.assertEqual(summary['minimum_reps_completion_percent'],0)
        self.assertEqual(summary['unknown_sets'],0)

    def test_legacy_results_preserved_and_only_finish_allowed(self):
        from research_engine.workout_legacy_v1 import replay as old_replay
        old=copy.deepcopy(self.snapshot);old['policy_version']='execution-ledger-v1'
        self.assertEqual(replay(old,[])['summary'],old_replay(old,[])['summary'])
        with tempfile.TemporaryDirectory() as folder:
            db=WorkoutStore(Path(folder)/'old.sqlite');db.create('a','old',old)
            with self.assertRaisesRegex(Conflict,'LEGACY'):
                db.append('a','old',0,self.result())
            out=db.append('a','old',0,self.event('finish',1,reason='time'))
            self.assertEqual(out['execution']['state'],'stopped')
            self.assertTrue(out['execution']['legacy_read_only'])

    def test_max_snapshot_survives_edits(self):
        self.record['value']=150
        self.assertEqual(replay(self.snapshot,[])['sets'][0]['weight_kg'],85)
        self.assertEqual(self.snapshot['max_records'][0]['id'],'max1')

    def test_exact_variant_required(self):
        self.record['exercise_id']='barbell_back_squat'
        with self.assertRaisesRegex(InvalidProgramme,'MISMATCH'):self.create()

    def test_estimated_max_not_silently_measured(self):
        self.record['kind']='estimated'
        with self.assertRaisesRegex(InvalidProgramme,'MEASURED'):self.create()

    def test_unit_conversion(self):
        self.assertAlmostEqual(kg(220.46226218487757,'lb'),100)
        for value in (float('nan'),float('inf'),True,-1):
            with self.assertRaises(InvalidProgramme):kg(value,'kg')

    def test_changed_weight_keeps_target(self):
        events=[self.event('change_load',1,set_id=self.first,value=80,unit='kg',reason='fatigue'),self.result(reps=3,reason='fatigue')]
        value=replay(self.snapshot,events)
        chart=value['summary']['chart'][0]
        self.assertEqual((chart['target_weight_kg'],chart['actual_weight_kg'],chart['reps_shortfall']),(85,80,1))
        self.assertEqual(len(value['sets'][0]['changes']),1)

    def test_shortfall_needs_reason(self):
        with self.assertRaisesRegex(InvalidProgramme,'SHORTFALL'):replay(self.snapshot,[self.result(reps=0)])

    def test_rest_cannot_complete_early(self):
        with self.assertRaisesRegex(InvalidProgramme,'REST_NOT_ELAPSED'):
            replay(self.snapshot,[self.result(),self.event('rest_end',100,outcome='completed')])

    def test_skipped_rest_stays_visible(self):
        value=replay(self.snapshot,[self.result(),self.event('rest_end',70,outcome='skipped')])
        self.assertEqual(value['rest_count'],1)
        self.assertEqual(value['rests'][0]['elapsed_seconds'],60)
        self.assertEqual(value['summary']['rest_shortfall_seconds'],120)

    def test_pause_does_not_erase_recovery(self):
        value=replay(self.snapshot,[self.result(),self.event('pause',30),self.event('resume',250),self.event('rest_end',251,outcome='completed')])
        self.assertEqual(value['rests'][0]['elapsed_seconds'],241)

    def test_no_set_during_rest(self):
        with self.assertRaisesRegex(InvalidProgramme,'SET_NOT_AVAILABLE'):
            replay(self.snapshot,[self.result(),self.event('skip_set',20,set_id=self.snapshot['session']['sets'][1]['id'],reason='time')])

    def test_finish_preserves_unattempted(self):
        value=replay(self.snapshot,[self.result(),self.event('finish',50,reason='time')])
        self.assertEqual(value['state'],'stopped')
        self.assertEqual(value['summary']['not_attempted_sets'],9)
        self.assertIsNone(value['summary']['chart'][1]['actual_reps'])
        self.assertEqual(value['rests'][0]['outcome'],'interrupted')

    def test_terminal_rejects_new_events(self):
        with self.assertRaisesRegex(InvalidProgramme,'WORKOUT_CLOSED'):
            replay(self.snapshot,[self.event('finish',1,reason='time'),self.result()])

    def test_pain_pauses_and_does_not_prescribe_lower_weight(self):
        value=replay(self.snapshot,[self.result(reps=2,reason='pain')])
        self.assertEqual(value['state'],'paused')
        codes=[g['code'] for g in value['guides']]
        self.assertIn('PAIN_REPORTED',codes);self.assertNotIn('SOURCE_DECREASE_RANGE',codes)
        self.assertIsNotNone(value['active_rest'])

    def test_order_and_time(self):
        with self.assertRaisesRegex(InvalidProgramme,'SET_ORDER'):replay(self.snapshot,[self.event('skip_set',1,set_id='invalid',reason='time')])
        with self.assertRaisesRegex(InvalidProgramme,'TIME_ORDER'):replay(self.snapshot,[self.result(),self.event('pause',1)])

    def test_duplicate_is_idempotent(self):
        result=self.result()
        self.assertEqual(replay(self.snapshot,[result,result])['revision'],1)
        changed={**result,'reps':5}
        with self.assertRaisesRegex(InvalidProgramme,'ID_CONFLICT'):replay(self.snapshot,[result,changed])

    def test_full_workout_has_no_final_rest(self):
        events=[];second=0
        for row in self.snapshot['session']['sets']:
            second+=1
            events.append(self.event('set_result',second,set_id=row['id'],reps=row['reps']['min'],rir=2))
            if row != self.snapshot['session']['sets'][-1]:
                second+=180;events.append(self.event('rest_end',second,outcome='completed'))
        events.append(self.event('finish',second+1))
        value=replay(self.snapshot,events)
        self.assertEqual(value['state'],'completed');self.assertEqual(value['rest_count'],9)
        self.assertEqual(value['summary']['minimum_reps_completion_percent'],100)
        self.assertIsNone(value['active_rest']);self.assertIsNone(value['summary']['growth_prediction'])

    def test_store_isolation_conflict_retry_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.sqlite';db=WorkoutStore(path)
            db.register_max('a',self.record);self.assertEqual(db.maxes('b'),[])
            db.create('a','w1',self.snapshot)
            with self.assertRaises(KeyError):db.get('b','w1')
            db.append('a','w1',0,self.result())
            self.assertEqual(db.append('a','w1',0,self.result())['execution']['revision'],1)
            with self.assertRaises(Conflict):db.append('a','w1',0,self.event('pause',20))
            self.assertEqual(WorkoutStore(path).get('a','w1')['execution']['revision'],1)
            with self.assertRaises(InvalidProgramme):db.append('a','w1',1,self.event('rest_end',30,outcome='completed'))
            self.assertEqual(db.get('a','w1')['execution']['revision'],1)

if __name__=='__main__': unittest.main()
