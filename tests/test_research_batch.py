import unittest
from scripts.research_batch import QUERY
class BatchTests(unittest.TestCase):
    def test_query_targets_strength_and_one_rm(self):
        self.assertIn('resistance training',QUERY)
        self.assertIn('1RM',QUERY)
        self.assertIn('animals',QUERY)
if __name__=='__main__':unittest.main()
