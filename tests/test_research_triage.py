import unittest
from scripts.research_triage import classify
class TriageTests(unittest.TestCase):
    def test_missing_fulltext_blocks_routine(self):
        p={'pmid':'1','title':'Bench press 8-week trial','abstract':'1RM measured'}
        r=classify(p,{})
        self.assertEqual(r['full_text_access'],'not_confirmed_open')
        self.assertTrue(r['runnable'].startswith('blocked'))
        self.assertTrue(r['chart'].startswith('blocked'))
    def test_open_metadata_does_not_approve(self):
        r=classify({'pmid':'2','title':'Squat trial'},{'isOpenAccess':'Y','pmcid':'PMC123'})
        self.assertEqual(r['full_text_access'],'open_full_text_reported')
        self.assertTrue(r['runnable'].startswith('blocked'))
if __name__=='__main__':unittest.main()
