"""Four-lift data and full API execution; auth is a local test override."""
import copy
import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app
from backend.workout_api import owner, store
from backend.workout_store import WorkoutStore
from backend.programme_options import options
from backend.programme_readiness import preview
from research_engine import petrizzo, novice
from research_engine.core import digest, InvalidProgramme
from research_engine.programme_dispatch import make_instance, prepare
from research_engine.workout import replay

class PetrizzoTests(unittest.TestCase):
    def fixture(self, days=2):
        self.source=petrizzo.definition(days)
        self.at='2026-10-18T09:00:00+00:00'
        self.profile={'age':25,'independent_sbd':True,'independent_ohp':True}
        self.setup=dict(mode='user_selected_source',accept_scope_limits=True,accept_adaptations=True,
            adaptation_id=petrizzo.ADAPTATION,rest_seconds=180,between_exercise_rest_seconds=300,
            equipment_step_kg=2.5,warmup='User selected progressive warm-up',
            starting_loads_kg={e:40 for e in petrizzo.EXERCISES},
            starting_load_origins={e:'known_working_load' for e in petrizzo.EXERCISES})
    def instance(self):
        return make_instance(self.source,petrizzo.ARM,self.profile,[],self.setup,self.at)
    def request(self):
        return dict(source_id=self.source['id'],source_version=digest(self.source),arm=petrizzo.ARM,
            profile=self.profile,setup=self.setup,created_at=self.at,max_record_ids={})
    def test_exact_schedules_data_and_legacy_preserved(self):
        self.assertEqual(digest(novice.definition()),'279463065a745b8b5f5581652a377ad37e7558bd1d3801aee46cc7b1f2140fcb')
        for days,total in ((2,156),(3,228)):
            self.fixture(days); source=self.source; counts={e:0 for e in petrizzo.EXERCISES}
            saved=json.loads((Path(__file__).resolve().parents[1]/'data/research/coaching'/f'petrizzo2018-four-lift-{days}d.json').read_text())
            self.assertEqual(saved,source)
            for i,s in enumerate(source['protocol']['sessions']):
                self.assertEqual(s['exercises'][1],petrizzo.EXERCISES[1 if i%2==0 else 3])
                self.assertEqual(petrizzo.EXERCISES[2] in s['exercises'],s['day']==2)
                snap=prepare(self.instance(),s['week'],s['day'],self.at,[],{e:40 for e in s['exercises']})
                self.assertEqual(snap['coaching']['arm'],petrizzo.ARM)
                for row in snap['session']['sets']:counts[row['exercise_id']]+=1
            self.assertEqual(sum(counts.values()),total)
            self.assertEqual(counts[petrizzo.EXERCISES[2]],12)
            row=options(dict(source_id=source['id'],version=digest(source),definition=source),True)[0]
            self.assertEqual(row['training_sessions'],12*days)
            self.assertEqual(row['arm_prescription']['reps'],5)
            self.assertFalse(row['scientific_approval'])
    def test_scope_missing_origin_and_source_tampering(self):
        self.fixture()
        self.assertEqual(preview(self.source,self.request(),[],True)['input_status'],'ready')
        self.profile['independent_ohp']=False
        self.assertEqual(preview(self.source,self.request(),[],True)['input_status'],'outside_supported_scope')
        self.profile['independent_ohp']=True
        self.setup['starting_load_origins'].pop(petrizzo.EXERCISES[-1])
        with self.assertRaisesRegex(InvalidProgramme,'STARTING_LOAD_RECORDS_REQUIRED'):self.instance()
        self.fixture()
        self.source['protocol']['sessions'][0]['exercises'].append(petrizzo.EXERCISES[-1])
        with self.assertRaisesRegex(InvalidProgramme,'UNSUPPORTED_PETRIZZO_DEFINITION'):self.instance()
    def test_registered_start_is_shown_and_changed_execution_retained(self):
        self.fixture(); instance=self.instance(); eids=self.source['protocol']['sessions'][0]['exercises']
        inputs=petrizzo.session_inputs(instance,eids,[])
        self.assertEqual(inputs['load_selection'][0]['input']['default_value'],40)
        self.assertIsNone(inputs['load_selection'][0]['recommended_load_kg'])
        with self.assertRaisesRegex(InvalidProgramme,'FIRST_LOAD_MUST_MATCH_REGISTERED_START'):
            prepare(instance,1,1,self.at,[],{e:35 for e in eids})
        snap=prepare(instance,1,1,self.at,[],{e:40 for e in eids})
        sid=snap['session']['sets'][0]['id']
        events=[dict(id='c',type='change_load',at=self.at,set_id=sid,value=35,unit='kg',reason='fatigue'),
                dict(id='r',type='set_result',at=self.at,set_id=sid,reps=4),
                dict(id='f',type='finish',at=self.at,reason='time')]
        ex=replay(snap,events)
        self.assertEqual(ex['sets'][0]['weight_kg'],40)
        self.assertEqual(ex['sets'][0]['actual']['weight_kg'],35)
        self.assertIsNone(ex['sets'][1]['actual'])
        prior=dict(workout_id='one',snapshot=snap,execution=ex,events=events)
        self.assertEqual(petrizzo.session_inputs(instance,eids,[prior])['load_selection'][0]['status'],'previous_session_not_completed')
    def test_full_two_and_three_day_api_lifecycle(self):
        for days,total in ((2,156),(3,228)):
            with self.subTest(days=days), tempfile.TemporaryDirectory() as directory:
                self.fixture(days); db=WorkoutStore(Path(directory)/'records.sqlite')
                app.dependency_overrides[owner]=lambda:'internal'
                app.dependency_overrides[store]=lambda:db
                entry=dict(source_id=self.source['id'],version=digest(self.source),status='research_preview',definition=self.source)
                try:
                    with patch('backend.coaching_api.catalog',return_value={'schema_version':3,'items':[entry]}), patch.dict(os.environ,COACHING_PREVIEW_OWNER_IDS='internal'):
                        client=TestClient(app)
                        def post(url,data):
                            response=client.post(url,json=data)
                            self.assertEqual(response.status_code,200,response.text)
                            return response.json()
                        request=dict(self.request(),id='four')
                        with patch.dict(os.environ,COACHING_PREVIEW_OWNER_IDS=''):
                            self.assertEqual(client.post('/v3/programme-instances',json=request).status_code,403)
                        post('/v3/programme-instances',request);base='/v3/programme-instances/four'
                        for session in self.source['protocol']['sessions']:
                            w,d=session['week'],session['day']
                            at=datetime.fromisoformat(self.at)+timedelta(days=(w-1)*7+(d-1)*2)
                            ready=client.get(base+'/next-session',params={'at':at.isoformat()})
                            self.assertEqual(ready.status_code,200,ready.text)
                            self.assertEqual(ready.json()['next_session']['day'],d)
                            wid=f'w{w}d{d}'
                            payload=dict(workout_id=wid,week=w,day=d,started_at=at.isoformat(),
                                initial_loads_kg={e:40 for e in session['exercises']})
                            ex=post(base+'/workouts',payload)['execution']
                            self.assertEqual(ex['coaching']['arm'],petrizzo.ARM)
                            self.assertEqual(post(base+'/workouts',payload)['execution'],ex)
                            def send(kind,**data):
                                nonlocal at,ex
                                at+=timedelta(seconds=300)
                                ex=post('/v2/workouts/'+wid+'/events',dict(expected_revision=ex['revision'],
                                    event=dict(id=str(ex['revision']),type=kind,at=at.isoformat(),**data)))['execution']
                            while ex['next_set_id']:
                                if ex['state']=='resting':send('rest_end',outcome='completed')
                                send('set_result',set_id=ex['next_set_id'],reps=5)
                            send('finish')
                            self.assertEqual(db.get('internal',wid)['execution'],ex)
                        end=post(base+'/evaluations',dict(id='end',at=(at+timedelta(days=1)).isoformat(),
                            outcome='completed',post_max_record_ids={},comparison_conditions={}))
                        self.assertEqual(end['training']['closed_sessions'],12*days)
                        self.assertEqual(end['training']['recorded_sets'],total)
                        self.assertIsNone(end['total_delta_kg'])
                finally:app.dependency_overrides.clear()

    def test_ohp_change_is_separate_from_sbd_total(self):
        from backend import coaching_store
        from backend.programme_evaluation import evaluate
        self.fixture()
        records=[dict(id=e,exercise_id=e,value=100,unit='kg',kind='measured',measured_at=self.at)
                 for e in petrizzo.EXERCISES]
        instance=make_instance(self.source,petrizzo.ARM,self.profile,records,self.setup,self.at)
        snap=prepare(instance,1,1,self.at,[],{e:40 for e in petrizzo.EXERCISES[:2]})
        with tempfile.TemporaryDirectory() as directory:
            db=WorkoutStore(Path(directory)/'records.sqlite')
            coaching_store.save_instance(db,'u','p',instance)
            coaching_store.start(db,'u','p','w',1,1,snap)
            with db.connect() as c:
                events=[dict(id='stop',type='finish',at=self.at,reason='time')]
                c.execute('UPDATE execution_workouts SET events=? WHERE owner=? AND id=?',(json.dumps(events),'u','w'))
            for r in records:db.register_max('u',dict(r,id='post-'+r['id'],value=110))
            result=evaluate(db,'u','p',dict(id='end',at=self.at,outcome='stopped',
                post_max_record_ids={e:'post-'+e for e in petrizzo.EXERCISES},
                comparison_conditions={e:'same' for e in petrizzo.EXERCISES}))
            self.assertEqual(result['total_delta_kg'],30)
            self.assertEqual(next(x for x in result['lifts'] if x['exercise_id']==petrizzo.EXERCISES[-1])['delta_kg'],10)

    def test_pain_and_rest_changes_keep_facts_without_load_advice(self):
        self.fixture()
        snap=prepare(self.instance(),1,1,self.at,[],{e:40 for e in petrizzo.EXERCISES[:2]})
        sid=snap['session']['sets'][0]['id']
        events=[dict(id='pain',type='change_load',at=self.at,set_id=sid,value=35,unit='kg',reason='pain')]
        paused=replay(snap,events)
        self.assertEqual(paused['state'],'paused')
        events += [dict(id='resume',type='resume',at=self.at),
                   dict(id='result',type='set_result',at=self.at,set_id=sid,reps=4),
                   dict(id='rest',type='rest_end',at='2026-10-18T09:01:00+00:00',outcome='skipped'),
                   dict(id='end',type='finish',at='2026-10-18T09:01:00+00:00',reason='time')]
        ex=replay(snap,events)
        enriched=petrizzo.enrich(snap,ex)
        self.assertEqual(enriched['coaching']['next_set_decision']['status'],'pain_context_required')
        self.assertIsNone(enriched['coaching']['next_set_decision']['factor'])
        ref=petrizzo.session_inputs(self.instance(),petrizzo.EXERCISES[:2],
            [dict(workout_id='pain',snapshot=snap,execution=ex,events=events)])['load_selection'][0]
        self.assertEqual(ref['status'],'pain_context_required')
        self.assertEqual(ref['recorded_choice_types'],[])
        self.assertIsNone(ex['sets'][1]['actual'])
