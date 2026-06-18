# main.py —— LightAgent 终极版（含 Agent/Harness/Skill/MCP/RAG）
import sys, os, importlib, traceback, datetime, threading, asyncio
from pathlib import Path
from intelligence.tool_executor import TOOLS_DEF, parse_tool_call
from intelligence.inference_engine import InferenceEngine
from intelligence.memory_store import HierarchicalMemory
from intelligence.vector_db import LightVectorDB
from intelligence.tool_registry import ToolRegistry
from intelligence.agent_loop import AgentLoop
from intelligence.skill_manager import SkillManager
from intelligence.self_healing import SelfHealing

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
# 修复 QtWebEngine 初始化顺序（必须在 QApplication 创建前导入和设置属性）
try:
    from PyQt5 import QtWebEngineWidgets
except ImportError:
    pass
from PyQt5.QtCore import Qt
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
app = QApplication(sys.argv)

ERROR_LOG = PROJECT_ROOT / "error_report.log"

def log_error(msg):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] {msg}\n")
    print(f"❌ 错误已记录：{ERROR_LOG}")

def safe_import_class(module, class_name, desc):
    try:
        mod = importlib.import_module(module)
        cls = getattr(mod, class_name)
        print(f"✅ {desc}")
        return cls
    except Exception as e:
        print(f"❌ {desc} 导入失败: {e}")
        log_error(f"{desc} 导入失败: {e}")
        return None

print("🔹 导入基础模块...")
SetupEnv = safe_import_class("utils.config", "setup_environment", "配置管理")
LogManager = safe_import_class("utils.logger", "LogManager", "日志系统")
CacheManager = safe_import_class("utils.cache", "CacheManager", "缓存管理")
Sandbox = safe_import_class("core.sandbox", "Sandbox", "安全沙箱")
HostExecutor = safe_import_class("core.host_executor", "HostExecutor", "主机执行器")
SafetyAuditor = safe_import_class("core.safety_auditor", "SafetyAuditor", "安全审计")
MainWindow = safe_import_class("ui.main_window", "MainWindow", "主窗口")

if not all([SetupEnv, LogManager, MainWindow]):
    sys.exit(1)

config = SetupEnv()
logger = LogManager()
logger.info("LightAgent 启动")

