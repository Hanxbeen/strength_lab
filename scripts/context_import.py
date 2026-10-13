"""Emit reviewed summary import SQL; never publishes a prescription."""
import json
from pathlib import Path
from research_engine.core import digest
from research_engine.context_guidance import validate_packet

def build(packet):
    validate_packet(packet)
    quote = lambda v: "'" + v.replace("'", "''") + "'"
    return ("INSERT INTO public.coaching_context_versions(id,version,payload) VALUES ("
            + ",".join([quote(packet['id']),quote(digest(packet)),
                        quote(json.dumps(packet,ensure_ascii=False))+"::jsonb"])
            + ") ON CONFLICT DO NOTHING;")

if __name__ == '__main__':
    print(build(json.loads(Path('data/research/coaching/context-evidence.json').read_text())))
