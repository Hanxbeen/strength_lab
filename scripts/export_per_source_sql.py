"""Emit reviewed immutable data only; apply after catalogue-v5 migration."""
import json
from pathlib import Path
from research_engine.core import digest
from research_engine.sbd import validate_source
from backend.programme_access import availability
ROOT=Path(__file__).resolve().parents[1]
def sql():
    source=json.loads((ROOT/'data/research/coaching/pilot2018-source-labels.json').read_text())
    validate_source(source)
    assert availability(source)['public_selection'],'Unreviewed version'
    literal=json.dumps(source,ensure_ascii=False,separators=(',',':')).replace("'","''")
    return ("INSERT INTO public.coaching_source_versions(source_id,version,payload,status) VALUES "
        "('"+source['id']+"','"+digest(source)+"','"+literal+"'::jsonb,'research_preview') "
        "ON CONFLICT (source_id,version) DO NOTHING;")
if __name__=='__main__':print(sql())
