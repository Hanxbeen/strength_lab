import io
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError
from backend.repository import database_catalog, CatalogUnavailable

class CatalogRepositoryTests(unittest.TestCase):
    def environment(self):
        return patch.dict('os.environ',{'SUPABASE_URL':'https://example.invalid','SUPABASE_PUBLISHABLE_KEY':'public-test'},clear=True)
    def test_actual_database_metadata_is_preserved(self):
        value={'schema_version':1,'items':[],'metadata':{'candidates':3,'awaiting_review':3}}
        with self.environment(),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(value).encode())) as fetch:
            self.assertEqual(database_catalog(),value)
            self.assertTrue(fetch.call_args.args[0].full_url.endswith('/rest/v1/rpc/research_catalog'))
    def test_unconfigured_is_not_empty_success(self):
        with patch.dict('os.environ',{},clear=True),self.assertRaises(CatalogUnavailable):database_catalog()
    def test_outage_is_not_empty_success(self):
        with self.environment(),patch('urllib.request.urlopen',side_effect=URLError('offline')),self.assertRaises(CatalogUnavailable):database_catalog()
    def test_unreleased_data_cannot_leak(self):
        value={'schema_version':1,'items':[{'id':'candidate','runnable':False,'status':'awaiting_human_review'}]}
        with self.environment(),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(value).encode())):
            self.assertEqual(database_catalog()['items'],[])
    def test_unsupported_schema_is_error(self):
        with self.environment(),patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"schema_version":2,"items":[]}')),self.assertRaises(CatalogUnavailable):database_catalog()
    def test_read_only_studies_are_returned_separately(self):
        study={'pmid':'123','decision':'NOT_RUNNABLE','runnable':False}
        value={'schema_version':1,'items':[],'studies':[study]}
        with self.environment(),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(value).encode())):
            response=database_catalog()
            self.assertEqual(response['studies'],[study])
            self.assertEqual(response['items'],[])
    def test_runnable_claim_in_study_is_rejected(self):
        value={'schema_version':1,'items':[],'studies':[{'decision':'NOT_RUNNABLE','runnable':True}]}
        with self.environment(),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(value).encode())),self.assertRaises(CatalogUnavailable):
            database_catalog()

if __name__=='__main__':unittest.main()
