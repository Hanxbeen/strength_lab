"""Read-only real Auth + API + Postgres preflight. Never substitute credentials."""
import json
import os
import sys
import urllib.request
import urllib.error
from urllib.parse import urlsplit

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward a test user's bearer token to a redirect destination.
        raise urllib.error.HTTPError(req.full_url, code, 'Redirect refused', headers, None)

def verify():
    base=os.environ.get('MUGEMUGE_API_URL','').rstrip('/')
    token=os.environ.get('MUGEMUGE_TEST_ACCESS_TOKEN','')
    url=urlsplit(base)
    local=url.scheme=='http' and url.hostname in ('127.0.0.1','localhost','::1')
    if not ((url.scheme=='https' and url.hostname) or local) or url.username or url.password or url.query or url.fragment:
        raise ValueError('API_URL_REQUIRED_HTTPS_OR_LOOPBACK')
    if not token or '\n' in token or '\r' in token:
        raise ValueError('TEST_ACCESS_TOKEN_REQUIRED')
    opener=urllib.request.build_opener(NoRedirect())
    def get(path):
        request=urllib.request.Request(base+path,headers={'Authorization':'Bearer '+token})
        with opener.open(request,timeout=45) as response:
            return json.load(response)
    readiness=get('/v3/runtime-readiness')
    if readiness.get('ready') is not True or readiness.get('storage')!='postgres':
        raise ValueError('REAL_POSTGRES_READINESS_REQUIRED')
    routines=get('/v3/routines')
    for level in ('foundation','trained','experienced'):
        if routines['coverage'][level]['option_count']<1:
            raise ValueError('EXPERIENCE_SUPPLY_MISSING')
    if routines['coverage']['entry']['learning_path_count']<1:
        raise ValueError('ENTRY_SUPPLY_MISSING')
    for path in ('/v2/max-records','/v3/programme-instances','/v3/entry/learning-sessions'):
        if not isinstance(get(path).get('items'),list):
            raise ValueError('OWNER_LIST_CONTRACT_INVALID')
    return {'real_auth_verified':True,'postgres_read_verified':True,
            'catalogue_options':len(routines['routines']),
            'coverage':routines['coverage'],'write_verified':False,
            'owner_isolation_verified':False,'client_execution_verified':False}

if __name__=='__main__':
    try:
        print(json.dumps(verify(),ensure_ascii=False))
    except urllib.error.HTTPError as error:
        print(json.dumps({'ok':False,'http_status':error.code,'error':'API_REQUEST_FAILED'}));sys.exit(1)
    except ValueError as error:
        # Known validation codes only; don't leak server payloads or connection information.
        code=str(error)
        if not code.isupper() or not code.replace('_','').isalpha():code='INVALID_RESPONSE'
        print(json.dumps({'ok':False,'error':code}));sys.exit(1)
    except (OSError,KeyError,TypeError,AttributeError):
        print(json.dumps({'ok':False,'error':'CONNECTION_OR_CONTRACT_FAILED'}));sys.exit(1)
