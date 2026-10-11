import copy
import unittest
from scripts.research_store import build_sql

class ResearchStoreTests(unittest.TestCase):
    def fixture(self):
        return {
            'oa_candidates_v2': {'selected':1,'requested':20,'papers':[{'pmid':'123','title':"O'Brien 연구"}]},
            'protocol_audit': {'papers':[{'pmid':'123','source_sha256':'a'*64}]},
            'review_queue': {'papers':[{'pmid':'123','status':'awaiting_human_review'}]},
            'release_gate': {'papers':[{'pmid':'123','protocol_publishable':False,'chart_publishable':False}]},
            'evidence_audit': {'papers':[]}
        }
    def test_private_atomic_idempotent_import(self):
        data=self.fixture()
        first,sql=build_sql(data,'2026-10-11T00:00:00Z')
        second,again=build_sql(copy.deepcopy(data),'2026-10-11T00:00:00Z')
        self.assertEqual((first,sql),(second,again))
        self.assertTrue(sql.startswith('BEGIN;'))
        self.assertTrue(sql.endswith('COMMIT;\n'))
        self.assertIn("O''Brien",sql)
        self.assertIn('ON CONFLICT (run_id,pmid) DO NOTHING',sql)
        self.assertNotIn('INSERT INTO public.research_protocol_versions',sql)
    def test_reject_mismatched_batch(self):
        data=self.fixture();data['release_gate']['papers'][0]['pmid']='456'
        with self.assertRaises(ValueError):build_sql(data)
    def test_reject_published_items(self):
        data=self.fixture();data['release_gate']['papers'][0]['protocol_publishable']=True
        with self.assertRaises(ValueError):build_sql(data)
    def test_reject_missing_digest(self):
        data=self.fixture();del data['protocol_audit']['papers'][0]['source_sha256']
        with self.assertRaises(ValueError):build_sql(data)
    def test_reject_duplicate_ids(self):
        data=self.fixture();data['oa_candidates_v2']['papers']*=2
        with self.assertRaises(ValueError):build_sql(data)
    def test_reject_overwriting_signed_review(self):
        data=self.fixture();data['review_queue']['papers'][0]['status']='approved'
        with self.assertRaises(ValueError):build_sql(data)

if __name__=='__main__':unittest.main()
