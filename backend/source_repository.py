"""Read source templates from the deployed v2 RPC; validate before serving."""
import json
import os
import urllib.request
import urllib.error
from .repository import CatalogUnavailable
from research_engine.core import compile_programme, InvalidProgramme

def source_catalog():
    base=os.environ.get('SUPABASE_URL','').rstrip('/')
    key=os.environ.get('SUPABASE_PUBLISHABLE_KEY','')
    if not base.startswith('https://') or not key: raise CatalogUnavailable('Database is not configured')
    request=urllib.request.Request(base+'/rest/v1/rpc/source_programme_catalog',data=b'{}',method='POST',headers={'apikey':key,'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=10) as response:value=json.loads(response.read())
        if value.get('schema_version')!=2 or not isinstance(value.get('items'),list): raise ValueError('Unsupported source schema')
        for p in value['items']:
            compiled=compile_programme(p['definition'])
            for key in ('programme_id','programme_version','engine_version','session_count','working_set_count'):
                if p[key]!=compiled[key]:raise ValueError('Source definition contract mismatch')
        return value
    except (urllib.error.URLError,ValueError,KeyError,TypeError,AttributeError,InvalidProgramme) as error:
        raise CatalogUnavailable('Source catalog unavailable') from error
