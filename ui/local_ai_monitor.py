# ui/local_ai_monitor.py —— 线程安全版
import time, os
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

class LocalAIMonitorTab(QWidget):
    log_signal = pyqtSignal(str)

    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.start_time = time.time()
        self.call_count = 0
        self.total_time = 0.0
        self.init_ui()
        self.log_signal.connect(self._append_log)
        if hasattr(agent.logger, 'status_signal'):
            agent.logger.status_signal.connect(self.add_log)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_stats)
        self.timer.start(3000)

    def init_ui(self):
        layout = QVBoxLayout()
        self.status_label = QLabel("🔍 检测中...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4EC9B0;")
        layout.addWidget(self.status_label)
        self.model_label = QLabel("模型: --")
        self.calls_label = QLabel("调用次数: 0")
        self.avg_time_label = QLabel("平均耗时: 0ms")
        layout.addWidget(self.model_label)
        layout.addWidget(self.calls_label)
        layout.addWidget(self.avg_time_label)
        layout.addWidget(QLabel("工作日志："))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        self.log_view.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4;")
        layout.addWidget(self.log_view)
        self.setLayout(layout)

    def add_log(self, message):
        """线程安全地添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colored = f"<span style='color:#888;'>[{timestamp}]</span> {message}"
        self.log_signal.emit(colored)

    def _append_log(self, html):
        """在主线程中安全地更新UI"""
        self.log_view.append(html)
        c = self.log_view.textCursor()
        c.movePosition(QTextCursor.End)
        self.log_view.setTextCursor(c)

    def refresh_stats(self):
        use_local = self.agent.config.get("use_local_llm", False)
        if use_local:
            model_name = "未知"
            try:
                if hasattr(self.agent.api, 'model_name'):
                    model_name = self.agent.api.model_name
                elif hasattr(self.agent.api, 'brain') and hasattr(self.agent.api.brain, 'model_path'):
                    model_name = os.path.basename(self.agent.api.brain.model_path)
            except:
                pass
            self.status_label.setText("🌸 本地大脑运行中")
            self.model_label.setText(f"模型: {model_name}")
        else:
            self.status_label.setText("⚠️ 本地大脑未启用")
            self.model_label.setText("模型: --")
        avg = (self.total_time / self.call_count) if self.call_count > 0 else 0
        self.calls_label.setText(f"调用次数: {self.call_count}")
        self.avg_time_label.setText(f"平均耗时: {avg:.0f}ms")
