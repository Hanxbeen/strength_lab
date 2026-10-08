import unittest
from scripts.research_protocol_audit import review_packet,table_rows
import xml.etree.ElementTree as ET
class AuditTests(unittest.TestCase):
 def test_table_rows_preserve_cells(self):
  t=ET.fromstring('<table-wrap><table><tbody><tr><td>1RM BP (kg)</td><td>105.4 ± 11.8</td></tr></tbody></table></table-wrap>')
  self.assertEqual(table_rows(t),[['1RM BP (kg)','105.4 ± 11.8']])
 def test_evidence_never_unlocks_publication(self):
  x=b'<article><body><sec id="S1"><title>Training protocol</title><p>Training twice a week for 8 weeks. Four sets of four repetitions of deadlift at 85% 1RM. Increase the load.</p></sec><table-wrap id="T1"><caption>1RM strength results</caption><table><tr><td>1RM BP (kg)</td><td>100 +/- 5</td></tr></table></table-wrap></body></article>'
  r=review_packet({'pmid':'1','pmcid':'PMC1','title':'test'},x)
  self.assertEqual(r['field_evidence']['progression']['status'],'candidate_found_not_verified')
  self.assertFalse(r['runnable']);self.assertFalse(r['chart_publishable'])
  self.assertEqual(r['candidate_outcome_rows'][0]['source']['table_id'],'T1')
if __name__=='__main__':unittest.main()
