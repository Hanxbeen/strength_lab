"""Pure schema checks for the draft Phase 1 mascot design contract.

Visual similarity and Rive animation quality require separate human review.
"""
import json
import unittest
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[1] / 'docs' / 'LILA_PHASE1_MASTER.json'


class LilaPhase1ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(SPEC_PATH.read_text(encoding='utf-8'))

    def test_phase2_is_locked_before_approval(self):
        self.assertEqual(self.spec['phase'], 1)
        self.assertEqual(self.spec['approval_status'], 'pending_user_approval')
        self.assertFalse(self.spec['approval_gate']['rive_work_permitted'])
        self.assertIsNone(self.spec['appearance']['tuft']['selected'])

    def test_all_six_levels_in_order(self):
        self.assertEqual([x['id'] for x in self.spec['levels']], list(range(1, 7)))
        self.assertEqual(self.spec['levels'][1]['name'], '새싹 릴라')

    def test_no_props_for_levels_one_to_five(self):
        self.assertTrue(all(not x['props'] for x in self.spec['levels'][:-1]))
        self.assertEqual(set(self.spec['levels'][-1]['props']), {'crown', 'cape'})

    def test_character_signature(self):
        a = self.spec['appearance']
        self.assertEqual(a['fur']['base'], '#2A2A2A')
        self.assertEqual(a['skin']['base'], '#F3E7DB')
        self.assertTrue(a['fur']['no_green_cast'])
        self.assertEqual(a['face']['eyes']['count'], 2)
        self.assertEqual(a['face']['eyes']['default_shape'], 'vertical_oval')
        self.assertEqual(a['face']['nostrils']['count'], 2)
        self.assertEqual(a['face']['mouth'], 'never')

    def test_all_expressions_are_mouthless_and_have_ids(self):
        x = self.spec['expressions']
        self.assertEqual(x['mouth_always'], 'none')
        ids = [s['id'] for s in x['states']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('dizzy', ids)
        self.assertIn('repairing', ids)

    def test_source_image_not_misrepresented_as_committed(self):
        self.assertEqual(self.spec['reference']['status'], 'chat_only_not_in_repository')


if __name__ == '__main__':
    unittest.main()
