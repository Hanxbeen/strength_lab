import unittest
from backend.routine_coverage import report

def option(level,engine,lifts):
    return dict(availability=dict(experience_context=level),definition=dict(adapter_version=engine),
                source_id=engine,exercise_ids=lifts)
SBD=['barbell_back_squat','barbell_bench_press','barbell_deadlift']
class CoverageTests(unittest.TestCase):
    def test_variations_not_independent_evidence_or_completion(self):
        result=report([option('foundation','petrizzo-2018-v1',SBD)]*2)
        self.assertEqual(result['levels']['foundation']['option_count'],2)
        self.assertEqual(result['levels']['foundation']['evidence_family_count'],1)
        self.assertFalse(result['all_levels_complete'])
        self.assertFalse(result['levels']['entry']['guided_learning']['counted_as_training_routines'])
    def test_squat_bench_not_sbd_and_empty_not_available(self):
        result=report([option('trained','helms-2018-v1',SBD[:2])])
        self.assertIn('NO_COMPLETE_SBD_OPTION',result['levels']['trained']['gaps'])
        self.assertIn('NO_EXECUTABLE_OPTION',result['levels']['experienced']['gaps'])
