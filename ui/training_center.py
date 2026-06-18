from PyQt5.QtGui import QTextCursor
# ui/training_center.py —— 详细日志版（完整代码可复制）
import threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QTextEdit, QListWidget,
                             QMessageBox, QInputDialog, QGroupBox, QGridLayout, QSplitter)
from PyQt5.QtCore import QTimer, Qt
from intelligence.experience_manager import ExperienceManager
from intelligence.training_engine import TrainingEngine

class TrainingCenterTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.engine = None
        self.manager = ExperienceManager()
        self.init_ui()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(1000)

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("🎓 智能训练中心（详细日志）")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #4A90D9;")
        layout.addWidget(title)

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("自动生成训练样本 (DeepSeek)")
        self.start_btn.clicked.connect(self.start_training)
        self.stop_btn = QPushButton("停止生成")
        self.stop_btn.clicked.connect(self.stop_training)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        manual_btn = QPushButton("手动添加样本")
        manual_btn.clicked.connect(self.manual_add)
        layout.addWidget(manual_btn)

        # 统计面板
        stats_group = QGroupBox("📊 学习统计")
        stats_layout = QGridLayout()
        self.total_label = QLabel("总样本: 0")
        self.used_label = QLabel("使用次数: 0")
        self.success_rate_label = QLabel("成功率: 0%")
        self.last_used_label = QLabel("最近使用: 无")
        self.generated_label = QLabel("本次生成: 0")
        self.passed_label = QLabel("已学习: 0")
        self.failed_label = QLabel("不合规: 0")
        self.skipped_label = QLabel("跳过重复: 0")
        self.efficiency_label = QLabel("学习效率: 0%")
        stats_layout.addWidget(self.total_label, 0, 0)
        stats_layout.addWidget(self.used_label, 0, 1)
        stats_layout.addWidget(self.success_rate_label, 1, 0)
        stats_layout.addWidget(self.last_used_label, 1, 1)
        stats_layout.addWidget(self.generated_label, 2, 0)
        stats_layout.addWidget(self.passed_label, 2, 1)
        stats_layout.addWidget(self.failed_label, 3, 0)
        stats_layout.addWidget(self.skipped_label, 3, 1)
        stats_layout.addWidget(self.efficiency_label, 4, 0)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 实时事件日志（允许复制，等宽字体）
        layout.addWidget(QLabel("📟 实时事件日志（点击内容可复制）："))
        self.event_log = QTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4; font-family: Consolas;")
        layout.addWidget(self.event_log)

        # 样本列表
        splitter = QSplitter(Qt.Vertical)
        list_widget = QWidget()
        list_layout = QVBoxLayout()
        list_layout.addWidget(QLabel("最近样本："))
        self.sample_list = QListWidget()
        list_layout.addWidget(self.sample_list)
        list_widget.setLayout(list_layout)
        splitter.addWidget(list_widget)
        layout.addWidget(splitter)

        clear_btn = QPushButton("清空经验库")
        clear_btn.clicked.connect(self.clear_experience)
        layout.addWidget(clear_btn)

        self.setLayout(layout)
        self.refresh_status()

    def log_event(self, msg, detail=""):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        QTimer.singleShot(0, lambda: self.event_log.append(f"[{timestamp}] {msg}"))
        if detail:
            QTimer.singleShot(0, lambda: self.event_log.append(f"{detail}"))
        # 自动滚动到底部
        cursor = self.event_log.textCursor()
        cursor.movePosition(cursor.End)
        self.event_log.setTextCursor(cursor)

    def start_training(self):
        if not self.agent.api:
            QMessageBox.warning(self, "错误", "请先配置 DeepSeek API Key")
            return
        reply = QMessageBox.question(self, "开始训练", "将使用 DeepSeek API 自动生成训练样本，是否继续？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.engine = TrainingEngine(self.agent.api, self.manager)
        self.engine.set_callback(lambda stats: self.refresh_status())
        self.engine.set_sample_callback(self.log_event)
        self.engine.start()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_training_progress)
        self.timer.start(500)
        self.log_event("🚀 训练开始")

    def update_training_progress(self):
        if self.engine:
            self.progress_bar.setMaximum(self.engine.total)
            self.progress_bar.setValue(self.engine.progress)
            self.status_label.setText(self.engine.status)
            self.refresh_status()
            if not self.engine.running:
                # 训练已结束，清理 UI
                self.timer.stop()
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.progress_bar.setVisible(False)
                final_msg = "✅ 训练完成" if self.engine.progress >= self.engine.total else "⏹ 训练已停止"
                self.log_event(final_msg, f"生成: {self.engine.stats['generated']}  已学习: {self.engine.stats['passed']}  跳过: {self.engine.stats['skipped']}  不合规: {self.engine.stats['failed']}")
        else:
            # 如果引擎意外丢失，也重置 UI
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)

    def stop_training(self):
        # 立即更新 UI，确保按钮和进度条响应
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("已停止")
        self.progress_bar.setVisible(False)
        if hasattr(self, 'timer'):
            self.timer.stop()
        if self.engine:
            self.engine.stop()
        self.log_event("⏹ 训练已手动停止")

    def manual_add(self):
        instruction, ok = QInputDialog.getText(self, "添加样本", "用户指令:")
        if not ok or not instruction:
            return
        code, ok = QInputDialog.getMultiLineText(self, "添加样本", "对应的 Python 代码:")
        if not ok or not code:
            return
        if self.manager.add_experience(instruction, code, "手动添加"):
            self.log_event(f"📝 手动添加: {instruction}", f"代码:\n{code}")
            self.refresh_status()
            QMessageBox.information(self, "成功", "样本已添加")
        else:
            self.log_event(f"⚠️ 重复跳过: {instruction}", f"代码:\n{code}")
            QMessageBox.warning(self, "重复", "该指令已存在（或相似度过高），未添加。")

    def clear_experience(self):
        reply = QMessageBox.question(self, "确认", "清空所有训练样本？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.manager.clear()
            self.refresh_status()
            self.log_event("🗑️ 经验库已清空")

    def refresh_status(self):
        stats = self.manager.get_stats()
        self.total_label.setText(f"总样本: {stats['total']}")
        self.used_label.setText(f"使用次数: {stats['used']}")
        self.success_rate_label.setText(f"成功率: {stats['success_rate']*100:.1f}%")
        self.last_used_label.setText(f"最近使用: {stats['last_used'] or '无'}")
        if self.engine:
            self.generated_label.setText(f"本次生成: {self.engine.stats['generated']}")
            self.passed_label.setText(f"已学习: {self.engine.stats['passed']}")
            self.failed_label.setText(f"不合规: {self.engine.stats['failed']}")
            self.skipped_label.setText(f"跳过重复: {self.engine.stats['skipped']}")
            total = self.engine.stats['generated']
            learned = self.engine.stats['passed']
            eff = (learned / total * 100) if total > 0 else 0
            self.efficiency_label.setText(f"学习效率: {eff:.1f}%")
        self.sample_list.clear()
        for exp in self.manager.get_all()[-50:]:
            self.sample_list.addItem(f"{exp['instruction']} → {exp['code'][:50]}...")