class LightAgent:
    def __init__(self):
        self.config = config
        self.logger = logger
        self.cache = None
        self.sandbox = None
        self.api = None
        self.safety_auditor = None
        self.memory = None
        self.knowledge_base = None
        self.learning_center = None
        self.evolution_controller = None
        self.host_executor = None
        self.tool_executor = None
        self.experience = None
        self.confirm_callback = None
        self.plugin_manager = None
        self.task_planner = None
        self.perception = None
        self.ab_manager = None
        self.fed_client = None

        self._safe_init("缓存与沙箱", self._init_cache_sandbox)
        self._safe_init("API", self._init_api)
        self._safe_init("安全审计", self._init_safety_auditor)
        self._safe_init("记忆系统", self._init_memory)
        self._safe_init("知识库", self._init_knowledge_base)
        self._safe_init("学习中心", self._init_learning_center)
        self._safe_init("进化控制器", self._init_evolution)
        self._safe_init("主机执行器", self._init_host_executor)
        self._safe_init("工具执行器", self._init_tool_executor)
        self._safe_init("经验管理器", self._init_experience)
        self._safe_init("插件系统", self._init_plugins)
        self._safe_init("任务规划器", self._init_task_planner)
        self._safe_init("多模态感知", self._init_perception)
        self._safe_init("A/B测试管理", self._init_ab_manager)
        self._safe_init("联邦学习客户端", self._init_fed_client)

        # 高级 Agent 集成（延迟导入确保模块已存在）
        from intelligence.core_agent_skills_harness import integrate_agent_skills_harness
        integrate_agent_skills_harness(self)

        self.logger.set_status_callback(self.update_status)
        print("🎉 所有初始化尝试完毕（部分可能未成功）")

    def _safe_init(self, name, func):
        print(f"🔸 初始化 {name}...")
        try:
            func()
            print(f"✅ {name} 完成")
        except Exception as e:
            print(f"❌ {name} 失败: {e}")
            log_error(f"{name} 初始化失败: {e}")

    def _init_cache_sandbox(self):
        from utils.cache import CacheManager
        from core.sandbox import Sandbox
        self.cache = CacheManager()
        self.sandbox = Sandbox(memory_limit=256)

    def _init_api(self):
        use_local = self.config.get("use_local_llm", False)
        if use_local:
            from intelligence.local_adapter import LocalAPI
            self.api = LocalAPI(logger=self.logger)
            print("   🌸 本地大脑（张瑶瑶）")
        else:
            api_key = self.config.get("api_key", "")
            if api_key:
                from intelligence.deepseek_api import DeepSeekAPI
                self.api = DeepSeekAPI(api_key=api_key)
                print("   ☁️ 云端 DeepSeek API")
            else:
                print("   ⚠️ 未配置 API Key")
                self.api = None

    def _init_safety_auditor(self):
        from core.safety_auditor import SafetyAuditor
        if self.api:
            self.safety_auditor = SafetyAuditor(self.api)

    def _init_memory(self):
        from intelligence.memory import MemoryManager
        if self.api:
            self.memory = MemoryManager(api=self.api)

    def _init_knowledge_base(self):
        from knowledge.knowledge_base import KnowledgeBase
        self.knowledge_base = KnowledgeBase(root_dir=PROJECT_ROOT / "Knowledge")

    def _init_learning_center(self):
        from knowledge.learning_center import LearningCenter
        if self.api and self.knowledge_base:
            self.learning_center = LearningCenter(api=self.api, knowledge_base=self.knowledge_base, memory=self.memory)

    def _init_evolution(self):
        from intelligence.evolution import EvolutionController
        self.evolution_controller = EvolutionController(agent=self)

    def _init_host_executor(self):
        from core.host_executor import HostExecutor
        self.host_executor = HostExecutor(allowed_dir=self.config.get("knowledge_raw_dir", "E:/LightAgent/Knowledge/raw"),
                                          logger=self.logger)

    def _init_tool_executor(self):
        from intelligence.tool_executor import ToolExecutor
        self.tool_executor = ToolExecutor(self.sandbox, self.host_executor, self.safety_auditor, self.knowledge_base)

    def _init_experience(self):
        from intelligence.experience_manager import ExperienceManager
        self.experience = ExperienceManager()

    def _init_plugins(self):
        from intelligence.plugin_system import PluginManager
        self.plugin_manager = PluginManager()

    def _init_task_planner(self):
        from intelligence.task_planner import TaskPlanner
        self.task_planner = TaskPlanner(self)

    def _init_perception(self):
        from intelligence.multimodal_perception import MultimodalPerception
        self.perception = MultimodalPerception()

    def _init_ab_manager(self):
        from intelligence.ab_experiment import ABTestManager
        self.ab_manager = ABTestManager()

    def _init_fed_client(self):
        from intelligence.federated_learning import FederatedClient
        self.fed_client = FederatedClient(self)

    def update_status(self, msg):
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.statusBar().showMessage(msg, 3000)

    def process_user_input(self, text, temperature=0.7):
        if not self.api:
            return "⚠️ AI 服务未连接"
        if text.startswith("/run"):
            return self._safe_execution_flow(text[4:].strip(), temperature)
        if text == "/index":
            threading.Thread(target=self._safe_index, daemon=True).start()
            return "🔍 知识库索引已启动"
        if text.startswith("/auto"):
            if hasattr(self, 'autonomous_agent'):
                task_id = self.autonomous_agent.submit_task(text[5:].strip())
                return f"🚀 自主任务已提交 (ID: {task_id})"
            return "Agent 未就绪"

        tools_desc = "\n".join([f"- {t['name']}: {t['desc']}" for t in TOOLS_DEF])
        system_prompt = f"你是 LightAgent AI 电脑管家。可用工具：\n{tools_desc}"

        messages = [{"role": "system", "content": system_prompt}]

        if self.memory:
            try:
                for mem in self.memory.retrieve_relevant(text, top_k=3):
                    messages.insert(0, {"role": "system", "content": f"相关记忆：{mem['content']}"})
            except: pass
        if self.knowledge_base:
            try:
                kb_results = self.knowledge_base.search(text, top_k=2)
                if kb_results:
                    messages.insert(0, {"role": "system", "content": f"【知识库】\n" + "\n".join(kb_results)})
            except: pass

        messages.append({"role": "user", "content": f"{text}\n请决定是否使用工具。需要工具返回JSON：{{\"tool\":\"工具名\",\"params\":{{...}}}}；否则直接回答。"})

        try:
            resp = self.api.chat(messages, temperature=temperature)
            tool_data = parse_tool_call(resp)
            if tool_data and 'tool' in tool_data:
                result = self.tool_executor.execute(tool_data['tool'], tool_data.get('params', {}))
                messages.append({"role": "assistant", "content": resp})
                messages.append({"role": "user", "content": f"工具执行结果：{result}"})
                return self.api.chat(messages, temperature=temperature)
            return resp
        except Exception as e:
            return f"❌ AI 请求失败：{e}"

    def _safe_execution_flow(self, task, temperature=0.7):
        return f"任务 '{task}' 已接收，但安全执行流程待完善"

    def _safe_index(self):
        try:
            if self.knowledge_base:
                self.knowledge_base.index_files()
                print("✅ 索引完成")
        except Exception as e:
            print(f"❌ 索引失败: {e}")

    def run(self):
        print("🖥️ 正在创建主窗口...")
        self.main_window = MainWindow(agent=self)
        self.main_window.show()
        print("✅ 主窗口已显示")
        return app.exec_()

if __name__ == "__main__":
    try:
        agent = LightAgent()
        exit_code = agent.run()
        sys.exit(exit_code)
    except Exception as e:
        err = f"💥 启动失败: {e}\n{traceback.format_exc()}"
        print(err)
        log_error(err)
        if QApplication.instance():
            QMessageBox.critical(None, "启动失败", f"启动失败:\n{e}")
        sys.exit(1)
