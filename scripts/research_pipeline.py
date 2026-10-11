"""Run discovery -> evidence -> automatic assessment -> atomic DB import.

--persist requires an already configured PostgreSQL connection in the runner.
Credentials stay in the environment; connection errors are not echoed.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlsplit, unquote
from scripts.research_store import FILES, build_sql

def persist(sql):
    url = os.environ.get('RESEARCH_DATABASE_URL', '')
    if not url:
        raise RuntimeError('RESEARCH_DATABASE_URL is required; no DB write occurred')
    connection = urlsplit(url)
    if connection.scheme not in ('postgres', 'postgresql') or not connection.hostname or not connection.password:
        raise RuntimeError('Invalid research database connection')
    env = os.environ.copy()
    env.update(PGHOST=connection.hostname, PGPORT=str(connection.port or 5432),
               PGUSER=unquote(connection.username or ''), PGPASSWORD=unquote(connection.password),
               PGDATABASE=unquote(connection.path.lstrip('/')), PGSSLMODE='require', PGCONNECT_TIMEOUT='15')
    # No SQL/credential-bearing stderr is printed. Transaction errors exit nonzero.
    done = subprocess.run(['psql', '-X', '--no-password', '-v', 'ON_ERROR_STOP=1', '-q'],
                          input=sql, text=True, env=env, capture_output=True, timeout=90)
    if done.returncode:
        raise RuntimeError('Research DB transaction failed; inspect protected runner logs')

def run(module, *args):
    subprocess.run([sys.executable, '-m', 'scripts.'+module, *map(str,args)], check=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--directory', required=True)
    parser.add_argument('--reuse-discovery', action='store_true')
    parser.add_argument('--persist', action='store_true')
    parser.add_argument('--limit', type=int, default=20)
    parser.add_argument('--pool', type=int, default=100)
    args = parser.parse_args()
    if args.persist and not os.environ.get('RESEARCH_DATABASE_URL'):
        parser.error('RESEARCH_DATABASE_URL is required for --persist')
    folder = Path(args.directory); folder.mkdir(parents=True, exist_ok=True)
    discovery = folder/'oa_candidates_v2.json'
    run('research_gold_eval')
    if not args.reuse_discovery:
        run('research_oa_v2', '--pool', args.pool, '--limit', args.limit, '--output', discovery)
    for module, source, output in [
        ('research_evidence_gate', discovery, 'evidence_audit'),
        ('research_protocol_audit', discovery, 'protocol_audit'),
        ('research_review_queue', folder/'protocol_audit.json', 'review_queue'),
        ('research_release_gate', folder/'review_queue.json', 'release_gate'),
    ]:
        run(module, '--input', source, '--output', folder/(output+'.json'))
    run('research_automatic_assessment', '--directory', folder)
    documents = {name: json.loads((folder/(name+'.json')).read_text())
                 for name in (*FILES, 'automatic_assessment')}
    run_id, sql = build_sql(documents)
    (folder/'import.sql').write_text(sql)
    if args.persist:
        persist(sql)
    print(json.dumps({'run_id': run_id, 'stored': args.persist,
                      'checked': documents['automatic_assessment']['automatically_checked']}))

if __name__ == '__main__':
    main()
