import unittest
from backend.catalog import public_catalog, preview_catalog

class CatalogContractTests(unittest.TestCase):
    def test_default_empty(self):
        self.assertEqual(public_catalog([]), [])
    def test_review_only_never_public(self):
        item = preview_catalog()[0]
        item.update(status="PUBLISHED_PROTOCOL", runnable=True, source_type="RESEARCH")
        self.assertEqual(public_catalog([item]), [])
    def test_released_record(self):
        item = preview_catalog()[0]
        item.update(status="PUBLISHED_PROTOCOL", runnable=True, source_type="RESEARCH",
                    source_sha256="a"*64, release_id="release-1")
        self.assertEqual(len(public_catalog([item])), 1)
    def test_copy_does_not_mutate_source(self):
        item = preview_catalog()[0]
        item.update(status="PUBLISHED_PROTOCOL", runnable=True, source_type="RESEARCH",
                    source_sha256="a"*64, release_id="release-1")
        public_catalog([item])[0]["title"] = "changed"
        self.assertEqual(item["title"], "SBD 기록 연습")

if __name__ == "__main__":
    unittest.main()
