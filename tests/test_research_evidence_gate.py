import unittest
from scripts.research_evidence_gate import evaluate
class EvidenceTests(unittest.TestCase):
 def test_methods_and_results_hints_do_not_approve(self):
  xml=b'<article><body><sec><title>Methods</title><p>Eight weeks of back squat training with 3 sets and progression.</p></sec><sec><title>Results</title><p>Bench press 1RM increased.</p></sec></body></article>'
  row=evaluate({'pmid':'1','pmcid':'PMC1','title':'Squat training'},xml)
  self.assertEqual(row['tier'],'direct_sbd_longitudinal_candidate')
  self.assertFalse(row['runnable']);self.assertFalse(row['chart_publishable'])
  self.assertEqual(row['evidence_hints']['sbd_methods'][0]['section'],'Methods')
 def test_acute_title_is_excluded(self):
  row=evaluate({'pmid':'2','pmcid':'PMC2','title':'Acute bench press performance'},b'<article><body><sec><title>Methods</title><p>Bench press.</p></sec></body></article>')
  self.assertEqual(row['tier'],'exclude_acute_title')
if __name__=='__main__':unittest.main()
