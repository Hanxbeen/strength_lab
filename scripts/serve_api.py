"""Start the real Supabase-backed API without coupling it to a hosting provider."""
import argparse
import os
from urllib.parse import urlsplit

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--ssl-certfile')
    parser.add_argument('--ssl-keyfile')
    args=parser.parse_args()
    required=('SUPABASE_URL','SUPABASE_PUBLISHABLE_KEY','WORKOUT_POSTGRES_DSN')
    missing=[key for key in required if not os.environ.get(key)]
    if missing:parser.error('Missing environment variable names: '+', '.join(missing))
    if urlsplit(os.environ['SUPABASE_URL']).scheme!='https':
        parser.error('SUPABASE_URL must use HTTPS')
    if bool(args.ssl_certfile)!=bool(args.ssl_keyfile):
        parser.error('Provide both TLS certificate and private key')
    # The supported runner never silently uses a local SQLite ledger.
    os.environ.setdefault('MUGEMUGE_ENV','staging')
    import uvicorn
    uvicorn.run('backend.main:app',host=args.host,port=args.port,
                ssl_certfile=args.ssl_certfile,ssl_keyfile=args.ssl_keyfile)

if __name__=='__main__':main()
