import json
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from registry import Registry, RegistryError
from registered_queries import GitHub, GitHubError, RegisteredQueries
from credentials import WindowsCredentials, CredentialError

SOURCE = dict(location='owner/repo', access='public', credential_ref=None)
SHA = 'a' * 40
OTHER = 'b' * 40
MARKER = 'PATCH_SECRET_UNIQUE_T04'

class Response:
    status = 200
    def __init__(self, body=None, status=200, headers=None):
        self.body = json.dumps(body or {}).encode(); self.status = status; self.headers = headers or {}
    def read(self, limit): return self.body[:limit]
    def getheader(self, name): return self.headers.get(name)

class Connection:
    def __init__(self, response): self.response=response; self.calls=[]
    def request(self, *args, **kwargs): self.calls.append((args, kwargs))
    def getresponse(self): return self.response
    def close(self): pass

class RegistryTests(unittest.TestCase):
    def test_persistence_explicit_link_update_and_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'registry.db'
            db = Registry(path, writable=True)
            project = db.project('example')
            source = db.source('github','Owner/Repo', access='public')
            self.assertIsNone(db.get(source)['project_id'])
            db.link(source, project)
            db.update(source, 'Owner/Other', 'private', 'test-ref')
            db.close()
            db = Registry(path)
            self.assertEqual(db.get(source)['project_id'], project)
            self.assertEqual(db.get(source)['location'], 'owner/other')
            with self.assertRaises(RegistryError): db.link(source, None)
            self.assertNotIn('credential_ref', db.catalog()['sources'][0])
            self.assertEqual(RegisteredQueries(db).query('unknown')['error'], 'SOURCE_NOT_REGISTERED')
            db.close()
            db=Registry(path,writable=True); db.link(source,None); self.assertIsNone(db.get(source)['project_id']); db.close()

    def test_invalid_repositories_and_public_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Registry(Path(folder)/'r.db',writable=True)
            for name in ['https://github.com/a/b','other.com/a/b','../repo','a/..','a/b?x=1']:
                with self.assertRaises(RegistryError): db.source('github',name,access='public')
            with self.assertRaises(RegistryError): db.source('github','a/b',access='public',credential_ref='secret')
            with self.assertRaises(RegistryError): db.source('github','a/b',access='private')
            db.close()

