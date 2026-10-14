import copy
import unittest
import test_workout_execution as fixtures
from research_engine.workout import replay
from research_engine.core import InvalidProgramme

class ReasonRecordsTests(unittest.TestCase):
    def setUp(self):
        fixtures.WorkoutTests.setUpClass()
        self.fixture=fixtures.WorkoutTests();self.fixture.setUp()
        self.snapshot=self.fixture.snapshot
        self.change=self.fixture.event('change_load',1,set_id=self.fixture.first,value=70,unit='kg',reason='other')
    def report(self, id='reason1', second=2, codes=None, status='answered', supersedes=None):
        return dict(id=id,type='reason_record',at=self.fixture.event('x',second)['at'],
                    target_event_id=self.change['id'],supersedes_event_id=supersedes,
                    response=dict(schema_version=1,reason_codes=codes or ['effort_insufficient'],response_status=status))
    def test_multiple_self_reports_pause_without_overwriting_actual(self):
        event=self.report(codes=['effort_insufficient','pain_discomfort'])
        result=replay(self.snapshot,[self.change,event])
        self.assertEqual(result['state'],'paused')
        self.assertEqual(result['sets'][0]['changes'][0]['reason'],'other')
        self.assertIsNone(result['sets'][0]['actual'])
        self.assertIn('PAIN_REPORTED',[g['code'] for g in result['guides']])
    def test_correction_after_finish_retains_prior_event_and_no_auto_resume(self):
        first=self.report(codes=['pain_discomfort'])
        finish=self.fixture.event('finish',3,reason='time')
        correction=self.report(id='reason2',second=4,codes=['equipment'],supersedes='reason1')
        events=[self.change,first,finish,correction]
        before=copy.deepcopy(events)
        result=replay(self.snapshot,events)
        self.assertEqual(events,before)
        self.assertEqual(result['state'],'stopped')
        self.assertEqual(result['reason_reports'][self.change['id']]['reason_codes'],['equipment'])
        self.assertEqual(result['revision'],4)
    def test_stale_correction_and_unknown_target_rejected(self):
        first=self.report()
        with self.assertRaisesRegex(InvalidProgramme,'REASON_REVISION'):
            replay(self.snapshot,[self.change,first,self.report(id='reason2',second=3)])
        with self.assertRaisesRegex(InvalidProgramme,'REASON_TARGET'):
            replay(self.snapshot,[first])
    def test_declined_is_not_inferred_fatigue(self):
        report=self.report(status='declined');report['response']['reason_codes']=[]
        result=replay(self.snapshot,[self.change,report,report])
        self.assertEqual(result['revision'],2)
        self.assertEqual(result['reason_reports'][self.change['id']]['response_status'],'declined')

if __name__=='__main__':unittest.main()
