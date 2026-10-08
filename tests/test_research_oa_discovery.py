import unittest
from scripts.research_oa_discovery import eligible
class OpenAccessSelectionTests(unittest.TestCase):
    def test_acute_study_excluded(self):
        self.assertFalse(eligible({'title':'Acute effects of bench press rest intervals'}))
    def test_sbd_longitudinal_candidate(self):
        self.assertTrue(eligible({'title':'Eight weeks of squat training'}))
    def test_review_excluded(self):
        self.assertFalse(eligible({'title':'Squat training systematic review'}))
if __name__=='__main__':unittest.main()
