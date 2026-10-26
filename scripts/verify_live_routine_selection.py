"""Real HTTPS catalogue; local authenticated-owner substitute and temporary ledger only."""
import json
from backend.coaching_api import catalog
from research_engine.core import digest
from tests.test_routine_selection import RoutineSelectionTests

def verify():
    actual=catalog()
    assert actual['items'], 'EMPTY_LIVE_CATALOGUE'
    for item in actual['items']:
        assert item['version']==digest(item['definition']), 'VERSION_MISMATCH'
    case=RoutineSelectionTests()
    case.setUp()
    try:
        case.catalog.stop()
        # Every request now uses the configured real Supabase catalogue.
        response=case.client.get('/v3/routines')
        assert response.status_code==200,response.text
        data=response.json()
        assert len(data['routines'])==8,data['coverage']
        case.test_every_public_option_preview_create_start_change_stop_reload()
        return dict(real_https_catalog=True,options=len(data['routines']),
            coverage=data['coverage'],all_eight_local_lifecycles=True,
            deployed_auth_verified=False,production_user_writes=False)
    finally:
        case.tearDown()

if __name__=='__main__':
    print(json.dumps(verify(),ensure_ascii=False))
