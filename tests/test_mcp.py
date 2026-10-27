import asyncio
from pathlib import Path
import sys
import unittest
from mcp import Client
from mcp.client.stdio import StdioServerParameters


class MCPTests(unittest.TestCase):
    def test_stdio_schema_and_path_input_cannot_redirect(self):
        async def check():
            root = Path(__file__).resolve().parents[1]
            params = StdioServerParameters(command=sys.executable, args=[str(root / "mcp_server.py"), "--project", str(root)])
            async with Client(params) as client:
                tools = (await client.list_tools()).tools
                self.assertEqual([t.name for t in tools], ["get_project_status"])
                self.assertFalse(tools[0].input_schema.get("properties"))
                result = await client.call_tool("get_project_status", {})
                self.assertFalse(result.is_error)
                self.assertTrue(result.structured_content["ok"])
                invalid = await client.call_tool("get_project_status", {"project": "C:/"})
                # SDK ignores extra arguments; they must never alter the fixed target.
                self.assertEqual(invalid.structured_content["project_path"], str(root))
        asyncio.run(check())
