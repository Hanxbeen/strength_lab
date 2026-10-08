import unittest
from scripts.research_gold_eval import evaluate
class GoldTests(unittest.TestCase):
 def setUp(self):
  self.packets={'papers':[{'pmid':'1','tables':[{'table_id':'T1','rows':[['1RM BP (kg)','Before','105 ± 10']]}]}]}
  self.reference={'reference_status':'curated','cases':[{'case_id':'x','pmid':'1','table_id':'T1','row_index_zero_based':0,'expected_cells':['1RM BP (kg)','Before','105 ± 10']}]}
 def test_exact(self):self.assertEqual(evaluate(self.packets,self.reference)['matched_cases'],1)
 def test_numeric_corruption_fails(self):
  self.packets['papers'][0]['tables'][0]['rows'][0][2]='106 ± 10'
  self.assertEqual(evaluate(self.packets,self.reference)['failed_cases'],1)
 def test_wrong_group_column_fails(self):
  self.packets['papers'][0]['tables'][0]['rows'][0][1]='After'
  self.assertEqual(evaluate(self.packets,self.reference)['failed_cases'],1)
 def test_missing_row_fails(self):
  self.packets['papers'][0]['tables'][0]['rows']=[]
  self.assertEqual(evaluate(self.packets,self.reference)['failed_cases'],1)
if __name__=='__main__':unittest.main()
