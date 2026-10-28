"""Fetch the four audited research-chart sources; never accept changed bytes.

Requires curl (uses its normal system TLS trust). No database writes.
Usage: python -m scripts.fetch_content_sources [--directory PATH]
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "data/research/coaching/sources"
SOURCES = (
    ("PMC5877330.xml", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5877330/fullTextXML",
     "1ec02777c1ea7ef63393384d14ee6270dfd45cd6412f7c2e32f795f292498b12"),
    ("PMC8435792.xml", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8435792/fullTextXML",
     "ec922473ddd0107354830afe5d0ae545b3e6f964fe7b98f3cdaf9f2b4e326bf6"),
    ("PMC6162635.xml", "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6162635/fullTextXML",
     "d3b91266b5f34e143d1c0864c2d33473b440dd789dd19c1e847f3c39a4b79bb1"),
    ("JEPonlineOCTOBER2018_Petrizzo.pdf", "https://www.asep.org/asep/asep/JEPonlineOCTOBER2018_Petrizzo.pdf",
     "fc8eb398f4a9eac7318eb3e22a3c2ea751cde935e22fe76633d013a4fb64b152"),
)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fetch_one(directory, entry):
    name, url, expected = entry
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / name
    if target.is_file() and sha256(target) == expected:
        return "reused"
    curl = shutil.which("curl")
    if curl is None:
        raise RuntimeError("curl is required; TLS verification must remain enabled")
    descriptor, pending = tempfile.mkstemp(prefix=name+".", suffix=".pending", dir=directory)
    os.close(descriptor)
    pending = Path(pending)
    try:
        subprocess.run([curl, "--fail", "--location", "--proto", "=https",
            "--proto-redir", "=https", "--max-time", "45", "--silent",
            "--show-error", "--output", str(pending), url], check=True)
        actual = sha256(pending)
        if actual != expected:
            raise ValueError(f"{name}: source SHA-256 mismatch; expected {expected}, got {actual}. "
                             "Review the source revision; do not silently update the accepted hash.")
        os.replace(pending, target)
        return "downloaded"
    finally:
        if pending.exists():
            pending.unlink()

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory",type=Path,default=DEFAULT_DIRECTORY)
    args=parser.parse_args()
    for entry in SOURCES:
        print(entry[0]+": "+fetch_one(args.directory,entry),flush=True)

if __name__=="__main__":
    main()