class GitHubTests(unittest.TestCase):
    def test_transport_public_never_credentials_and_redirects(self):
        conn=Connection(Response({'ok':True}))
        with patch('registered_queries.http.client.HTTPSConnection',return_value=conn) as factory, patch('registered_queries.WindowsCredentials',side_effect=AssertionError):
            self.assertEqual(GitHub(SOURCE).request(''), {'ok':True})
            factory.assert_called_once_with('api.github.com',timeout=10)
            self.assertEqual(conn.calls[0][0][0], 'GET')
            self.assertNotIn('Authorization',conn.calls[0][1]['headers'])
        for status,code in [(301,'PERMISSION_OR_POLICY_DENIED'),(401,'CREDENTIAL_REJECTED'),(404,'REPOSITORY_UNAVAILABLE_OR_NOT_AUTHORIZED'),(403,'PERMISSION_OR_POLICY_DENIED'),(429,'RATE_LIMITED')]:
            with patch('registered_queries.http.client.HTTPSConnection',return_value=Connection(Response(status=status))):
                with self.assertRaisesRegex(GitHubError,code): GitHub(SOURCE).request('')

    def test_private_fails_without_anonymous_retry(self):
        class Missing:
            def get(self,ref): raise CredentialError('CREDENTIAL_NOT_CONFIGURED')
        with patch('registered_queries.http.client.HTTPSConnection') as factory:
            with self.assertRaises(CredentialError): GitHub(dict(SOURCE,access='private',credential_ref='test'),Missing()).request('')
            factory.assert_not_called()

    def test_size_invalid_and_network(self):
        response=Response(); response.body=b'x'*(2*1024*1024+1)
        for resp,code in [(response,'RESPONSE_TOO_LARGE'),(Response([]),'INVALID_RESPONSE')]:
            if code=='INVALID_RESPONSE': resp.body=b'['
            with patch('registered_queries.http.client.HTTPSConnection',return_value=Connection(resp)):
                with self.assertRaisesRegex(GitHubError,code): GitHub(SOURCE).request('')
        with patch('registered_queries.http.client.HTTPSConnection',side_effect=OSError):
            with self.assertRaisesRegex(GitHubError,'NETWORK_UNAVAILABLE'): GitHub(SOURCE).request('')

    def fixture(self):
        return dict(status='ahead',base_commit={'sha':SHA},total_commits=1,
                    commits=[{'sha':OTHER,'commit':{'message':'title\nbody'}}],
                    files=[dict(filename='x.py',status='modified',additions=1,deletions=0,changes=1,patch=MARKER)],patch=MARKER)

    def test_allowlist_patch_and_incomplete(self):
        data=self.fixture()
        with patch.object(GitHub,'request',return_value=data): result=GitHub(SOURCE).compare(SHA,OTHER)
        self.assertNotIn(MARKER,json.dumps(result)); self.assertNotIn('patch',json.dumps(result))
        self.assertTrue(result['complete']); self.assertEqual(result['commits'][0]['title'],'title')
        data['files']*=300
        with patch.object(GitHub,'request',return_value=data): result=GitHub(SOURCE).compare(SHA,OTHER)
        self.assertFalse(result['complete']); self.assertEqual(result['error'],'INCOMPLETE_COMPARE')
        data=self.fixture(); del data['files']
        with tempfile.TemporaryDirectory() as folder:
            db=Registry(Path(folder)/'r.db',writable=True); identifier=db.source('github','owner/repo',access='public')
            with patch.object(GitHub,'request',return_value=data): result=RegisteredQueries(db).query(identifier,SHA,OTHER)
            self.assertEqual(result['error'],'INVALID_RESPONSE'); db.close()
            self.assertNotIn(MARKER,(Path(folder)/'r.db').read_bytes().decode('latin1'))

    def test_default_branch_is_dynamic(self):
        with patch.object(GitHub,'request',side_effect=[dict(full_name='owner/repo',private=False,default_branch='release/x'),dict(ref='refs/heads/release/x',object=dict(type='commit',sha=SHA))]) as request:
            result=GitHub(SOURCE).metadata()
            self.assertEqual(result['default_branch'],'release/x'); self.assertEqual(request.call_args.args[0],'/git/ref/heads/release%2Fx')

class WindowsStoreTests(unittest.TestCase):
    def test_real_windows_roundtrip_update_delete(self):
        import os, uuid
        if os.name!='nt': self.skipTest('Windows required')
        store=WindowsCredentials(); reference='t04-test-'+uuid.uuid4().hex
        try:
            store.set(reference,'SIMULATED_TOKEN_ONE'); self.assertEqual(store.get(reference),'SIMULATED_TOKEN_ONE')
            store.set(reference,'SIMULATED_TOKEN_TWO'); self.assertEqual(store.get(reference),'SIMULATED_TOKEN_TWO')
        finally: store.delete(reference)
        with self.assertRaisesRegex(CredentialError,'CREDENTIAL_NOT_CONFIGURED'): store.get(reference)

