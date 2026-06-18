# add_ui_tabs.py —— 为五大新模块创建UI标签页并集成到主窗口
import os, shutil

PROJECT = r"E:\LightAgent"
UI_DIR = os.path.join(PROJECT, "ui")

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已创建 {path}")

# ─── 1. 多模态IO 界面 ───
safe_write("ui/multimodal_tab.py", r'''# ui/multimodal_tab.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from intelligence.multimodal_io import MultimodalIO

class Worker(QThread):
    result = pyqtSignal(str)
    def __init__(self, func):
        super().__init__()
        self.func = func
    def run(self):
        try:
            res = self.func()
            self.result.emit(res)
        except Exception as e:
            self.result.emit(f"错误: {e}")

class MultimodalTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.io = agent.multimodal if hasattr(agent, 'multimodal') else MultimodalIO(agent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🎤 语音识别"))
        self.voice_btn = QPushButton("开始聆听")
        self.voice_btn.clicked.connect(self.start_listen)
        layout.addWidget(self.voice_btn)

        layout.addWidget(QLabel("📷 图像分析"))
        self.img_path_label = QLabel("未选择图片")
        layout.addWidget(self.img_path_label)
        img_btn = QPushButton("选择图片并分析")
        img_btn.clicked.connect(self.analyze_image)
        layout.addWidget(img_btn)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.setLayout(layout)

    def start_listen(self):
        self.voice_btn.setEnabled(False)
        self.result_area.append("🎤 正在聆听...")
        self.worker = Worker(self.io.listen_and_process)
        self.worker.result.connect(self.on_voice_result)
        self.worker.start()

    def on_voice_result(self, text):
        self.voice_btn.setEnabled(True)
        self.result_area.append(f"识别结果: {text}")
        if text and "无法识别" not in text:
            reply = self.agent.process_user_input(text)
            self.result_area.append(f"AI: {reply}")
            # TTS 朗读回复
            if hasattr(self.io, 'speak_text'):
                self.io.speak_text(reply)

    def analyze_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.img_path_label.setText(path)
            result = self.io.analyze_image(path)
            self.result_area.append(f"图像分析: {result}")
''')

# ─── 2. 任务调度器 界面 ───
safe_write("ui/scheduler_tab.py", r'''# ui/scheduler_tab.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget,
                             QInputDialog, QMessageBox, QLabel)
from PyQt5.QtCore import QTimer
from intelligence.task_scheduler import TaskScheduler

class SchedulerTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.scheduler = agent.task_scheduler if hasattr(agent, 'task_scheduler') else TaskScheduler()
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_list)
        self.timer.start(2000)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("📋 任务管理器"))

        self.task_list = QListWidget()
        layout.addWidget(self.task_list)

        add_btn = QPushButton("添加简单任务")
        add_btn.clicked.connect(self.add_task)
        layout.addWidget(add_btn)

        cancel_btn = QPushButton("取消选中任务")
        cancel_btn.clicked.connect(self.cancel_task)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)
        self.scheduler.start()

    def add_task(self):
        name, ok = QInputDialog.getText(self, "任务名称", "请输入任务描述:")
        if ok and name:
            self.scheduler.add_task(name, lambda: self.agent.process_user_input(name))
            self.refresh_list()

    def cancel_task(self):
        item = self.task_list.currentItem()
        if item:
            task_id = item.text().split()[0]
            self.scheduler.cancel_task(task_id)
            self.refresh_list()

    def refresh_list(self):
        self.task_list.clear()
        for tid, task in self.scheduler.tasks.items():
            self.task_list.addItem(f"{tid} [{task.status.value}] {task.name}")
''')

# ─── 3. API网关 界面 ───
safe_write("ui/api_gateway_tab.py", r'''# ui/api_gateway_tab.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QComboBox, QLineEdit)
from intelligence.api_gateway import APIGateway

class APIGatewayTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.gateway = APIGateway()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🌐 外部API调用"))

        self.service_combo = QComboBox()
        self.service_combo.addItems(list(self.gateway.services.keys()))
        layout.addWidget(self.service_combo)

        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("参数（如城市名）")
        layout.addWidget(self.param_input)

        call_btn = QPushButton("调用服务")
        call_btn.clicked.connect(self.call_service)
        layout.addWidget(call_btn)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        layout.addWidget(self.result_area)

        self.setLayout(layout)

    def call_service(self):
        service = self.service_combo.currentText()
        param = self.param_input.text()
        if param:
            result = self.gateway.call(service, param)
        else:
            result = self.gateway.call(service)
        self.result_area.append(f"[{service}] {result}")
''')

