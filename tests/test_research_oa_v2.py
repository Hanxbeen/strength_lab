import unittest
from unittest.mock import patch
from scripts.research_oa_v2 import classify,lookup_batch
class V2Tests(unittest.TestCase):
 def test_reject_acute(self):self.assertEqual(classify({'title':'Acute bench press performance'}),'excluded_off_topic_or_acute')
 def test_reject_sprint(self):self.assertEqual(classify({'title':'Sprint and jump with squat testing'}),'excluded_off_topic_or_acute')
 def test_direct(self):self.assertEqual(classify({'title':'Bench press strength training over eight weeks'}),'direct_sbd_candidate')
 @patch('scripts.research_oa_v2.get')
 def test_batch_metadata(self,get):
  get.return_value=b'{"resultList":{"result":[{"id":"123","pmcid":"PMC123","isOpenAccess":"Y"}]}}'
  self.assertEqual(lookup_batch(['123'])['123']['pmcid'],'PMC123')
if __name__=='__main__':unittest.main()
