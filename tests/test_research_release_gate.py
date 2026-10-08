import unittest
from scripts.research_release_gate import validate,REQUIRED_PROTOCOL,REQUIRED_CHART
class GateTests(unittest.TestCase):
 def item(self):
  return {'status':'approved','reviewer_id':'reviewer-1','reviewed_at':'2026-10-08T00:00:00Z','source_sha256':'a'*64,'source_url':'https://example.org/source','complete_arm_session_matrix':True,'validated_group_timepoint_mapping':True,'fields':{k:{'status':'verified','source_locators':[{'table_id':'T1','row':2}]} for k in REQUIRED_PROTOCOL+REQUIRED_CHART}}
 def test_complete_signoff_passes(self):
  self.assertEqual(validate(self.item(),'protocol'),[])
  self.assertEqual(validate(self.item(),'chart'),[])
 def test_missing_progression_blocks(self):
  item=self.item();item['fields']['progression']['status']='unverified'
  self.assertIn('unverified_progression',validate(item,'protocol'))
 def test_missing_group_mapping_blocks_chart(self):
  item=self.item();item['validated_group_timepoint_mapping']=False
  self.assertIn('missing_group_timepoint_mapping',validate(item,'chart'))
 def test_unsigned_blocks(self):
  item=self.item();item.pop('reviewer_id')
  self.assertIn('missing_reviewer_id',validate(item,'protocol'))
if __name__=='__main__':unittest.main()
