# intelligence/tool_executor.py —— 支持本地工具和 MCP 工具
import json, re, asyncio
from intelligence.mcp_client import get_mcp_client

TOOLS_DEF = [
    {"name": "run_python", "desc": "在沙箱中执行Python代码", "params": {"code": "string"}},
    {"name": "write_file", "desc": "写入文件", "params": {"filename": "string", "content": "string"}},
    {"name": "run_system_command", "desc": "执行白名单系统命令", "params": {"cmd": "string"}},
    {"name": "open_website", "desc": "打开网址", "params": {"url": "string"}},
    {"name": "search_knowledge_base", "desc": "搜索知识库", "params": {"query": "string"}},
]

class ToolExecutor:
    def __init__(self, sandbox, host_executor, safety_auditor, knowledge_base):
        self.sandbox = sandbox
        self.host = host_executor
        self.auditor = safety_auditor
        self.kb = knowledge_base

    def execute(self, tool_name, params):
        # 本地工具
        if tool_name == "run_python":
            code = params.get("code", "")
            if self.auditor:
                try:
                    result = self.auditor.audit(code, "工具调用")
                    if isinstance(result, tuple): ok, reason = result
                    else: ok, reason = False, "格式错误"
                    if isinstance(ok, str): ok = ok.strip('"').strip("'").lower() in ("true","approved","yes")
                    if not ok: return f"安全审计拒绝: {reason}"
                except Exception as e: return f"审计异常: {e}"
            if self.sandbox:
                res = self.sandbox.run(code, timeout=5)
                return res["output"].strip() if res["success"] else f"沙箱错误: {res.get('error')}"
            return "沙箱未就绪"

        elif tool_name == "write_file":
            if self.host: self.host.write_file(params.get("filename",""), params.get("content","")); return "文件写入成功"
            return "文件执行器未就绪"

        elif tool_name == "run_system_command":
            if self.host: self.host.run_allowed_command(params.get("cmd","")); return "命令已执行"
            return "命令执行器未就绪"

        elif tool_name == "open_website":
            if self.host: self.host.open_website(params.get("url","")); return "正在打开网页"
            return "浏览器未就绪"

        elif tool_name == "search_knowledge_base":
            if self.kb:
                docs = self.kb.search(params.get("query",""), top_k=3)
                return "\n\n".join(docs) if docs else "未找到相关知识"
            return "知识库未就绪"

        # MCP 工具 (格式: server.tool)
        if '.' in tool_name:
            server, tool = tool_name.split('.', 1)
            try:
                async def run(): return await get_mcp_client().call_tool(server, tool, params)
                return asyncio.run(run())
            except Exception as e: return f"MCP 工具调用失败: {e}"

        return f"未知工具: {tool_name}"

def parse_tool_call(text):
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    json_str = match.group(1) if match else text
    try: return json.loads(json_str)
    except: return None
