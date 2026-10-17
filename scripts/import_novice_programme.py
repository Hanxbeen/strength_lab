"""Idempotent internal-prototype insert; never promotes or overwrites a stored version."""
import json
from pathlib import Path
from research_engine.core import digest
from research_engine.novice import validate_source


def build(source):
    validate_source(source)
    quote = lambda value: "'" + value.replace("'", "''") + "'"
    return ('INSERT INTO public.coaching_source_versions(source_id,version,payload,status) VALUES (' +
            quote(source['id']) + ',' + quote(digest(source)) + ',' +
            quote(json.dumps(source, ensure_ascii=False, allow_nan=False)) +
            "::jsonb,'research_preview') ON CONFLICT (source_id,version) DO NOTHING;")


if __name__ == '__main__':
    print(build(json.loads((Path(__file__).resolve().parents[1]/'data/research/coaching/novice-sbd-choice.json').read_text())))
