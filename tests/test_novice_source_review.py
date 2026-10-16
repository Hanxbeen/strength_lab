"""Data-integrity and non-release regression tests, not scientific validation."""
import json
import unittest
from pathlib import Path
from research_engine import programme_dispatch

PATH = Path(__file__).resolve().parents[1] / 'data/research/coaching/reviews/novice-sbd-20261016.json'


class NoviceSourceReviewTests(unittest.TestCase):
    def setUp(self):
        self.review = json.loads(PATH.read_text())
        self.mao, self.petrizzo = self.review['reports']

    def test_midpoint_measurement_not_baseline_reuse(self):
        p = self.mao
        self.assertEqual(p['training_weeks'], 8)
        self.assertEqual(p['load_percent_by_training_week'], [70, 72.5, 75, 75] * 2)
        self.assertEqual(p['load_reference_by_training_week'], ['baseline_1rm'] * 4 + ['midpoint_1rm'] * 4)
        self.assertEqual(p['remeasure_1rm_after_training_week'], 4)

    def test_distinct_set_rest_designs_preserved(self):
        arms = self.mao['arms']
        self.assertEqual(arms['TS'], dict(sets=4, reps=10, rest_seconds=120))
        self.assertEqual(arms['RR'], dict(sets=8, reps=5, rest_seconds=51))
        self.assertEqual(arms['TS']['sets'] * arms['TS']['reps'], 40)
        self.assertEqual(arms['RR']['sets'] * arms['RR']['reps'], 40)
        # 3*120 != 7*51: preserve actual reported seconds, not manufactured equality.
        self.assertEqual((arms['TS']['sets']-1)*arms['TS']['rest_seconds'], 360)
        self.assertEqual((arms['RR']['sets']-1)*arms['RR']['rest_seconds'], 357)

    def test_denominators_and_noncompleters_preserved(self):
        p = self.petrizzo
        c = p['completion']
        self.assertEqual(c['completed_12_weeks'], 24)
        self.assertEqual(c['stalled'] + c['injury_withdrawal'], 16)
        self.assertEqual(c['completed_12_weeks'] + c['stalled'] + c['injury_withdrawal'], p['population']['analyzed'])
        self.assertEqual(p['population']['analyzed'] + c['other_excluded_dropouts'], p['population']['recruited'])
        self.assertNotEqual(c['completed_12_weeks']/p['population']['recruited'], 0.6)

    def test_no_silent_sbd_replacement_or_prescription(self):
        self.assertNotIn('barbell_deadlift', self.mao['exercise_order'])
        self.assertIn('barbell_bent_over_row', self.mao['exercise_order'])
        self.assertIn('barbell_standing_shoulder_press', self.petrizzo['original_exercise_ids'])
        self.assertIsNone(self.petrizzo['progression']['fixed_increment_kg'])
        self.assertFalse(self.mao['incomplete_set_rule']['automatic_application_in_product'])
        self.assertFalse(self.review['adoption_decisions']['automatic_sbd_prescription'])

    def test_review_does_not_enter_runtime(self):
        self.assertFalse(self.review['executable'])
        self.assertFalse(self.review['scientific_approval'])
        self.assertIsNone(self.review['runtime_adapter'])
        for value in [self.review] + self.review['reports']:
            with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_SOURCE'):
                programme_dispatch.validate_source(value)
