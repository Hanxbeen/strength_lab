#!/usr/bin/env python3
"""Export the approved Lila master without cropping, redrawing, or recoloring."""
from pathlib import Path
import hashlib
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/brand/app-icon/lila-approved-master.png"
DEST = ROOT / "apps/ios/MugeMuge/Resources/Assets.xcassets/AppIcon.appiconset/AppIcon.png"
APPROVED_SHA256 = "b1087d66213d5ffedb1e1c2ffbc87b9ffcc0686225bb5fd67643c0755c4b174b"

def create():
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != APPROVED_SHA256:
        raise ValueError("Master differs from the approved icon; review before exporting.")
    with Image.open(SOURCE) as source:
        if source.width != source.height or source.mode != "RGB":
            raise ValueError("Approved master must be a square, opaque RGB image.")
        icon = source.resize((1024, 1024), Image.Resampling.LANCZOS)
        DEST.parent.mkdir(parents=True, exist_ok=True)
        icon.save(DEST, format="PNG", optimize=True)
    print(f"Approved app icon exported: {DEST}")

if __name__ == "__main__":
    create()
