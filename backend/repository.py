"""Published catalog comes from the same RLS-protected DB RPC used by the app."""
import json
import os
import urllib.error
import urllib.request
from .catalog import public_catalog

class CatalogUnavailable(Exception):
    pass

def database_catalog():
    base = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_PUBLISHABLE_KEY', '')
    if not base.startswith('https://') or not key:
        raise CatalogUnavailable('Catalog database is not configured')
    request = urllib.request.Request(base + '/rest/v1/rpc/research_catalog',
        data=b'{}', method='POST', headers={'apikey': key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            value = json.loads(response.read())
        if not isinstance(value, dict) or value.get('schema_version') != 1 or not isinstance(value.get('items'), list):
            raise ValueError('Unsupported catalog response')
        if not all(isinstance(record, dict) for record in value['items']):
            raise ValueError('Malformed catalog records')
        return {'schema_version': 1, 'items': public_catalog(value['items']), 'metadata': value.get('metadata')}
    except (urllib.error.URLError, ValueError, TypeError, KeyError) as error:
        raise CatalogUnavailable('Catalog database request failed') from error
