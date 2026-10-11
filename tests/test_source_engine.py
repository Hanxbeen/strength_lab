"""Adversarial tests on real, cached source documents; explicit opt-in source path."""
import copy
import json
import os
from pathlib import Path
import socket
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from research_engine.adapters import extract, SOURCES
from research_engine.batch import build, store_database, read_database
from research_engine.core import (InvalidProgramme, compile_programme, initial_load, instantiate_session,
                                 progression, validate_schedule, explain_exercise, assess_profile)

SOURCE_DIR=Path(os.environ.get('RESEARCH_ENGINE_SOURCE_DIR','data/research/engine-sources'))

@unittest.skipUnless(all((SOURCE_DIR/(p+'.xml')).exists() for p in SOURCES),'Real source cache required; run source integration suite explicitly')
class SourceEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build(SOURCE_DIR)
        assert not cls.catalog['failures'],cls.catalog['failures']
    def programme(self,id='PMC11140948-SG'):
        return copy.deepcopy(next(p for p in self.catalog['programmes'] if p['programme_id']==id))
    def test_real_source_counts(self):
        self.assertEqual(self.catalog['source_count'],3)
        self.assertEqual(self.catalog['programme_count'],5)
        expected={'PMC11140948-SG':(16,160),'PMC11140948-DG':(16,160),'PMC5003312-LOW':(24,504),'PMC5003312-HIGH':(24,504),'PMC6974452-TRAD':(24,432)}
        for p in self.catalog['programmes']:
            self.assertEqual((p['session_count'],p['working_set_count']),expected[p['programme_id']])
    def test_offline_reproducibility(self):
        with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')):
            self.assertEqual(build(SOURCE_DIR),self.catalog)
    def test_source_mutation_blocks(self):
        raw=(SOURCE_DIR/'PMC11140948.xml').read_bytes()
        with self.assertRaisesRegex(InvalidProgramme,'SOURCE_CHANGED'):
            extract('PMC11140948',raw.replace(b'85%',b'95%',1))
    def test_unknown_source_is_not_approved(self):
        with self.assertRaisesRegex(InvalidProgramme,'UNSUPPORTED_SOURCE'):extract('PMC8041766',b'<article/>')
    def test_field_edit_without_proof_is_rejected(self):
        p=self.programme()['definition'];p['exercises'][0]['reps']['max']=40
        with self.assertRaisesRegex(InvalidProgramme,'changed_value'):compile_programme(p)
    def test_missing_evidence_is_rejected(self):
        p=self.programme()['definition'];p['provenance'].pop('exercises.1.rest')
        with self.assertRaises(InvalidProgramme):compile_programme(p)
    def test_max_must_match_exact_exercise(self):
        p=self.programme()['definition']
        with self.assertRaisesRegex(InvalidProgramme,'Exact exercise'):initial_load(p,'barbell_half_squat',{'barbell_back_squat':100})
        value=initial_load(p,'barbell_half_squat',{'barbell_half_squat':100})
        self.assertEqual(value['weight_kg'],85)
    def test_rounding_retains_unrounded_prescription(self):
        p=self.programme()['definition'];value=initial_load(p,'barbell_half_squat',{'barbell_half_squat':103},2.5)
        self.assertEqual(value['source_weight_kg'],87.55)
        self.assertEqual(value['weight_kg'],87.5)
        self.assertIsNotNone(value['policy'])
    def test_rir_does_not_invent_percent(self):
        value=initial_load(self.programme()['definition'],'barbell_hip_thrust',{})
        self.assertIsNone(value['weight_kg']);self.assertEqual(value['target']['target'],2)
    def test_progression_retains_range_and_timing(self):
        p=self.programme()['definition']
        self.assertEqual(progression(p,3)['kg_range'],[2.5,5.0])
        self.assertEqual(progression(p,5)['kg_range'],[2.5,10.0])
        self.assertEqual(progression(p,4)['action'],'no_rule_triggered')
    def test_frequency_and_recovery(self):
        p=self.programme('PMC6974452-TRAD')['definition']
        days=[w*7+d for w in range(8) for d in (0,2,4)]
        self.assertTrue(validate_schedule(p,days)['source_programme_unchanged'])
        days[1]=1
        with self.assertRaisesRegex(InvalidProgramme,'Recovery'):validate_schedule(p,days)
    def setup(self):
        return {'exercise_order':['barbell_half_squat','dumbbell_bulgarian_split_squat','barbell_hip_thrust'],
                'warmup':'user chosen warmup','between_exercise_rest_seconds':180,'split_squat_reps':'per_leg',
                'measured_1rm_kg':{'barbell_half_squat':100},'working_loads_kg':{'dumbbell_bulgarian_split_squat':10,'barbell_hip_thrust':40}}
    def profile(self):return {'sex':'female','age':25,'training_months':12,'healthy':True}
    def test_full_session_is_ready_without_ai(self):
        p=self.programme()
        with patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')):
            result=instantiate_session(p,p['sessions'][0]['id'],self.profile(),self.setup())
            explanation=explain_exercise(p['definition'],'barbell_half_squat')
        self.assertEqual(result['readiness'],'READY');self.assertEqual(len(result['sets']),10)
        self.assertEqual(result['sets'][0]['weight_kg'],85)
        self.assertEqual(len(explanation['evidence']),4)
    def test_source_gaps_are_not_silently_filled(self):
        p=self.programme();setup=self.setup();setup.pop('warmup')
        with self.assertRaisesRegex(InvalidProgramme,'warmup'):instantiate_session(p,p['sessions'][0]['id'],self.profile(),setup)
    def test_population_not_extrapolated(self):
        p=self.programme()['definition']
        self.assertFalse(assess_profile(p,{'sex':'male','age':25,'training_months':12,'healthy':True})['within_recorded_scope'])
        self.assertFalse(assess_profile(p,{})['within_recorded_scope'])
    def test_last_set_has_no_fake_rest_interval(self):
        self.assertIsNone(self.programme()['sessions'][0]['sets'][-1]['rest_after'])
    def test_transaction_and_idempotency(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog.sqlite3'
            first=store_database(path,self.catalog);second=store_database(path,self.catalog)
            self.assertEqual(first,second)
            self.assertEqual(read_database(path),self.catalog)
            with sqlite3.connect(path) as db:self.assertEqual(db.execute('select count(*) from programmes').fetchone()[0],5)
            bad=copy.deepcopy(self.catalog);bad['failures']=[{'error':'missing source'}]
            with self.assertRaises(InvalidProgramme):store_database(path,bad)
            self.assertEqual(read_database(path),self.catalog)

if __name__=='__main__':unittest.main()