# ─── 4. 用户管理 界面 ───
safe_write("ui/user_manager_tab.py", r'''# ui/user_manager_tab.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QLineEdit, QHBoxLayout, QMessageBox)
from intelligence.user_manager import UserManager

class UserManagerTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.um = UserManager()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("👥 用户管理"))

        # 注册
        reg_layout = QHBoxLayout()
        self.reg_user = QLineEdit()
        self.reg_user.setPlaceholderText("用户名")
        self.reg_pass = QLineEdit()
        self.reg_pass.setPlaceholderText("密码")
        self.reg_pass.setEchoMode(QLineEdit.Password)
        reg_btn = QPushButton("注册")
        reg_btn.clicked.connect(self.register)
        reg_layout.addWidget(self.reg_user)
        reg_layout.addWidget(self.reg_pass)
        reg_layout.addWidget(reg_btn)
        layout.addLayout(reg_layout)

        # 登录
        login_layout = QHBoxLayout()
        self.login_user = QLineEdit()
        self.login_user.setPlaceholderText("用户名")
        self.login_pass = QLineEdit()
        self.login_pass.setPlaceholderText("密码")
        self.login_pass.setEchoMode(QLineEdit.Password)
        login_btn = QPushButton("登录")
        login_btn.clicked.connect(self.login)
        login_layout.addWidget(self.login_user)
        login_layout.addWidget(self.login_pass)
        login_layout.addWidget(login_btn)
        layout.addLayout(login_layout)

        self.status_label = QLabel("当前用户: 未登录")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def register(self):
        ok, msg = self.um.register(self.reg_user.text(), self.reg_pass.text())
        QMessageBox.information(self, "注册结果", msg)

    def login(self):
        ok, msg = self.um.login(self.login_user.text(), self.login_pass.text())
        if ok:
            self.status_label.setText(f"当前用户: {self.um.current_user} (角色: {self.um.get_current_role()})")
        QMessageBox.information(self, "登录结果", msg)
''')

# ─── 5. 测试面板（简单版） ───
safe_write("ui/test_runner_tab.py", r'''# ui/test_runner_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel
import subprocess, sys

class TestRunnerTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("🧪 自动化测试"))

        run_btn = QPushButton("运行沙箱测试")
        run_btn.clicked.connect(self.run_tests)
        layout.addWidget(run_btn)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.setLayout(layout)

    def run_tests(self):
        try:
            result = subprocess.run([sys.executable, "-m", "unittest", "tests.test_sandbox"],
                                    capture_output=True, text=True, timeout=30)
            self.output_area.append(result.stdout)
            self.output_area.append(result.stderr)
        except Exception as e:
            self.output_area.append(f"测试运行异常: {e}")
''')

# ─── 6. 修改 main_window.py 添加所有新标签页 ───
mainwin_path = os.path.join(PROJECT, "ui", "main_window.py")
if os.path.exists(mainwin_path):
    with open(mainwin_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 添加导入语句
    imports_to_add = [
        "from ui.multimodal_tab import MultimodalTab",
        "from ui.scheduler_tab import SchedulerTab",
        "from ui.api_gateway_tab import APIGatewayTab",
        "from ui.user_manager_tab import UserManagerTab",
        "from ui.test_runner_tab import TestRunnerTab",
    ]
    for imp in imports_to_add:
        if imp not in content:
            content = content.replace(
                "from ui.analysis_tab import AnalysisReportTab",
                f"from ui.analysis_tab import AnalysisReportTab\n{imp}"
            )

    # 在 TAB_CONFIG 列表中添加标签页
    tabs_to_add = [
        '    ("🎤 多模态", "ui.multimodal_tab", "MultimodalTab"),',
        '    ("📋 任务", "ui.scheduler_tab", "SchedulerTab"),',
        '    ("🌐 API网关", "ui.api_gateway_tab", "APIGatewayTab"),',
        '    ("👥 用户", "ui.user_manager_tab", "UserManagerTab"),',
        '    ("🧪 测试", "ui.test_runner_tab", "TestRunnerTab"),',
    ]
    tab_config_end = content.find("TAB_CONFIG = [")
    tab_config_end = content.find("]", tab_config_end)
    for tab in tabs_to_add:
        if tab not in content:
            content = content[:tab_config_end] + tab + "\n" + content[tab_config_end:]

    with open(mainwin_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main_window.py 已添加五大新标签页")

print("\n🎉 UI标签页集成完成！重启 LightAgent 后，您将看到：")
print("   - 🎤 多模态（语音、图像）")
print("   - 📋 任务（调度管理）")
print("   - 🌐 API网关（天气等）")
print("   - 👥 用户（注册/登录）")
print("   - 🧪 测试（运行单元测试）")
print("   启动命令：python main.py")
