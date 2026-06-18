# intelligence/mcp_client.py —— MCP 客户端
import asyncio, logging
from typing import Any
from mcp import ClientSession
from mcp.client.stdio import stdio_client

logger = logging.getLogger("MCPClient")

class MCPClient:
    def __init__(self):
        self.servers = {}

    async def connect_stdio(self, server_name: str, command: str, args: list[str] = None):
        transport = await stdio_client(command, args or [])
        session = await ClientSession.create(transport)
        await session.initialize()
        self.servers[server_name] = {"session": session, "transport": transport}

    async def list_tools(self, server_name: str):
        return await self.servers[server_name]["session"].list_tools()

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict) -> Any:
        return await self.servers[server_name]["session"].call_tool(tool_name, arguments)

    async def close_all(self):
        for info in self.servers.values():
            await info["session"].close()

_client = None
def get_mcp_client() -> MCPClient:
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
