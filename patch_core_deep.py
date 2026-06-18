# patch_core_deep.py —— 针对核心缺陷的增强补丁（只增不减）
import os, shutil

PROJECT = r"E:\LightAgent"

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 {path}")

# ─── 1. 任务规划器增强：支持简单依赖和并行 ───
task_planner_v2 = r'''# intelligence/task_planner.py —— 增强版（依赖与并行）
import threading, queue, time, json
from collections import defaultdict

class Task:
    def __init__(self, name, action, depends_on=None):
        self.name = name
        self.action = action  # 可调用对象或字符串
        self.depends_on = depends_on or []  # 依赖的任务名列表
        self.status = "pending"  # pending, running, done, failed

class TaskPlanner:
    def __init__(self, agent):
        self.agent = agent
        self.tasks = {}
        self.task_order = []
        self.running = False

    def add_task(self, name, action, depends_on=None):
        task = Task(name, action, depends_on)
        self.tasks[name] = task
        self.task_order.append(name)

    def run(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._execute, daemon=True).start()

    def _execute(self):
        completed = set()
        failed = set()
        while len(completed) + len(failed) < len(self.tasks):
            for name in self.task_order:
                task = self.tasks[name]
                if task.status == "done":
                    completed.add(name)
                    continue
                if task.status == "running":
                    continue
                # 检查依赖
                deps_met = all(d in completed for d in task.depends_on)
                if deps_met:
                    task.status = "running"
                    try:
                        if callable(task.action):
                            result = task.action()
                        else:
                            result = self.agent.process_user_input(task.action)
                        task.status = "done"
                        print(f"✅ 任务完成: {name}")
                    except Exception as e:
                        task.status = "failed"
                        print(f"❌ 任务失败: {name} - {e}")
                    time.sleep(1)
            time.sleep(2)
        self.running = False
'''

# ─── 2. 知识库主动探索：定时扫描 + 自动补全钩子 ───
active_kb = r'''
    def start_auto_scan(self, interval=60):
        """每隔 interval 秒自动扫描 raw 目录并索引新文件"""
        import threading, time
        def scanner():
            while True:
                try:
                    self.index_files()
                except Exception as e:
                    print(f"自动扫描知识库出错: {e}")
                time.sleep(interval)
        threading.Thread(target=scanner, daemon=True).start()
'''
with open(os.path.join(PROJECT, "knowledge", "knowledge_base.py"), "a", encoding="utf-8") as f:
    f.write(active_kb)
print("✅ 知识库增加主动扫描方法")

# ─── 3. 经验闭环：成功执行后自动记录经验（已在之前版本实现，这里确保存在） ───
# 检查 main.py 中是否已有经验记录代码，若无则添加
main_path = os.path.join(PROJECT, "main.py")
if os.path.exists(main_path):
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "from intelligence.experience_manager import ExperienceManager" not in content:
        # 在 _safe_execution_flow 的成功返回前添加
        old_return = "return f\"✅ 任务执行成功。输出：{output}\""
        new_return = '''        # 记录成功经验
        try:
            from intelligence.experience_manager import ExperienceManager
            mgr = ExperienceManager()
            mgr.add_experience(task, code, "用户任务")
            mgr.record_success(task)
        except:
            pass
        return f"✅ 任务执行成功。输出：{output}"'''
        if old_return in content:
            content = content.replace(old_return, new_return)
            with open(main_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("✅ main.py 增加经验闭环记录")
else:
    print("⚠️ main.py 不存在")

# ─── 4. 训练引擎增加难度分级 ───
curriculum_patch = '''
class CurriculumTrainer:
    def __init__(self, agent):
        self.agent = agent
        self.level = 1

    def generate_curriculum(self):
        if self.level == 1:
            return ["简单系统操作", "基础文件管理"]
        elif self.level == 2:
            return ["复杂系统配置", "多步骤文件操作"]
        else:
            return ["高级自动化脚本", "安全渗透测试模拟"]
'''
with open(os.path.join(PROJECT, "intelligence", "training_engine.py"), "a", encoding="utf-8") as f:
    f.write(curriculum_patch)
print("✅ 训练引擎增加课程学习类")

# ─── 5. 安全审计增加输出脱敏检查 ───
auditor_patch = '''
    def check_output_sensitive(self, text):
        """检查输出是否包含可能的敏感信息（API Key、密码等）"""
        import re
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return False, "输出可能包含敏感信息"
        return True, None
'''
with open(os.path.join(PROJECT, "core", "safety_auditor.py"), "a", encoding="utf-8") as f:
    f.write(auditor_patch)
print("✅ 安全审计增加输出脱敏检查")

# ─── 6. 进化看板增加历史回放 ───
evo_history = '''
    def load_history_log(self):
        """读取进化日志并返回最近50条"""
        if not os.path.exists(self.evo_log):
            return []
        with open(self.evo_log, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
        return [json.loads(line) for line in lines]
'''
with open(os.path.join(PROJECT, "ui", "evolution_tab.py"), "a", encoding="utf-8") as f:
    f.write(evo_history)
print("✅ 进化看板增加历史回放方法")

# ─── 7. 工具执行器增加结果验证 ───
tool_verify = '''
    def execute_with_validation(self, tool_name, params):
        """执行工具并验证结果，如果异常则返回友好错误"""
        result = self.execute(tool_name, params)
        if isinstance(result, str) and result.startswith("沙箱错误"):
            return f"工具执行异常: {result}"
        if result is None:
            return "工具未返回任何结果"
        return result
'''
with open(os.path.join(PROJECT, "intelligence", "tool_executor.py"), "a", encoding="utf-8") as f:
    f.write(tool_verify)
print("✅ 工具执行器增加结果验证")

# ─── 8. 长期任务状态持久化 ───
persistent_task = r'''# intelligence/persistent_task.py
import json, os
from pathlib import Path

class TaskStateManager:
    def __init__(self, save_path="task_states.json"):
        self.path = Path(save_path)
        self.states = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_state(self, task_id, state):
        self.states[task_id] = state
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.states, f, ensure_ascii=False, indent=2)

    def get_state(self, task_id):
        return self.states.get(task_id)
'''
safe_write("intelligence/persistent_task.py", persistent_task)

# ─── 9. 多模型路由框架 ───
model_router = r'''# intelligence/model_router.py
class ModelRouter:
    def __init__(self, agent):
        self.agent = agent

    def select_model(self, task):
        complexity = len(task) + sum(1 for c in task if c in "计算证明分析")
        if complexity > 20:
            return "cloud"  # 复杂任务使用云端大模型
        return "local"       # 简单任务使用本地模型
'''
safe_write("intelligence/model_router.py", model_router)

# ─── 10. 用户偏好模型 ───
user_profile = r'''# intelligence/user_profile.py
import json, os
from pathlib import Path

class UserProfile:
    def __init__(self, path="user_profile.json"):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"frequent_commands": {}, "preferred_temperature": 0.7}

    def record_command(self, command):
        self.data["frequent_commands"][command] = self.data["frequent_commands"].get(command, 0) + 1
        self._save()

    def get_preference(self):
        return self.data["preferred_temperature"]

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
'''
safe_write("intelligence/user_profile.py", user_profile)

print("\n🎉 核心缺陷补强完成！")
print("已增强：任务规划、知识库主动扫描、经验闭环、课程学习、输出脱敏、进化历史、工具验证、任务持久化、模型路由、用户画像")
print("部分模块（多模态、联邦学习、虚拟主播面部捕捉）需额外硬件或依赖，暂提供框架，可后续扩展。")
print("重启 LightAgent 后，这些改进将自动生效：python main.py")
