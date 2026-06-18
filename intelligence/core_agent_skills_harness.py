# intelligence/core_agent_skills_harness.py —— Skill + Harness + Autonomous Agent
import threading, queue, time, json, yaml, os, re, sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 技能系统
@dataclass
class SkillStep:
    description: str
    action: str
    params: Dict = field(default_factory=dict)
    check: str = ""
    max_retries: int = 1
    timeout: int = 30

@dataclass
class Skill:
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    steps: List[SkillStep] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    safety_level: str = "low"
    created_at: str = ""
    success_count: int = 0
    fail_count: int = 0

class SkillManager:
    def __init__(self, skills_dir: Path = PROJECT_ROOT / "skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        skills_dir.mkdir(exist_ok=True)
        self._load_default_skills()

    def _load_default_skills(self):
        if "桌面整理" not in self.skills:
            skill = Skill(
                name="桌面整理",
                description="自动整理桌面文件到分类文件夹",
                triggers=["整理桌面", "清理桌面", "桌面太乱"],
                steps=[
                    SkillStep(description="扫描桌面文件", action="run_python",
                              params={"code": "import os,shutil,json;from pathlib import Path;desktop=Path.home()/'Desktop';files=[f.suffix for f in desktop.iterdir() if f.is_file()];print(json.dumps({s:files.count(s) for s in set(files)}))"}),
                    SkillStep(description="按类型移动文件到子文件夹", action="run_python",
                              params={"code": "import os,shutil;from pathlib import Path;desktop=Path.home()/'Desktop';types={'.txt':'文档','.docx':'文档','.pdf':'文档','.jpg':'图片','.png':'图片','.zip':'压缩包'};[shutil.move(str(f), str((desktop/types.get(f.suffix.lower(),'其他'))/f.name)) for f in desktop.iterdir() if f.is_file()] if not (desktop/types.get(f.suffix.lower(),'其他')).exists() else None;print('桌面整理完成')"})
                ],
                safety_level="low"
            )
            self.skills["桌面整理"] = skill

    def find_skill(self, user_input: str) -> Optional[Skill]:
        best_match = None
        max_score = 0
        for skill in self.skills.values():
            score = sum(1 for trigger in skill.triggers if trigger in user_input)
            if score > max_score:
                max_score = score
                best_match = skill
        return best_match if max_score > 0 else None

    def add_skill(self, skill: Skill):
        self.skills[skill.name] = skill

# 安全马具
class SafetyBoundary(Enum):
    ALLOWED_DIRS = ["桌面", "文档", "下载", "E:/LightAgent/Knowledge/raw"]
    FORBIDDEN_DIRS = ["C:/Windows", "C:/Program Files", "/etc", "/sys"]
    ALLOWED_COMMANDS = ["dir", "echo", "calc", "notepad", "explorer", "tasklist", "ipconfig"]
    FORBIDDEN_COMMANDS = ["del", "format", "rm", "shutdown", "taskkill"]

class Harness:
    def __init__(self, auditor, sandbox, host):
        self.auditor = auditor
        self.sandbox = sandbox
        self.host = host
        self.execution_log = []

    def pre_check(self, task: str, code: str) -> tuple[bool, str]:
        for forbidden in SafetyBoundary.FORBIDDEN_DIRS.value:
            if forbidden.lower() in code.lower():
                return False, f"代码试图访问禁止目录: {forbidden}"
        for forbidden_cmd in SafetyBoundary.FORBIDDEN_COMMANDS.value:
            if re.search(rf'\b{forbidden_cmd}\b', code, re.IGNORECASE):
                return False, f"代码包含禁止命令: {forbidden_cmd}"
        if self.auditor:
            ok, reason = self.auditor.audit(code, task)
            if not ok:
                return False, f"安全审计不通过: {reason}"
        return True, "通过"

    def verify_result(self, expected: str, actual: str) -> bool:
        if not expected:
            return True
        return any(word in actual for word in expected.split())

    def auto_fix(self, task: str, code: str, error: str) -> Optional[str]:
        print(f"🔧 尝试修复错误: {error}")
        return None

# 自主 Agent
class TaskStatus(Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    REPAIRING = "repairing"

@dataclass
class AgentTask:
    id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    plan: List[str] = field(default_factory=list)
    current_step: int = 0
    result: str = ""
    errors: List[str] = field(default_factory=list)

class AutonomousAgent:
    def __init__(self, api, tool_executor, skill_manager: SkillManager, harness: Harness):
        self.api = api
        self.tool_executor = tool_executor
        self.skill_manager = skill_manager
        self.harness = harness
        self.task_queue = queue.Queue()
        self.running = False
        self.current_task: Optional[AgentTask] = None

    def start(self):
        self.running = True
        threading.Thread(target=self._main_loop, daemon=True).start()

    def submit_task(self, goal: str) -> str:
        task = AgentTask(id=str(time.time())[-8:], goal=goal)
        self.task_queue.put(task)
        return task.id

    def _main_loop(self):
        while self.running:
            try:
                task = self.task_queue.get(timeout=5)
            except queue.Empty:
                continue
            self._execute_task(task)

    def _execute_task(self, task: AgentTask):
        self.current_task = task
        task.status = TaskStatus.PLANNING
        skill = self.skill_manager.find_skill(task.goal)
        if skill:
            print(f"✅ 匹配到技能: {skill.name}")
            self._run_skill(task, skill)
            return
        plan = self._generate_plan(task.goal)
        if not plan:
            task.status = TaskStatus.FAILED
            task.errors.append("无法生成执行计划")
            return
        task.plan = plan
        for i, step in enumerate(plan):
            task.current_step = i
            task.status = TaskStatus.EXECUTING
            tool_data = parse_tool_call(step)
            if tool_data and 'tool' in tool_data:
                ok, reason = self.harness.pre_check(step, str(tool_data.get('params', {})))
                if not ok:
                    task.errors.append(f"步骤{i} 预检失败: {reason}")
                    repaired = self._repair_step(task, step, reason)
                    if repaired:
                        step = repaired
                    else:
                        continue
                try:
                    result = self.tool_executor.execute(tool_data['tool'], tool_data.get('params', {}))
                    task.status = TaskStatus.VERIFYING
                    if "错误" in result or "失败" in result:
                        task.errors.append(f"步骤{i} 执行异常: {result}")
                        repaired = self._repair_step(task, step, result)
                        if repaired:
                            step = repaired
                        else:
                            continue
                    task.result = result
                except Exception as e:
                    task.errors.append(f"步骤{i} 异常: {e}")
            else:
                try:
                    response = self.api.chat([{"role": "user", "content": step}])
                    task.result = response
                except Exception as e:
                    task.errors.append(f"步骤{i} LLM 调用失败: {e}")
        task.status = TaskStatus.COMPLETED if not task.errors else TaskStatus.FAILED

    def _run_skill(self, task: AgentTask, skill: Skill):
        for i, step in enumerate(skill.steps):
            task.current_step = i
            task.status = TaskStatus.EXECUTING
            if step.action.startswith("run_python"):
                code = step.params.get("code", "")
                ok, reason = self.harness.pre_check(task.goal, code)
                if not ok:
                    task.errors.append(f"技能步骤{i} 预检失败: {reason}")
                    continue
                try:
                    result = self.tool_executor.execute("run_python", {"code": code})
                    task.result = result
                except Exception as e:
                    task.errors.append(f"技能步骤{i} 异常: {e}")
        task.status = TaskStatus.COMPLETED if not task.errors else TaskStatus.FAILED

    def _generate_plan(self, goal: str) -> Optional[List[str]]:
        prompt = f"将以下目标拆解为具体的执行步骤，每步一行，步骤应包含可直接执行的工具调用（JSON格式）或自然语言描述。\n目标：{goal}\n可用工具：run_python, write_file, run_system_command, open_website, search_knowledge_base\n只返回步骤列表。"
        try:
            resp = self.api.chat([{"role": "user", "content": prompt}])
            return [line.strip() for line in resp.split("\n") if line.strip()]
        except:
            return None

    def _repair_step(self, task: AgentTask, code: str, error: str) -> Optional[str]:
        task.status = TaskStatus.REPAIRING
        fixed = self.harness.auto_fix(task.goal, code, error)
        if fixed:
            return fixed
        if "'\"approved\"'" in error:
            return code.replace("approved", "True")
        return None

def parse_tool_call(text):
    import re, json
    match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    json_str = match.group(1) if match else text
    try:
        return json.loads(json_str)
    except:
        return None

def integrate_agent_skills_harness(agent):
    if not hasattr(agent, 'skill_manager'):
        agent.skill_manager = SkillManager()
        print("✅ Skill 系统就绪")
    if not hasattr(agent, 'harness'):
        agent.harness = Harness(agent.safety_auditor, agent.sandbox, agent.host_executor)
        print("✅ Harness 安全框架就绪")
    if not hasattr(agent, 'autonomous_agent'):
        agent.autonomous_agent = AutonomousAgent(agent.api, agent.tool_executor, agent.skill_manager, agent.harness)
        agent.autonomous_agent.start()
        print("✅ 自主 Agent 循环已启动")
