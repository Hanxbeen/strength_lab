import json
import unittest
from scripts.build_zourdos_review import build, OUTPUT, SBD
from research_engine import programme_dispatch


class ZourdosReviewTests(unittest.TestCase):
    def test_transcription_and_arm_accounting(self):
        draft = build()
        self.assertEqual(json.loads(OUTPUT.read_text()), draft)
        rows = {r['id']: r for r in draft['protocol']['rows']}
        self.assertEqual(len(rows), 42)
        for name, arm in draft['protocol']['arms'].items():
            sessions = arm['sessions']
            self.assertEqual(len(sessions), 18)
            used = [rows[key] for s in sessions for key in s['row_ids']]
            self.assertEqual(len({r['id'] for r in used}), 42)
            self.assertEqual(sum(r['sets'] for r in used), 150)
            self.assertEqual([s['kind'] for s in sessions[:3]], list(name))
            for week in range(1, 7):
                for e, frequency in zip(SBD, [3, 3, 1]):
                    self.assertEqual(sum(r['training_week'] == week and r['exercise_id'] == e for r in used), frequency)

    def test_unknowns_are_not_turned_into_prescriptions(self):
        rows = build()['protocol']['rows']
        unresolved = [r for r in rows if r['load']['kind'] == 'individually_adjusted']
        self.assertEqual(len(unresolved), 10)
        for r in unresolved:
            self.assertIsNone(r['load']['percent'])
            self.assertIsNone(r['load']['adjustment_rule'])
            self.assertEqual(r['load']['reported_change_options_lb'], [0, 5, 10])
        for r in rows:
            self.assertIsNone(r['training_rest_seconds'])
            if r['session_kind'] == 'S':
                self.assertEqual(r['reps']['kind'], 'to_failure')
                self.assertIsNone(r['reps']['value'])
                self.assertIsNone(r['reps']['rpe_target'])
        self.assertEqual([r['load']['percent'] for r in rows if r['session_kind'] == 'P' and r['exercise_id'] == SBD[0]], [80, 80, 85, 85, 90, 90])
        self.assertTrue(any(c['id'] == 'power_week_typo' for c in build()['conflicts']))

    def test_research_draft_is_rejected_by_runtime(self):
        draft = build()
        self.assertFalse(draft['executable'])
        self.assertFalse(draft['scientific_approval'])
        self.assertNotIn('adapter_version', draft)
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_SOURCE'):
            programme_dispatch.validate_source(draft)
