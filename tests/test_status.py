import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from project_status import ProjectStatus


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-b", "main")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--allow-empty", "-m", "initial")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], stderr=subprocess.DEVNULL).decode().strip()

    def test_clean_and_git_agreement(self):
        result = ProjectStatus(str(self.root)).query()
        self.assertTrue(result["ok"])
        self.assertTrue(result["clean"])
        self.assertEqual(result["head"], self.git("rev-parse", "HEAD"))
        self.assertEqual(result["branch"], self.git("branch", "--show-current"))
        self.assertFalse(result["remote_checked"])

    def test_changes_and_rename(self):
        (self.root / "tracked").write_text("one")
        self.git("add", "tracked")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "file")
        self.git("mv", "tracked", "renamed")
        (self.root / "renamed").write_text("two")
        (self.root / "private-name").write_text("secret-content")
        result = ProjectStatus(str(self.root)).query()
        self.assertFalse(result["clean"])
        self.assertEqual(result["changes"], dict(staged=1, unstaged=1, untracked=1, conflicted=0))
        self.assertNotIn("secret-content", str(result))
        self.assertNotIn("private-name", str(result))

    def test_detached(self):
        self.git("checkout", "--detach")
        result = ProjectStatus(str(self.root)).query()
        self.assertTrue(result["detached_head"])
        self.assertIsNone(result["branch"])

    def test_invalid_paths_and_nested_boundary(self):
        nested = self.root / "nested"
        nested.mkdir()
        for path in (nested, self.root / "missing"):
            self.assertFalse(ProjectStatus(str(path)).query()["ok"])

    def test_git_unavailable(self):
        with patch("project_status.shutil.which", return_value=None):
            self.assertEqual(ProjectStatus(str(self.root)).query()["error"]["code"], "GIT_UNAVAILABLE")

    def test_deleted_authorized_path(self):
        directory = self.root / "vanishing"
        directory.mkdir()
        status = ProjectStatus(str(directory))
        directory.rmdir()
        self.assertEqual(status.query()["error"]["code"], "PATH_UNAVAILABLE")

    def test_fixed_commands_use_no_shell_and_no_optional_locks(self):
        real_run = subprocess.run
        with patch("project_status.subprocess.run", wraps=real_run) as invoked:
            self.assertTrue(ProjectStatus(str(self.root)).query()["ok"])
            for call in invoked.call_args_list:
                self.assertFalse(call.kwargs["shell"])
                self.assertEqual(call.kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
                self.assertIn("core.fsmonitor=false", call.args[0])
                self.assertNotIn("fetch", call.args[0])
                self.assertNotIn("pull", call.args[0])

    def test_environment_cannot_redirect(self):
        with patch.dict(os.environ, {"GIT_DIR": str(self.root / "missing"), "GIT_WORK_TREE": "Z:/outside"}):
            self.assertTrue(ProjectStatus(str(self.root)).query()["ok"])

    def test_gitfile_rejected(self):
        nested = self.root / "nested"
        nested.mkdir()
        (nested / ".git").write_text("gitdir: ../.git")
        self.assertEqual(ProjectStatus(str(nested)).query()["error"]["code"], "REPOSITORY_BOUNDARY_OR_NOT_GIT")

    def test_external_objects_rejected(self):
        info = self.root / ".git" / "objects" / "info"
        (info / "alternates").write_text("Z:/outside")
        self.assertEqual(ProjectStatus(str(self.root)).query()["error"]["code"], "EXTERNAL_GIT_STORAGE_UNSUPPORTED")

    def test_unsafe_configuration_rejected_before_git(self):
        config = self.root / ".git" / "config"
        original = config.read_text()
        for extra in ('[filter "probe"]\n clean = python evil.py\n', '[include]\n path = Z:/outside\n', '[core]\n worktree = Z:/outside\n', '[core]\n excludesFile = Z:/outside\n'):
            config.write_text(original + extra)
            with patch("project_status.subprocess.run") as run:
                self.assertEqual(ProjectStatus(str(self.root)).query()["error"]["code"], "UNSUPPORTED_GIT_CONFIGURATION")
                run.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows junction boundary")
    def test_untracked_junction_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            (Path(outside) / "private").write_text("private")
            link = self.root / "escape"
            subprocess.run(["cmd", "/c", "mklink", "/J", str(link), outside], check=True, stdout=subprocess.DEVNULL)
            try:
                with patch("project_status.subprocess.run") as run:
                    self.assertEqual(ProjectStatus(str(self.root)).query()["error"]["code"], "LINKED_PROJECT_ENTRY_UNSUPPORTED")
                    run.assert_not_called()
            finally:
                os.rmdir(link)

    def test_timeout_and_failure_sanitized(self):
        with patch("project_status.subprocess.run", side_effect=subprocess.TimeoutExpired("git", 15)):
            self.assertEqual(ProjectStatus(str(self.root)).query()["error"]["code"], "GIT_TIMEOUT")
        with patch("project_status.subprocess.run", return_value=subprocess.CompletedProcess([], 1, b"", b"secret")):
            result = ProjectStatus(str(self.root)).query()
            self.assertEqual(result["error"]["code"], "GIT_QUERY_FAILED")
            self.assertNotIn("secret", str(result))


if __name__ == "__main__":
    unittest.main()
