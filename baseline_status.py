"""Bounded anonymous GitHub main lookup and locally evidenced commit relation."""
from datetime import datetime, timezone
import http.client
import json
import re
import subprocess
from project_status import ProjectStatus, QueryError


class BaselineStatus:
    def __init__(self, status: ProjectStatus, repository: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", repository) or repository.split('/')[1] in ('.', '..'):
            raise ValueError("Expected a fixed GitHub owner/repository identifier")
        self.status = status
        self.repository = repository

    def remote(self):
        result = dict(source="github_https_api", repository=self.repository, branch="main",
                      queried_at=datetime.now(timezone.utc).isoformat(), ok=False)
        connection = http.client.HTTPSConnection("api.github.com", timeout=10)
        try:
            connection.request("GET", f"/repos/{self.repository}/git/ref/heads/main", headers={
                "User-Agent": "project-baseline-status", "Accept": "application/vnd.github+json",
                "Cache-Control": "no-cache", "X-GitHub-Api-Version": "2022-11-28"})
            response = connection.getresponse()
            if response.status != 200:
                result["error"] = f"HTTP_{response.status}"
                return result
            payload = response.read(65537)
            if len(payload) > 65536:
                raise ValueError("Response too large")
            data = json.loads(payload)
            sha = data["object"]["sha"]
            if data.get("ref") != "refs/heads/main" or data["object"].get("type") != "commit" or not re.fullmatch(r"[0-9a-f]{40}", sha):
                raise ValueError("Invalid reference")
            result.update(ok=True, sha=sha)
        except (OSError, http.client.HTTPException):
            result["error"] = "NETWORK_UNAVAILABLE"
        except (ValueError, KeyError, TypeError):
            result["error"] = "INVALID_RESPONSE"
        finally:
            connection.close()
        return result

    def query(self):
        local = self.status.query()
        result = dict(local=local, remote=None, relation="UNKNOWN", evidence="unavailable")
        if not local["ok"]:
            return result
        remote = result["remote"] = self.remote()
        if not remote["ok"]:
            return result
        try:
            # Revalidate boundaries after the network wait; do not trust a stale local snapshot.
            again = self.status.query()
            if not again["ok"] or again["head"] != local["head"] or again["branch"] != local["branch"]:
                result["evidence"] = "local_changed_during_query"
                return result
            run = self.status._run
            if run("rev-parse", "--is-shallow-repository").strip() != b"false":
                result["evidence"] = "shallow_history"
                return result
            if run("for-each-ref", "--format=%(refname)", "refs/replace").strip() or (self.status.authorized / '.git/info/grafts').exists():
                result["evidence"] = "rewritten_history"
                return result
            run("cat-file", "-e", remote["sha"] + "^{commit}")
            ahead, behind = map(int, run("rev-list", "--left-right", "--count", local["head"] + "..." + remote["sha"]).split())
            result.update(ahead=ahead, behind=behind, evidence="complete_local_commit_graph",
                          relation="SAME" if not ahead and not behind else "AHEAD" if not behind else "BEHIND" if not ahead else "DIVERGED")
        except (OSError, ValueError, QueryError, subprocess.TimeoutExpired):
            # Git stderr/exception text can contain private data. Never expose it.
            result["evidence"] = "commit_graph_unavailable"
        return result
