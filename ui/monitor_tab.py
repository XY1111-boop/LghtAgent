from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import time
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont, QTextCursor

class MonitorTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.start = time.time()
        self.init_ui()
        if hasattr(agent.logger, 'status_signal'):
            agent.logger.status_signal.connect(self.add_log)
            self.add_log("监控已连接")
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_status)
        self.timer.start(2000)
        QTimer.singleShot(0, self._delayed_init)
    def init_ui(self):
        layout = QVBoxLayout()
        self.status_label = QLabel("● 就绪")
        self.status_label.setStyleSheet("color:#4EC9B0; font-weight:bold;")
        layout.addWidget(self.status_label)
        self.log_view = QTextEdit(); self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        self.log_view.setStyleSheet("background:#1E1E1E; color:#D4D4D4;")
        layout.addWidget(self.log_view)
        self.setLayout(layout)
    def add_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        QTimer.singleShot(0, lambda: self._append(f"<span style='color:#888;'>[{ts}]</span> {msg}"))
    def _append(self, html):
        self.log_view.append(html)
        c = self.log_view.textCursor()
        c.movePosition(QTextCursor.End)
        self.log_view.setTextCursor(c)
    def refresh_status(self):
        uptime = time.time() - self.start
        h, rem = divmod(uptime, 3600)
        m, s = divmod(rem, 60)
        api_ok = bool(self.agent.config.get("api_key",""))
        self.status_label.setText(f"● 运行中 | API:{'已连接' if api_ok else '未配置'} | 运行:{int(h):02d}:{int(m):02d}:{int(s):02d}")

    def _delayed_init(self):
        """延迟初始化，在主事件循环启动后执行"""
        pass


    def update_ai_metrics(self, metrics):
        """接收AI内部指标并显示"""
        if hasattr(self, 'ai_metrics_label'):
            self.ai_metrics_label.setText(f"推理延迟: {metrics.get('latency',0)}ms | Token: {metrics.get('tokens',0)}")