class RegisteredMCPTests(unittest.TestCase):
    def test_real_stdio_schema_and_unknown_source(self):
        import asyncio, os, sys
        from mcp import Client
        from mcp.client.stdio import StdioServerParameters
        async def check(folder):
            env=dict(os.environ, LOCALAPPDATA=folder)
            with patch.dict(os.environ, env):
                db=Registry(writable=True); db.close()
            root=Path(__file__).resolve().parents[1]
            params=StdioServerParameters(command=sys.executable,args=[str(root/'registry_mcp.py')],env=env)
            async with Client(params) as client:
                tools=(await client.list_tools()).tools
                self.assertEqual({t.name for t in tools},{'list_registered_projects','get_registered_source_status','compare_registered_github_commits'})
                for tool in tools:
                    self.assertNotIn('path',tool.input_schema.get('properties',{}))
                result=await client.call_tool('list_registered_projects',{})
                self.assertFalse(result.is_error)
                result=await client.call_tool('get_registered_source_status',{'source_id':'unknown'})
                self.assertEqual(result.structured_content['error'],'SOURCE_NOT_REGISTERED')
        with tempfile.TemporaryDirectory() as folder: asyncio.run(check(folder))

class SecurityBoundaryTests(unittest.TestCase):
    def test_private_header_and_no_retry(self):
        class Store:
            def get(self,ref): return 'SIMULATED_PRIVATE_TOKEN'
        for status in (200,401,403,404):
            conn=Connection(Response(status=status))
            captured=[]
            original=conn.request
            def capture(*args,**kwargs):
                captured.append(dict(kwargs['headers'])); original(*args,**kwargs)
            conn.request=capture
            with patch('registered_queries.http.client.HTTPSConnection',return_value=conn):
                try: GitHub(dict(SOURCE,access='private',credential_ref='ref'),Store()).request('')
                except GitHubError: pass
            self.assertEqual(len(captured),1)
            self.assertEqual(captured[0]['Authorization'],'Bearer SIMULATED_PRIVATE_TOKEN')

    def test_remove_revokes_access(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Registry(Path(folder)/'r.db',writable=True)
            source=db.source('github','a/b',access='public'); db.remove(source)
            self.assertEqual(RegisteredQueries(db).query(source)['error'],'SOURCE_NOT_REGISTERED'); db.close()

    def test_local_redirect_rejected_before_git(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Registry(Path(folder)/'r.db',writable=True)
            # Simulate an authorized path now resolving to a different target.
            db.write('INSERT INTO sources VALUES(?,?,?,?,?,?,?)',('s',None,'local',folder,None,None,'now'))
            with patch('registered_queries.Path.resolve',return_value=Path(folder)/'elsewhere'), patch('registered_queries.ProjectStatus') as git:
                self.assertEqual(RegisteredQueries(db).query('s')['error'],'LOCAL_SOURCE_UNAVAILABLE'); git.assert_not_called()
            db.close()

    def test_patch_never_enters_adapter_logs_or_errors(self):
        import asyncio, contextlib, io, logging
        from registry_mcp import create_registry_server
        async def check(db, identifier):
            with patch('registry_mcp.Registry',return_value=db): server=create_registry_server()
            data=GitHubTests().fixture()
            captured=io.StringIO(); handler=logging.StreamHandler(captured); logging.getLogger().addHandler(handler)
            try:
                with contextlib.redirect_stdout(captured), contextlib.redirect_stderr(captured), patch.object(GitHub,'request',return_value=data):
                    result=await server.call_tool('compare_registered_github_commits',{'source_id':identifier,'base_sha':SHA,'head_sha':OTHER})
                self.assertNotIn(MARKER,str(result)); self.assertNotIn(MARKER,captured.getvalue())
                del data['files']
                with patch.object(GitHub,'request',return_value=data):
                    result=await server.call_tool('compare_registered_github_commits',{'source_id':identifier,'base_sha':SHA,'head_sha':OTHER})
                self.assertNotIn(MARKER,str(result)); self.assertIn('INVALID_RESPONSE',str(result))
            finally: logging.getLogger().removeHandler(handler)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'r.db'; db=Registry(path,writable=True); identifier=db.source('github','owner/repo',access='public')
            asyncio.run(check(db,identifier)); db.close(); self.assertNotIn(MARKER.encode(),path.read_bytes())
