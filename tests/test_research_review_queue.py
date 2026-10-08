import unittest
from scripts.research_review_queue import create
class ReviewQueueTests(unittest.TestCase):
 def test_complete_keyword_hints_do_not_approve(self):
  row={'pmid':'1','pmcid':'PMC1','title':'Example','field_evidence':{'progression':{'evidence':[{'matched':'progression'}]}},'tables':[{'table_id':'T1','caption':'Training protocol','row_count':2,'rows':[['Week','Set type'],['1','CS']]}],'candidate_outcome_rows':[{'cells':['1RM BP (kg)','100']} ]}
  result=create({'papers':[row]});item=result['papers'][0]
  self.assertEqual(item['week_row_locators'][0]['week'],1)
  self.assertFalse(item['runnable']);self.assertFalse(item['chart_publishable'])
  self.assertTrue(all(x['status']=='unverified' for x in item['fields'].values()))
 def test_row_integrity_mismatch(self):
  r=create({'papers':[{'pmid':'1','tables':[{'table_id':'T','caption':'Training','row_count':2,'rows':[['1']]}]}]})['papers'][0]
  self.assertEqual(r['integrity_issues'][0]['issue'],'row_count_mismatch')
if __name__=='__main__':unittest.main()
