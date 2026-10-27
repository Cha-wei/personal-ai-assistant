"""Read-only Git facts for one operator-authorized repository. No MCP dependency."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import subprocess


class QueryError(Exception):
    pass


ERROR_MESSAGES = {
    "PATH_UNAVAILABLE": "The authorized project directory is missing or inaccessible.",
    "AUTHORIZATION_BOUNDARY": "The project path or Git root no longer matches the authorized directory.",
    "REPOSITORY_BOUNDARY_OR_NOT_GIT": "Expected a repository root with an internal .git directory; non-Git paths and gitfiles are unsupported.",
    "EXTERNAL_GIT_STORAGE_UNSUPPORTED": "External Git common directories and object alternates are unsupported.",
    "UNSUPPORTED_GIT_CONFIGURATION": "Repository configuration is outside the supported safe subset; includes, filters and external paths are not allowed.",
    "LINKED_PROJECT_ENTRY_UNSUPPORTED": "Project symlinks and junctions are unsupported to prevent traversal outside the authorized directory.",
    "GIT_UNAVAILABLE": "System Git was not found on PATH.",
    "GIT_QUERY_FAILED": "Git could not read repository facts; check repository validity, ownership and whether HEAD has a commit.",
    "REPOSITORY_CHANGED_DURING_QUERY": "HEAD or branch changed during the query; retry when the repository is stable.",
}


class ProjectStatus:
    def __init__(self, project: str):
        # Capture the canonical target once; reject later junction/symlink retargeting.
        self.configured = Path(project).absolute()
        self.authorized = self.configured.resolve()

    def _check_metadata(self, metadata: Path):
        # Inspect names/types only. Never follow links, including untracked junctions.
        def inaccessible(_error):
            raise QueryError("PATH_UNAVAILABLE")

        for directory, dirs, files in os.walk(self.authorized, followlinks=False, onerror=inaccessible):
            for name in dirs + files:
                path = Path(directory) / name
                if path.is_symlink() or path.is_junction():
                    raise QueryError("LINKED_PROJECT_ENTRY_UNSUPPORTED")
        allowed = {
            "core": {"repositoryformatversion", "filemode", "bare", "logallrefupdates", "symlinks", "ignorecase", "autocrlf", "eol", "safecrlf"},
            "remote": {"url", "fetch", "pushurl"},
            "branch": {"remote", "merge", "rebase", "description"},
            "user": {"name", "email"},
            "init": {"defaultbranch"},
        }
        section = None
        for line in (metadata / "config").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith(("#", ";")):
                continue
            header = re.fullmatch(r'\[([A-Za-z]+)(?: "[^"\\]*")?\]', line)
            if header:
                section = header[1].lower()
                if section not in allowed:
                    raise QueryError("UNSUPPORTED_GIT_CONFIGURATION")
                continue
            setting = re.fullmatch(r'([A-Za-z][A-Za-z0-9-]*)\s*=\s*(?:"[^"\\]*"|[^"\\]*)', line)
            if not setting or section not in allowed or setting[1].lower() not in allowed[section]:
                raise QueryError("UNSUPPORTED_GIT_CONFIGURATION")

    def query(self) -> dict:
        result = {
            "project_path": str(self.authorized),
            "source": "local_git_cli",
            "queried_at": datetime.now(timezone.utc).isoformat(),
            "remote_checked": False,
            "submodule_contents_checked": False,
        }
        try:
            if not self.configured.is_dir():
                raise QueryError("PATH_UNAVAILABLE")
            if self.configured.resolve() != self.authorized:
                raise QueryError("AUTHORIZATION_BOUNDARY")
            metadata = self.authorized / ".git"
            # Linked worktrees/gitfiles can redirect Git outside the authorized directory.
            if not metadata.is_dir() or metadata.resolve() != metadata.absolute():
                raise QueryError("REPOSITORY_BOUNDARY_OR_NOT_GIT")
            if (metadata / "commondir").exists() or (metadata / "objects" / "info" / "alternates").exists():
                raise QueryError("EXTERNAL_GIT_STORAGE_UNSUPPORTED")
            self._check_metadata(metadata)
            git = shutil.which("git")
            if not git:
                raise QueryError("GIT_UNAVAILABLE")
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
            env.update(GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_ATTR_NOSYSTEM="1", GIT_NO_LAZY_FETCH="1")

            def run(*args):
                completed = subprocess.run(
                    [git, "--no-optional-locks", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
                     "-c", "core.excludesFile=" + os.devnull, "-c", "core.attributesFile=" + os.devnull,
                     "-C", str(self.authorized), *args],
                    env=env, capture_output=True, timeout=15, shell=False,
                )
                if completed.returncode:
                    raise QueryError("GIT_QUERY_FAILED")
                return completed.stdout

            root = Path(os.fsdecode(run("rev-parse", "--show-toplevel").strip())).resolve()
            if root != self.authorized:
                raise QueryError("AUTHORIZATION_BOUNDARY")
            branch = run("rev-parse", "--abbrev-ref", "HEAD").decode("utf-8", "replace").strip()
            head = run("rev-parse", "--verify", "HEAD").decode("ascii").strip()
            raw = run("status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=all")
            counts = {"staged": 0, "unstaged": 0, "untracked": 0, "conflicted": 0}
            entries = iter(raw.split(b"\0"))
            for entry in entries:
                if not entry:
                    continue
                xy = entry[:2]
                if xy == b"??":
                    counts["untracked"] += 1
                elif b"U" in xy or xy in (b"AA", b"DD"):
                    counts["conflicted"] += 1
                else:
                    counts["staged"] += xy[0:1] != b" "
                    counts["unstaged"] += xy[1:2] != b" "
                if b"R" in xy or b"C" in xy:
                    next(entries, None)
            # Detect common concurrent checkout/commit races; this is not an atomic snapshot.
            if run("rev-parse", "--verify", "HEAD").decode("ascii").strip() != head or run("rev-parse", "--abbrev-ref", "HEAD").decode("utf-8", "replace").strip() != branch:
                raise QueryError("REPOSITORY_CHANGED_DURING_QUERY")
            result.update(ok=True, branch=None if branch == "HEAD" else branch,
                          detached_head=branch == "HEAD", head=head, clean=not raw, changes=counts)
        except QueryError as exc:
            result.update(ok=False, error={"code": str(exc), "message": ERROR_MESSAGES[str(exc)]})
        except subprocess.TimeoutExpired:
            result.update(ok=False, error={"code": "GIT_TIMEOUT", "message": "Git query exceeded 15 seconds."})
        except (OSError, ValueError):
            result.update(ok=False, error={"code": "QUERY_UNAVAILABLE", "message": "Authorized project could not be queried."})
        return result
