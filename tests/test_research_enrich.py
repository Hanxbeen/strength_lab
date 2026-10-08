import unittest
from unittest.mock import patch
from scripts.research_enrich import enrich
class EnrichTests(unittest.TestCase):
    @patch('scripts.research_enrich.get')
    def test_no_fulltext_is_blocked(self,mock):
        mock.return_value=b'{"resultList":{"result":[{"pmcid":"PMC123","isOpenAccess":"N"}]}}'
        result=enrich({'pmid':'123'})
        self.assertFalse(result['runnable'])
        self.assertEqual(result['full_text_status'],'not_available')
    @patch('scripts.research_enrich.get')
    def test_fulltext_never_auto_approves(self,mock):
        mock.side_effect=[b'{"resultList":{"result":[{"pmcid":"PMC123","isOpenAccess":"Y"}]}}',b'<article><body><sec><p>'+b'bench press 1RM sets repetitions rest interval progression intensity training frequency '*30+b'</p></sec></body></article>']
        result=enrich({'pmid':'123'})
        self.assertEqual(result['full_text_status'],'open_xml_accessible')
        self.assertFalse(result['runnable'])
        self.assertFalse(result['chart_publishable'])
if __name__=='__main__':unittest.main()
