"""Local stdio adapter; the operator, never the model, chooses the project."""
import argparse
from typing import Any
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from project_status import ProjectStatus


def create_server(project: str) -> MCPServer:
    status = ProjectStatus(project)
    server = MCPServer("authorized-project-status")

    @server.tool(structured_output=True, annotations=ToolAnnotations(read_only_hint=True, destructive_hint=False, open_world_hint=False))
    def get_project_status() -> dict[str, Any]:
        """Read local branch, HEAD and change counts for the sole configured project. No remote query or file contents."""
        return status.query()

    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="Operator-authorized Git repository root")
    create_server(parser.parse_args().project).run(transport="stdio")
