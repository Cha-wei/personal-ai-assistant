"""Minimal operator-owned registry; query consumers open SQLite read-only."""
import os
from pathlib import Path
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from project_status import ProjectStatus

class RegistryError(Exception):
    pass

def database_path():
    root = os.environ.get('LOCALAPPDATA')
    if not root or not Path(root).is_absolute():
        raise RegistryError('REGISTRY_UNAVAILABLE')
    return Path(root) / 'personal-ai-assistant' / 'registry.sqlite3'

def repository_name(value):
    if not isinstance(value, str) or len(value) > 200 or not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+', value) or value.split('/')[1] in ('.', '..'):
        raise RegistryError('INVALID_REPOSITORY')
    return value.lower()

class Registry:
    def __init__(self, path=None, *, writable=False):
        self.path = Path(path) if path else database_path()
        self.writable = writable
        if writable:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path.resolve().as_uri() + ('?mode=rwc' if writable else '?mode=ro'), uri=True, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        version = self.db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0, 1) or (version == 0 and not writable):
            self.db.close()
            raise RegistryError('UNSUPPORTED_SCHEMA')
        if version == 0:
            self.db.executescript('''CREATE TABLE projects(id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE sources(id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id), kind TEXT NOT NULL,
            location TEXT NOT NULL, access TEXT, credential_ref TEXT, created_at TEXT NOT NULL);
            PRAGMA user_version=1;''')

    def close(self):
        self.db.close()

    def write(self, sql, args):
        if not self.writable:
            raise RegistryError('PERMISSION_OR_POLICY_DENIED')
        with self.db:
            self.db.execute(sql, args)

    def project(self, name):
        if not isinstance(name, str) or not name.strip() or len(name) > 200 or any(ord(c) < 32 for c in name):
            raise RegistryError('INVALID_PROJECT_NAME')
        identifier = str(uuid.uuid4())
        self.write('INSERT INTO projects VALUES(?,?,?)', (identifier, name, datetime.now(timezone.utc).isoformat()))
        return identifier

    def source(self, kind, location, project_id=None, access=None, credential_ref=None):
        location, access, credential_ref = self.validate(kind, location, access, credential_ref)
        identifier = str(uuid.uuid4())
        self.write('INSERT INTO sources VALUES(?,?,?,?,?,?,?)', (identifier, project_id, kind, location, access, credential_ref, datetime.now(timezone.utc).isoformat()))
        return identifier

    def validate(self, kind, location, access, reference):
        if kind == 'local':
            result = ProjectStatus(location).query()
            if not result['ok']:
                raise RegistryError('LOCAL_SOURCE_UNAVAILABLE')
            return result['project_path'], None, None
        if kind != 'github' or access not in ('public', 'private'):
            raise RegistryError('INVALID_SOURCE')
        location = repository_name(location)
        if access == 'private' and (not reference or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', reference)):
            raise RegistryError('CREDENTIAL_NOT_CONFIGURED')
        if access == 'public' and reference:
            raise RegistryError('PERMISSION_OR_POLICY_DENIED')
        return location, access, reference

    def get(self, identifier):
        row = self.db.execute('SELECT * FROM sources WHERE id=?', (identifier,)).fetchone()
        if row is None:
            raise RegistryError('SOURCE_NOT_REGISTERED')
        return dict(row)

    def catalog(self):
        return {'projects': [dict(r) for r in self.db.execute('SELECT * FROM projects ORDER BY id')],
                'sources': [dict(r) for r in self.db.execute('SELECT id,project_id,kind,location,access,created_at FROM sources ORDER BY id')]}

    def link(self, identifier, project_id):
        self.get(identifier)
        self.write('UPDATE sources SET project_id=? WHERE id=?', (project_id, identifier))

    def update(self, identifier, location, access=None, credential_ref=None):
        row = self.get(identifier)
        location, access, credential_ref = self.validate(row['kind'], location, access, credential_ref)
        self.write('UPDATE sources SET location=?,access=?,credential_ref=? WHERE id=?', (location, access, credential_ref, identifier))

    def rename(self, identifier, name):
        if not name or len(name) > 200 or any(ord(c) < 32 for c in name):
            raise RegistryError('INVALID_PROJECT_NAME')
        self.write('UPDATE projects SET name=? WHERE id=?', (name, identifier))

    def remove(self, identifier):
        self.get(identifier)
        self.write('DELETE FROM sources WHERE id=?', (identifier,))
