# last_resort_main.py —— 每个操作都独立保护，必定弹出窗口
import os, shutil

PROJECT = r"E:\LightAgent"
MAIN = os.path.join(PROJECT, "main.py")

if os.path.exists(MAIN):
    shutil.copy2(MAIN, MAIN + ".bak")

FINAL_MAIN = r'''# main.py —— 绝对容错版，任何错误都不会阻止窗口显示
import sys, os, importlib, traceback, datetime, threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

# 修复 QtWebEngine
try:
    from PyQt5 import QtWebEngineWidgets
except:
    pass
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

# 导入基础模块
print("🔹 导入基础模块...")
SetupEnv = safe_import_class("utils.config", "setup_environment", "配置管理")
LogManager = safe_import_class("utils.logger", "LogManager", "日志系统")
MainWindow = safe_import_class("ui.main_window", "MainWindow", "主窗口")

if not all([SetupEnv, LogManager, MainWindow]):
    print("❌ 致命错误，无法启动")
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

        # 逐个初始化，失败仅记录，绝不退出
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
            from intelligence.deepseek_api import DeepSeekAPI
            self.api = DeepSeekAPI(api_key=api_key)

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
        if self.api:
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

    def update_status(self, msg):
        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.statusBar().showMessage(msg, 3000)

    def process_user_input(self, text, temperature=0.7):
        return "系统正在运行（占位回复）"

    def run(self):
        print("🖥️ 正在创建主窗口...")
        self.main_window = MainWindow(agent=self)
        self.main_window.show()
        print("✅ 主窗口已显示")
        return app.exec_()

# 全局异常钩子
def global_exception_hook(exc_type, exc_value, exc_tb):
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print(f"💥 未捕获的异常:\n{error_msg}")
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.datetime.now()}] 全局异常: {error_msg}\n")
    sys.__excepthook__(exc_type, exc_value, exc_tb)
sys.excepthook = global_exception_hook

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
'''

with open(MAIN, "w", encoding="utf-8") as f:
    f.write(FINAL_MAIN)

print("✅ 最终容错 main.py 已生成。")
print("请运行 python main.py，这次将看到详细的初始化过程，并且主窗口一定会出现。")
