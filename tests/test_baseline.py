import json
import unittest
from unittest.mock import patch
from baseline_status import BaselineStatus
from project_status import ProjectStatus
import test_status


class BaselineTests(unittest.TestCase):
    setUp = test_status.StatusTests.setUp
    git = test_status.StatusTests.git
    def baseline(self, sha):
        obj = BaselineStatus(ProjectStatus(str(self.root)), 'Cha-wei/personal-ai-assistant')
        obj.remote = lambda: dict(ok=True, sha=sha)
        return obj

    def test_relations_and_dirty_independent(self):
        first = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.baseline(first).query()['relation'], 'SAME')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-m', 'next')
        second = self.git('rev-parse', 'HEAD')
        (self.root / 'untracked').write_text('private')
        result = self.baseline(first).query()
        self.assertEqual(result['relation'], 'AHEAD')
        self.assertFalse(result['local']['clean'])
        self.git('checkout', '--detach', first)
        self.assertEqual(self.baseline(second).query()['relation'], 'BEHIND')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-m', 'fork')
        self.assertEqual(self.baseline(second).query()['relation'], 'DIVERGED')
        self.assertEqual(self.baseline('0'*40).query()['relation'], 'UNKNOWN')

    def test_http_and_failures(self):
        obj = BaselineStatus(ProjectStatus(str(self.root)), 'Cha-wei/personal-ai-assistant')
        with patch('baseline_status.http.client.HTTPSConnection') as cls:
            response = cls.return_value.getresponse.return_value
            response.status = 200
            response.read.return_value = json.dumps(dict(ref='refs/heads/main', object=dict(type='commit', sha='a'*40))).encode()
            self.assertEqual(obj.remote()['sha'], 'a'*40)
            for code in (403, 404, 429, 500, 302):
                response.status = code
                self.assertEqual(obj.query()['relation'], 'UNKNOWN')
            response.status = 200
            response.read.return_value = b'bad'
            self.assertEqual(obj.remote()['error'], 'INVALID_RESPONSE')
            cls.return_value.getresponse.side_effect = TimeoutError('secret')
            result = obj.query()
            self.assertEqual(result['relation'], 'UNKNOWN')
            self.assertNotIn('secret', str(result))
            cls.assert_called_with('api.github.com', timeout=10)

    def test_target_validation(self):
        for value in ('https://evil/x', 'a/b/c', 'a/..', 'a/b?x', 'a/b\r\nx'):
            with self.assertRaises(ValueError):
                BaselineStatus(ProjectStatus(str(self.root)), value)

    def test_incomplete_or_rewritten_graph_is_unknown(self):
        sha = self.git('rev-parse', 'HEAD')
        obj = self.baseline(sha)
        (self.root / '.git' / 'shallow').write_text(sha + '\n')
        self.assertEqual(obj.query()['evidence'], 'shallow_history')
        (self.root / '.git' / 'shallow').unlink()
        self.git('replace', sha, sha)
        self.assertEqual(obj.query()['evidence'], 'rewritten_history')
