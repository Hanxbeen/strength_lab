import hashlib
import unittest
from scripts.research_automatic_assessment import assess

class AutomaticAssessmentTests(unittest.TestCase):
    def fixture(self):
        raw=b'<article><front><article-meta><article-id>123</article-id><article-id>PMC456</article-id></article-meta></front></article>'
        return {'pmid':'123','pmcid':'PMC456','title':'Training','source_sha256':hashlib.sha256(raw).hexdigest()},raw
    def codes(self, result):
        return [r['code'] for r in result['reasons']]
    def test_source_change_stops_interpretation(self):
        p,raw=self.fixture()
        self.assertEqual(self.codes(assess(p,raw+b' ')),['SOURCE_CHANGED'])
    def test_identity_must_match(self):
        p,raw=self.fixture();p['pmid']='999'
        self.assertEqual(self.codes(assess(p,raw)),['SOURCE_MISMATCH'])
    def test_missing_source_is_not_review_queue(self):
        p,_=self.fixture();r=assess(p)
        self.assertEqual(r['decision'],'SOURCE_ERROR')
        self.assertFalse(r['runnable'])
    def test_cluster_and_variable_set_limitation(self):
        p,raw=self.fixture();p['tables']=[{'caption':'Resistance training program.','rows':[['Set 1','Set 2','Cluster rest']]}]
        r=assess(p,raw)
        self.assertIn('VARIABLE_SET_PRESCRIPTION',self.codes(r))
        self.assertIn('CLUSTER_REST',self.codes(r))
        self.assertFalse(r['runnable'])
    def test_hypothetical_table_is_not_prescription(self):
        p,raw=self.fixture();p.update(title='Effects of movement tempo',missing_evidence_fields=['duration','frequency'],tables=[{'caption':'Hypothetical training program','rows':[['Set 1','Set 2']]}])
        self.assertEqual(self.codes(assess(p,raw)),['NOT_TRAINING_PROGRAM'])
    def test_unknown_layout_never_gets_fabricated_session(self):
        p,raw=self.fixture()
        self.assertEqual(self.codes(assess(p,raw)),['MISSING_PRESCRIPTION'])
    def test_accessories_are_not_silently_dropped(self):
        p,raw=self.fixture();p['tables']=[{'caption':'Resistance training protocol','rows':[['Trap-bar deadlift','Bulgarian split squat']]}]
        self.assertIn('UNSUPPORTED_EXERCISES',self.codes(assess(p,raw)))

if __name__=='__main__':unittest.main()
