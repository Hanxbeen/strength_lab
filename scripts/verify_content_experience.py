"""All public choices through local API; fixture Auth/SQLite, never production writes."""
import json
from collections import Counter
from unittest.mock import patch
from research_engine import entry_learning
from research_engine.core import digest
from tests.test_routine_selection import RoutineSelectionTests
from tests.test_entry_learning import EntryLearningTests


def verify():
    case = RoutineSelectionTests()
    case.setUp()
    source = entry_learning.definition()
    learning_item = dict(source_id=source['id'], version=digest(source),
                         status='research_preview', definition=source)
    results = []
    guides = set()
    try:
        with patch('backend.entry_learning_api.catalogue', return_value=dict(items=[learning_item])):
            response = case.client.get('/v3/routines')
            assert response.status_code == 200, response.text
            catalog = response.json()
            assert len(catalog['routines']) == 10
            assert len(catalog['learning_paths']) == 1
            for index, option in enumerate(catalog['routines']):
                content = option['experience']
                assert content['source_version'] == option['source_version'] == digest(option['definition'])
                assert {g['exercise_id'] for g in content['exercises']} == set(option['exercise_ids'])
                for guide in content['exercises']:
                    assert guide['available'], guide
                    guides.add(guide['exercise_id'])
                chart = content['research_chart']
                assert bool(chart['points']) if chart['available'] else bool(chart['reason'])
                assert chart['individual_forecast'] is False
                assert content['during_workout'] and content['limitations']
                request, daily = case.request_for(option['definition'], option['arm'])
                preview = case.post('/v3/routines/preview', dict(request, **daily))
                assert preview['session_status'] == 'ready'
                iid, wid = 'content-i'+str(index), 'content-w'+str(index)
                base = '/v3/programme-instances/'+iid
                case.post('/v3/programme-instances', dict(request, id=iid))
                execution = case.post(base+'/workouts', dict(workout_id=wid, week=1, day=1,
                    started_at=request['created_at'], **daily))['execution']
                assert execution['experience']['exercise_guides']
                assert 'set_result' in execution['experience']['available_action_ids']
                sid = execution['next_set_id']
                for event in [dict(id='load', type='change_load', at=request['created_at'],
                                   set_id=sid, value=35, unit='kg', reason='fatigue'),
                              dict(id='actual', type='set_result', at=request['created_at'],
                                   set_id=sid, reps=1, rpe=9),
                              dict(id='end', type='finish', at=request['created_at'], reason='time')]:
                    execution = case.post('/v2/workouts/'+wid+'/events',
                        dict(expected_revision=execution['revision'], event=event))['execution']
                assert set(execution['experience']['available_action_ids']) <= {'reason_record'}
                result_response = case.client.get('/v2/workouts/'+wid+'/result')
                assert result_response.status_code == 200, result_response.text
                result = result_response.json()
                assert result['analysis']['performed']['recorded_sets'] == 1
                assert result['analysis']['differences']['unrecorded_set_ids']
                assert result['analysis']['effect_achievement_rate'] is None
                evaluation = case.post(base+'/evaluations', dict(id='evaluation', at=request['created_at'],
                    outcome='stopped', post_max_record_ids={}, comparison_conditions={}))
                analysis = evaluation['analysis']
                assert len(analysis['charts']['sessions']) == 1
                assert analysis['charts']['missing_value_policy'] == 'gap_not_zero'
                assert all(x['delta_kg'] is None for x in evaluation['lifts'])
                assert all(x['status'] == 'not_measured' for x in analysis['measurement_statuses'])
                reread = case.client.get(base).json()['evaluations'][0]
                assert reread['analysis'] == analysis
                results.append(dict(source_id=option['source_id'], arm=option['arm'],
                    level=option['availability']['experience_context'],
                    research_chart_available=chart['available'],
                    research_metric=chart.get('metric'), local_lifecycle_verified=True))
            entry = catalog['learning_paths'][0]['experience']
            assert len(entry['exercises']) == 3
            guides.update(g['exercise_id'] for g in entry['exercises'])
            fixture = EntryLearningTests(); fixture.setUp()
            started = case.post('/v3/entry/learning-sessions', dict(id='content-entry',
                source_id=source['id'], source_version=digest(source), started_at=fixture.at,
                profile=dict(age=25,current_pain=False,exercise_restriction=False),
                setup=dict(equipment_checked=True,accept_self_report_limits=True)))
            event = dict(fixture.observation('squat'), pain=True)
            stopped = case.post('/v3/entry/learning-sessions/content-entry/events',
                dict(expected_revision=started['execution']['revision'], event=event))
            assert stopped['execution']['state'] == 'stopped'
            assert stopped['execution']['candidate_working_loads'] == {}
            assert stopped['execution']['experience']['available_action_ids'] == []
            entry_result = case.client.get('/v2/workouts/content-entry/result')
            assert entry_result.status_code == 200, entry_result.text
            assert entry_result.json()['analysis']['scope'] == 'learning_session'
            assert entry_result.json()['analysis']['effect_achievement_rate'] is None
        assert len(guides) == 8, guides
        return dict(schema_version='content-experience-verification-v1',
            public_options=10, learning_paths=1, exercise_guides=sorted(guides),
            levels=dict(Counter(x['level'] for x in results)), choices=results,
            entry_pain_stop_verified=True, evaluation_reload_verified=True,
            source_definitions_unchanged=True,
            validation_environment='TestClient + source fixtures + owner substitute + temporary SQLite',
            live_catalog_verified=False, deployed_auth_verified=False,
            production_user_writes=False, iphone_interactions_verified=False)
    finally:
        case.tearDown()


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
