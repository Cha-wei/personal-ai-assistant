"""Local operator entry point. Never exposed as MCP tools."""
import argparse
import getpass
import json
import sqlite3
from credentials import WindowsCredentials, CredentialError
from registry import Registry, RegistryError

def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('project'); p.add_argument('name')
    p = commands.add_parser('rename'); p.add_argument('project_id'); p.add_argument('name')
    p = commands.add_parser('source'); p.add_argument('kind', choices=['local','github']); p.add_argument('location'); p.add_argument('--project-id'); p.add_argument('--access', choices=['public','private']); p.add_argument('--credential-ref')
    p = commands.add_parser('update'); p.add_argument('source_id'); p.add_argument('location'); p.add_argument('--access', choices=['public','private']); p.add_argument('--credential-ref')
    p = commands.add_parser('link'); p.add_argument('source_id'); p.add_argument('project_id')
    p = commands.add_parser('unlink'); p.add_argument('source_id')
    p = commands.add_parser('remove-source'); p.add_argument('source_id')
    commands.add_parser('list')
    for name in ('credential-set', 'credential-delete'):
        p = commands.add_parser(name); p.add_argument('reference')
    args = parser.parse_args()
    db = None
    try:
        if args.command.startswith('credential-'):
            store = WindowsCredentials()
            if args.command == 'credential-set':
                # getpass can fall back to echoed input: reject that fallback.
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('error', getpass.GetPassWarning)
                    token = getpass.getpass('Fine-grained PAT (hidden): ')
                try:
                    store.set(args.reference, token)
                finally:
                    del token
            else:
                store.delete(args.reference)
            print(json.dumps({'ok': True}))
            return
        db = Registry(writable=True)
        cmd = args.command
        if cmd == 'project': result = db.project(args.name)
        elif cmd == 'source': result = db.source(args.kind,args.location,args.project_id,args.access,args.credential_ref)
        elif cmd == 'update': result = db.update(args.source_id,args.location,args.access,args.credential_ref)
        elif cmd == 'rename': result = db.rename(args.project_id,args.name)
        elif cmd == 'link': result = db.link(args.source_id,args.project_id)
        elif cmd == 'remove-source': result = db.remove(args.source_id)
        elif cmd == 'unlink': result = db.link(args.source_id,None)
        else: result = db.catalog()
        print(json.dumps({'ok': True, 'result': result}, ensure_ascii=True))
    except (CredentialError, RegistryError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        return 1
    except (sqlite3.Error, OSError, getpass.GetPassWarning):
        print(json.dumps({'ok': False, 'error': 'OPERATOR_OPERATION_FAILED'}))
        return 1
    finally:
        if db is not None: db.close()

if __name__ == '__main__':
    raise SystemExit(main())
