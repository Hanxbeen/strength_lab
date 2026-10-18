import copy
import io
import json
import os
import unittest
from unittest.mock import patch
from backend.coaching_api import catalog
from backend.repository import CatalogUnavailable
from research_engine.novice import definition
from research_engine.core import digest, InvalidProgramme
from scripts.import_novice_programme import build


class CatalogueV3Tests(unittest.TestCase):
    def entry(self):
        source = definition()
        return dict(source_id=source['id'],version=digest(source),status='research_preview',definition=source)
    def fetch(self, body):
        response = io.BytesIO(json.dumps(body).encode())
        with patch.dict(os.environ,SUPABASE_URL='https://example.test',SUPABASE_PUBLISHABLE_KEY='test'), \
             patch('urllib.request.urlopen',return_value=response) as opened:
            result = catalog()
            self.assertTrue(opened.call_args[0][0].full_url.endswith('/coaching_programme_catalog_v4'))
            return result
    def test_new_rpc_and_suspended_filter(self):
        entry=self.entry();stopped=copy.deepcopy(entry);stopped['status']='suspended'
        result=self.fetch(dict(schema_version=3,items=[entry,stopped]))
        self.assertEqual(result['items'],[entry])
    def test_malformed_or_changed_definition_fails_closed(self):
        entry=self.entry();entry['version']='wrong'
        with self.assertRaises(CatalogUnavailable):self.fetch(dict(schema_version=3,items=[entry]))
        entry=self.entry();entry['definition']['scientific_approval']=True;entry['version']=digest(entry['definition'])
        with self.assertRaises(CatalogUnavailable):self.fetch(dict(schema_version=3,items=[entry]))
        with self.assertRaises(CatalogUnavailable):self.fetch(dict(schema_version=4,items=[]))
    def test_insert_is_not_update_or_publication(self):
        source=definition();sql=build(source)
        self.assertIn(digest(source),sql);self.assertIn('ON CONFLICT (source_id,version) DO NOTHING',sql)
        self.assertIn('internal_product_prototype',sql)
        source['publication_status']='published'
        with self.assertRaises(InvalidProgramme):build(source)
