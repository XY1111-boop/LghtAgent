# ui/main_window.py —— 完整版（含滚动支持、设置菜单、所有标签页）
# type: ignore
from ui.dev_tree_tab import DevTreeTab
from ui.training_center import TrainingCenterTab
from ui.analysis_tab import AnalysisReportTab
from ui.dev_tree_tab import DevTreeTab
from ui.test_runner_tab import TestRunnerTab
import importlib, traceback
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QAction, QMessageBox,
                             QLabel, QScrollArea)
from PyQt5.QtCore import Qt

TAB_CONFIG = [
    ("AI 控制台", "ui.ai_console", "AIConsoleTab"),
    ("本地浏览器", "ui.browser_tab", "BrowserTab"),
    ("工作流", "ui.workflow_tab", "WorkflowTab"),
    ("进化看板", "ui.evolution_tab", "EvolutionTab"),
    ("学习中心", "ui.learning_tab", "LearningTab"),
    ("📡 实时监控", "ui.monitor_tab", "MonitorTab"),
    ("🧠 记忆库", "ui.memory_viewer_tab", "MemoryViewerTab"),
    ("💬 聊天室", "ui.chat_room_tab", "ChatRoomTab"),
    ("🧠 本地大脑监控", "ui.local_ai_monitor", "LocalAIMonitorTab"),
    ("🎓 训练中心", "ui.training_center", "TrainingCenterTab"),
    ("📊 分析报告", "ui.analysis_tab", "AnalysisReportTab"),
    ("🧪 测试", "ui.test_runner_tab", "TestRunnerTab"),
    
    
    
    
    
    ("🌳 项目树", "ui.dev_tree_tab", "DevTreeTab"),
]

class MainWindow(QMainWindow):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.setWindowTitle("LightAgent - AI 电脑管家")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: #FFFFFF; color: #333333;")

        # 菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)

        self.tabs = QTabWidget()
        loaded = 0
        for title, module, cls_name in TAB_CONFIG:
            if self._try_load(title, module, cls_name):
                loaded += 1

        if loaded == 0:
            fail_label = QLabel("所有标签页加载失败，但主窗口仍可显示。\n请查看控制台输出。")
            fail_label.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(fail_label, "提示")

        self.setCentralWidget(self.tabs)
        self.statusBar().showMessage(f"成功加载 {loaded}/{len(TAB_CONFIG)} 个标签页")

    def _try_load(self, title, module_name, class_name):
        """安全加载单个标签页，并包裹在 QScrollArea 中"""
        print(f"正在加载 {title} ...", end=" ")
        try:
            mod = importlib.import_module(module_name)
            cls = getattr(mod, class_name)
            widget = cls(self.agent)
            scroll = self._wrap_scroll(widget)
            self.tabs.addTab(scroll, title)
            print("✅")
            return True
        except Exception as e:
            print(f"❌ 失败: {e}")
            traceback.print_exc()
            placeholder = QLabel(f"<h3>{title} 加载失败</h3><p>{e}</p>")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, f"{title} (错误)")
            return False

    def _wrap_scroll(self, widget):
        """将控件包裹在 QScrollArea 中，使其可滚动"""
        if isinstance(widget, QScrollArea):
            return widget
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(widget)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        return scroll


    def show_permission_dialog(self, title, code, risk):
        from PyQt5.QtWidgets import QMessageBox, QCheckBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(f"AI 请求执行以下操作 (风险: {risk})：\n\n{code[:200]}")
        msg.setInformativeText("请确认是否允许执行。")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        cb_10min = QCheckBox("10 分钟内不再提示")
        cb_always = QCheckBox("永久信任此应用")
        layout = msg.layout()
        layout.addWidget(cb_10min, layout.rowCount(), 0, 1, 2)
        layout.addWidget(cb_always, layout.rowCount(), 0, 1, 2)
        reply = msg.exec_()
        if reply == QMessageBox.Yes:
            if cb_always.isChecked():
                return "always"
            elif cb_10min.isChecked():
                return "temp"
            return "once"
        return "deny"

    def open_settings(self):
        """打开设置对话框"""
        try:
            from ui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.agent.config, self)
            if dialog.exec_():
                self.agent.api.api_key = self.agent.config.get("api_key", "")
                self.statusBar().showMessage("设置已保存")
        except Exception as e:
            QMessageBox.warning(self, "设置错误", str(e))
