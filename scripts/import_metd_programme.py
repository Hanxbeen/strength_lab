"""Print an idempotent immutable-source insert; never marks a programme public."""
import json
from pathlib import Path
from research_engine.core import digest
from research_engine.metd import validate_source

def build(source):
    validate_source(source)
    payload=json.dumps(source,ensure_ascii=False,separators=(',',':')).replace("'","''")
    return "INSERT INTO public.coaching_source_versions(source_id,version,payload,status) VALUES ('%s','%s','%s'::jsonb,'research_preview') ON CONFLICT (source_id,version) DO NOTHING;" % (source['id'],digest(source),payload)

if __name__=='__main__':
    print(build(json.loads((Path(__file__).resolve().parents[1]/'data/research/coaching/metd2021.json').read_text())))
