"""Prepare an immutable internal-preview insert; never approve or publish a routine."""
import argparse,json
from pathlib import Path
from research_engine.core import digest
from research_engine.sbd import validate_source

def build(source):
    validate_source(source)
    quote=lambda value:"'"+value.replace("'","''")+"'"
    return ('INSERT INTO public.coaching_source_versions(source_id,version,payload) VALUES ('+
            quote(source['id'])+','+quote(digest(source))+','+
            quote(json.dumps(source,ensure_ascii=False,allow_nan=False))+"::jsonb) ON CONFLICT DO NOTHING;\n")

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.write_text(build(json.loads(args.source.read_text())))
