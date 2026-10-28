"""Local stdio adapter; the operator, never the model, chooses the project."""
import argparse
from typing import Any
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from project_status import ProjectStatus
from baseline_status import BaselineStatus


def create_server(project: str, github_repository: str | None = None) -> MCPServer:
    status = ProjectStatus(project)
    server = MCPServer("authorized-project-status")

    @server.tool(structured_output=True, annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False))
    def get_project_status() -> dict[str, Any]:
        """Read local branch, HEAD and change counts for the sole configured project. No remote query or file contents."""
        return status.query()

    if github_repository is not None:
        baseline = BaselineStatus(status, github_repository)

        @server.tool(structured_output=True, annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=True))
        def get_project_baseline_status() -> dict[str, Any]:
            """Query the operator-configured public GitHub main and compare using local commit evidence. Never sync."""
            return baseline.query()

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Operator-authorized Git repository root")
    parser.add_argument("--github-repository", help="Fixed public GitHub owner/repository; enables baseline query")
    args = parser.parse_args()
    create_server(args.project, args.github_repository).run(transport="stdio")
