#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIVE_BIN="${RIVE_BIN:-$HOME/.rive/bin/rive}"

if [ ! -x "$RIVE_BIN" ]; then
  echo "Official Rive CLI required: https://rive.app/docs/cli/getting-started" >&2
  exit 2
fi

cd "$ROOT"
# The production Lila visual asset is the ORIGINAL 3D poster sprite,
# not the historically retained vector/ellipse experiment.
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
assert r["roots"]["types"].get("ImageAsset") == 6
for art in r["artboards"]:
    assert art["types"].get("Image",0) == 1
    assert art["types"].get("StateMachine",0) == 1
    assert art["types"].get("LinearAnimation",0) == 2
for level in range(1,7):
    src=Path(f"assets/lila/poster_sprites/lila_lv{level:02}.webp")
    png=Path(f"assets/lila/rive_cli/sprites/lila_lv{level:02}.png")
    assert Image.open(src).convert("RGBA").tobytes() == Image.open(png).convert("RGBA").tobytes()
print("Rive QA: 6/6 original 3D sprites pixel-identical to source, 6 artboards, 12 loop animations")
PY

cp assets/lila/rive_cli/build/rive_cli.riv apps/ios/MugeMuge/Resources/lila.riv
python3 -m unittest discover -s tests -q
echo "Bundled original 3D Lila Rive: apps/ios/MugeMuge/Resources/lila.riv"
