# tool_registry.py —— 工具注册、MCP 服务端/客户端
import json, asyncio, subprocess
from mcp import Server, ClientSession
from mcp.server.stdio import stdio_server
from mcp.client.stdio import stdio_client

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.mcp_server = None
        self.mcp_clients = {}

    def register_local(self, name, func, description, params_schema):
        self.tools[name] = {"func": func, "desc": description, "params": params_schema}

    async def start_mcp_server(self):
        server = Server("MindForge")
        @server.call_tool()
        async def call_tool(name: str, arguments: dict):
            if name in self.tools:
                return await self.tools[name]["func"](**arguments)
            raise ValueError(f"Unknown tool: {name}")
        async with stdio_server() as (read, write):
            await server.run(read, write)

    async def connect_mcp_client(self, server_name, command):
        transport = await stdio_client(command)
        session = await ClientSession.create(transport)
        await session.initialize()
        self.mcp_clients[server_name] = session
