#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIVE_BIN="${RIVE_BIN:-$HOME/.rive/bin/rive}"

if [ ! -x "$RIVE_BIN" ]; then
  echo "Official Rive CLI required: https://rive.app/docs/cli/getting-started" >&2
  exit 2
fi

cd "$ROOT"
# Initial generation uses the *original poster images* with 4× AI SR.
# Prebuilt PNGs remain checked-in so a normal build never silently retrains
# or re-generates assets with a different model.
if [ ! -f assets/lila/poster_upscaled/lila_lv06_4x.png ]; then
  /opt/homebrew/bin/python3.13 scripts/upscale_lila_posters.py
fi

python3 scripts/build_lila_eye_blinks.py
python3 scripts/generate_lila_poster_rive_rml.py

"$RIVE_BIN" assets/lila/rive_cli --verify
"$RIVE_BIN" assets/lila/rive_cli --once
"$RIVE_BIN" inspect assets/lila/rive_cli --summary > assets/lila/rive_cli/build/inspect.json

python3 - <<'PY'
import json
from pathlib import Path
from PIL import Image
r=json.loads(Path("assets/lila/rive_cli/build/inspect.json").read_text())
assert not r["problems"], r["problems"]
assert [x["name"] for x in r["artboards"]] == [f"LilaLv{i}" for i in range(1,7)]
assert r["roots"]["types"].get("ImageAsset") == 12
for art in r["artboards"]:
    assert art["types"].get("Image",0) == 2
    assert art["types"].get("StateMachine",0) == 1
    assert art["types"].get("StateMachineLayer",0) == 3
    assert art["types"].get("LinearAnimation",0) == 3
for level in range(1,7):
    src=Image.open(f"assets/lila/poster_sprites/lila_lv{level:02}.webp")
    png=Image.open(f"assets/lila/rive_cli/sprites/lila_lv{level:02}.png")
    overlay=Image.open(f"assets/lila/rive_cli/sprites/lila_lv{level:02}_blink_overlay.png")
    assert png.size == (src.width*4,src.height*4)
    assert overlay.size == png.size
    assert overlay.getchannel("A").getbbox() is not None
print("Rive QA: original 3D artwork 4× + independently animated eyelids on all six levels; 18 loop animations")
PY

cp assets/lila/rive_cli/build/rive_cli.riv apps/ios/MugeMuge/Resources/lila.riv
python3 -m unittest discover -s tests -q
echo "Bundled upscaled Lila Rive: apps/ios/MugeMuge/Resources/lila.riv"
