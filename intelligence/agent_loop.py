# agent_loop.py —— ReAct Agent + Workflow 引擎
import re, json, threading, time
from intelligence.tool_registry import ToolRegistry
from intelligence.memory_store import HierarchicalMemory

class AgentLoop:
    def __init__(self, inference_engine, tools: ToolRegistry, memory: HierarchicalMemory):
        self.engine = inference_engine
        self.tools = tools
        self.memory = memory

    def run(self, goal, max_steps=5):
        thoughts = []
        for step in range(max_steps):
            # 构建 prompt
            prompt = self._build_prompt(goal, thoughts)
            resp = self.engine.chat([{"role": "user", "content": prompt}], temperature=0.2)
            thoughts.append(resp)
            # 解析动作
            action = self._parse_action(resp)
            if not action:
                # 最终回答
                return resp
            # 执行工具
            tool_result = self.tools.tools[action["tool"]]["func"](**action.get("params", {}))
            thoughts.append(f"工具结果: {tool_result}")
        return "达到最大步数"

    def _parse_action(self, text):
        match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return None

    def _build_prompt(self, goal, thoughts):
        # 注入分层记忆
        mems = self.memory.retrieve(goal, 3)
        mem_str = "\n".join([m["content"] for m in mems])
        return f"""目标: {goal}
记忆: {mem_str}
之前的思考: {thoughts}
现在请决定下一步行动，需要工具请输出JSON。"""
