"""Finite version dispatch; no generated prescription rules."""
from . import coaching,sbd,metd,novice,petrizzo
from .workout import require
from .core import digest
from .programme_schedule import policy,selected

def adapter(source):
    version=source.get('adapter_version')
    if version==coaching.ENGINE:return coaching
    if version in (sbd.ENGINE,'per-source-labels-v1'):return sbd
    if version==metd.ENGINE:return metd
    if version==novice.ENGINE:return novice
    if version==petrizzo.ENGINE:return petrizzo
    require(False,'UNSUPPORTED_SOURCE')

def validate_source(source):return adapter(source).validate_source(source)
def exercises(source):
    if sbd.source_labels(source):return tuple(source['exercises'])
    return adapter(source).EXERCISES
def max_exercises(source):
    if sbd.source_labels(source):return sbd.EXERCISES
    return exercises(source)
def make_instance(source,*args):
    result=adapter(source).make_instance(source,*args)
    result['schedule_policy']=policy(source)
    result['programme_version']=digest({'adapter_programme_version':result['programme_version'],'schedule_policy':result['schedule_policy']})
    return result
def prepare(instance,*args):
    result=adapter(instance['source']).prepare(instance,*args)
    if 'schedule_policy' in instance:result['schedule_policy']=selected(instance['source'],instance['schedule_policy'])
    return result
def enrich(snapshot,result):return adapter(snapshot['source']).enrich(snapshot,result)
