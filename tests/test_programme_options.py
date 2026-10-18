import json
import unittest
from pathlib import Path
from backend.programme_options import options
from research_engine.core import digest

class ProgrammeOptionTests(unittest.TestCase):
    def load(self, name):
        source = json.loads((Path(__file__).resolve().parents[1] /
            'data/research/coaching' / (name + '.json')).read_text())
        return {'source_id': source['id'], 'version': digest(source),
                'status': 'research_preview', 'definition': source}

    def test_all_current_choices_preserve_sources(self):
        counts = {'novice-sbd-choice': (1,24), 'pilot2018-sbd': (1,30),
                  'helms2018': (2,23), 'metd2021': (3,18)}
        total = 0
        for name, (arms, sessions) in counts.items():
            item = self.load(name)
            original = digest(item)
            rows = options(item, True)
            self.assertEqual(len(rows), arms)
            self.assertEqual(digest(item), original)
            total += len(rows)
            for row in rows:
                self.assertEqual(row['training_sessions'], sessions)
                self.assertEqual(row['source_version'], item['version'])
                self.assertIsNone(row['difficulty_rank'])
                self.assertFalse(row['scientific_approval'])
                self.assertTrue(row['start_requires_readiness_check'])
        self.assertEqual(total, 7)

    def test_rpe_arm_does_not_publish_percent_as_prescribed_load(self):
        rows = options(self.load('helms2018'), True)
        rpe = next(x for x in rows if x['arm']=='RPEG')
        for session in rpe['sessions']:
            self.assertNotIn('table_percent_1rm', session['target'])
        self.assertNotIn('barbell_deadlift', rpe['exercise_ids'])
        self.assertEqual(rows[0]['sessions'][6]['target']['conditional_progression'], True)

    def test_unreleased_access_and_novice_missing_first_load(self):
        row = options(self.load('novice-sbd-choice'), False)[0]
        self.assertFalse(row['can_request_start'])
        self.assertEqual(row['access'], 'not_released')
        self.assertIn('initial_loads_kg', row['required_inputs'])
        self.assertIsNone(row['arm_prescription']['automatic_load_adjustment'])

    def test_metd_keeps_effort_and_backoff_dependency(self):
        rows = {r['arm']:r for r in options(self.load('metd2021'), True)}
        self.assertEqual(rows['MAX_BOFF']['arm_prescription']['backoff']['percent_actual_single_load'],80)
        self.assertEqual(rows['AMRAP']['arm_prescription']['reps']['rpe'],[9,9.5])
        self.assertNotIn('initial_rpe_loads_kg', rows['AMRAP']['required_inputs'])
        self.assertIn('initial_rpe_loads_kg', rows['MAX']['required_inputs'])

    def test_per_mapping_is_visible_without_mutating_source(self):
        item = self.load('pilot2018-sbd')
        before = digest(item)
        row = options(item, True)[0]
        review = row['source_mapping_review']
        self.assertEqual(review['total_encoded_sets'], 515)
        self.assertEqual(review['substituted_set_count'], 22)
        self.assertEqual(review['substituted_row_count'], 12)
        self.assertEqual(review['affected_session_count'], 4)
        self.assertEqual(review['source_set_counts']['Front squat'], 22)
        self.assertFalse(review['exact_source_replication'])
        self.assertFalse(review['working_sets_verified'])
        self.assertFalse(review['front_squat_from_back_squat_1rm_supported'])
        self.assertEqual(digest(item), before)
        self.assertTrue(all(x['source_exercise_id']=='barbell_front_squat'
                            and x['applied_exercise_id']=='barbell_back_squat'
                            for x in review['substitutions']))
