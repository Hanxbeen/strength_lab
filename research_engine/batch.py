"""Offline source extraction and immutable local release artifacts.

The v2 artifact is a source workload template, NOT a v1 scientific publication.
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from .adapters import SOURCES, extract
from .core import ENGINE_VERSION, InvalidProgramme, compile_programme, digest

def build(source_dir):
    programmes=[]; failures=[]
    for pmc in SOURCES:
        path=Path(source_dir)/(pmc+'.xml')
        try:
            raw=path.read_bytes()
            programmes.extend(compile_programme(p) for p in extract(pmc,raw))
        except (OSError, InvalidProgramme) as error:
            failures.append({'pmcid':pmc,'error':type(error).__name__,'reason':str(error)})
    return {'schema_version':2,'engine_version':ENGINE_VERSION,'programmes':programmes,
            'failures':failures,'source_count':len(set(p['definition']['source']['pmcid'] for p in programmes)),
            'programme_count':len(programmes),'scientific_approval':False,
            'excluded_arms':[{'pmcid':'PMC6974452','arm':'ISO','reason':'Post-set isometric intervention requires a separate event contract; not silently omitted.'}]}

def store_database(path, catalog):
    """Append immutable versions; a failed batch never replaces the previous active catalog."""
    if catalog['failures'] or not catalog['programmes']:
        raise InvalidProgramme('Incomplete batch cannot replace active catalog')
    connection=sqlite3.connect(path)
    try:
        connection.execute('pragma foreign_keys=on')
        with connection:
            connection.execute('create table if not exists programmes (id text not null, version text not null, payload text not null, primary key(id,version))')
            connection.execute('create table if not exists releases (id text primary key, payload text not null)')
            connection.execute('create table if not exists state (singleton integer primary key check(singleton=1), release_id text not null references releases(id))')
            for p in catalog['programmes']:
                payload=json.dumps(p,ensure_ascii=False,sort_keys=True,allow_nan=False)
                old=connection.execute('select payload from programmes where id=? and version=?',(p['programme_id'],p['programme_version'])).fetchone()
                if old and old[0]!=payload: raise InvalidProgramme('Immutable version collision')
                connection.execute('insert or ignore into programmes values (?,?,?)',(p['programme_id'],p['programme_version'],payload))
            release=digest(catalog)
            connection.execute('insert or ignore into releases values (?,?)',(release,json.dumps(catalog,ensure_ascii=False,sort_keys=True)))
            connection.execute('insert into state values (1,?) on conflict(singleton) do update set release_id=excluded.release_id',(release,))
        return release
    finally:
        connection.close()

def read_database(path):
    connection=sqlite3.connect('file:'+str(Path(path).resolve())+'?mode=ro',uri=True)
    try:
        row=connection.execute('select r.payload from releases r join state s on s.release_id=r.id where s.singleton=1').fetchone()
        if not row: raise InvalidProgramme('No active catalog')
        return json.loads(row[0])
    finally:
        connection.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-dir',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--database')
    args=parser.parse_args()
    result=build(args.source_dir)
    if result['failures']:
        print(json.dumps(result['failures'],ensure_ascii=False))
        raise SystemExit(1)
    destination=Path(args.output);destination.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=destination.parent,prefix='.research-v2-')
    try:
        with os.fdopen(fd,'w') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
        if args.database:store_database(args.database,result)
        os.replace(tmp,destination)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    print(json.dumps({'sources':result['source_count'],'programmes':result['programme_count'],
                      'sessions':sum(p['session_count'] for p in result['programmes']),
                      'sets':sum(p['working_set_count'] for p in result['programmes'])}))

if __name__=='__main__':main()
