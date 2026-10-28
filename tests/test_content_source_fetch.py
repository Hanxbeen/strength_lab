"""Downloader rejects tampering and preserves existing files atomically."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.fetch_content_sources import fetch_one

class ContentSourceFetchTests(unittest.TestCase):
    def test_valid_cache_never_calls_network(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp); data=b"verified"; (directory/"source.xml").write_bytes(data)
            with patch("scripts.fetch_content_sources.subprocess.run") as run:
                self.assertEqual(fetch_one(directory,("source.xml","https://example.test",hashlib.sha256(data).hexdigest())),"reused")
            run.assert_not_called()

    def test_mismatch_preserves_old_file_and_cleans_partial_download(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp); target=directory/"source.xml"; target.write_bytes(b"old")
            def download(args,check):
                Path(args[args.index("--output")+1]).write_bytes(b"changed")
            with patch("scripts.fetch_content_sources.shutil.which",return_value="/usr/bin/curl"),patch("scripts.fetch_content_sources.subprocess.run",side_effect=download):
                with self.assertRaisesRegex(ValueError,"SHA-256 mismatch"):
                    fetch_one(directory,("source.xml","https://example.test",hashlib.sha256(b"reviewed").hexdigest()))
            self.assertEqual(target.read_bytes(),b"old")
            self.assertEqual(list(directory.iterdir()),[target])

    def test_verified_download_is_atomic_and_requires_https(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp); target=directory/"source.xml"; data=b"reviewed"
            def download(args,check):
                self.assertTrue(check)
                self.assertNotIn("--insecure",args)
                self.assertEqual(args[args.index("--proto")+1],"=https")
                self.assertEqual(args[args.index("--proto-redir")+1],"=https")
                self.assertFalse(target.exists())
                Path(args[args.index("--output")+1]).write_bytes(data)
            with patch("scripts.fetch_content_sources.shutil.which",return_value="/usr/bin/curl"),patch("scripts.fetch_content_sources.subprocess.run",side_effect=download):
                self.assertEqual(fetch_one(directory,("source.xml","https://example.test",hashlib.sha256(data).hexdigest())),"downloaded")
            self.assertEqual(target.read_bytes(),data)
            self.assertEqual(list(directory.iterdir()),[target])

if __name__=="__main__":
    unittest.main()

