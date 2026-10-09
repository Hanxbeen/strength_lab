#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RIVE_BIN="${RIVE_BIN:-$HOME/.rive/bin/rive}"

if [ ! -x "$RIVE_BIN" ]; then
  echo "Official Rive CLI required: https://rive.app/docs/cli/getting-started" >&2
  exit 2
fi

cd "$ROOT"
python3 scripts/build_lila_phase2_assets.py
python3 scripts/generate_lila_rive_rml.py
"$RIVE_BIN" assets/lila/rive_cli --verify
"$RIVE_BIN" assets/lila/rive_cli --once
"$RIVE_BIN" inspect assets/lila/rive_cli --summary > assets/lila/rive_cli/build/inspect.json

python3 - <<'PY'
import json
from pathlib import Path
r=json.loads(Path("assets/lila/rive_cli/build/inspect.json").read_text())
assert not r["problems"], r["problems"]
assert [x["name"] for x in r["artboards"]] == [f"LilaLv{i}" for i in range(1,7)]
for art in r["artboards"]:
    assert art["types"].get("StateMachine",0)==1
    assert art["types"].get("LinearAnimation",0)==2
print("Rive artboard QA: 6/6 pass, no problems")
PY

cp assets/lila/rive_cli/build/rive_cli.riv apps/ios/MugeMuge/Resources/lila.riv
python3 -m unittest discover -s tests -q
echo "Bundled genuine Rive binary: apps/ios/MugeMuge/Resources/lila.riv"
