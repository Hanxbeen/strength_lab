"""Finite version dispatch; no generated prescription rules."""
from . import coaching,sbd
from .workout import require

def adapter(source):
    version=source.get('adapter_version')
    if version==coaching.ENGINE:return coaching
    if version==sbd.ENGINE:return sbd
    require(False,'UNSUPPORTED_SOURCE')

def validate_source(source):return adapter(source).validate_source(source)
def exercises(source):return adapter(source).EXERCISES
def make_instance(source,*args):return adapter(source).make_instance(source,*args)
def prepare(instance,*args):return adapter(instance['source']).prepare(instance,*args)
def enrich(snapshot,result):return adapter(snapshot['source']).enrich(snapshot,result)
