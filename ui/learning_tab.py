from PyQt5.QtGui import QTextCursor
# filename: E:\LightAgent\ui\learning_tab.py
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import os, threading
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QPushButton, QTextEdit, QFileDialog, QMessageBox,
                             QLabel, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from knowledge.file_processor import extract_text_from_file

class LearningTab(QWidget):
    # 各种 UI 更新信号，全部在主线程处理
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)          # 设置进度条值
    show_progress_signal = pyqtSignal(bool)    # 显示/隐藏进度条
    result_signal = pyqtSignal(str)            # 添加结果文本

    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.file_queue = []
        self.stop_requested = False
        self.init_ui()
        self.status_signal.connect(self.update_status_label)
        self.progress_signal.connect(self.progress.setValue)
        self.show_progress_signal.connect(self.progress.setVisible)
        self.result_signal.connect(self.result_view.append)
        if hasattr(self.agent, "logger"):
            self.agent.logger.info("学习中心就绪")
        QTimer.singleShot(0, self._delayed_init)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("待处理文件（支持拖拽或多选添加）："))
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(True)
        self.file_list.dragEnterEvent = self.dragEnterEvent
        self.file_list.dropEvent = self.dropEvent
        layout.addWidget(self.file_list)

        btn_layout = QHBoxLayout()
        btn_add = QPushButton("添加文件")
        btn_add.clicked.connect(self.add_file)
        btn_remove = QPushButton("移除选中")
        btn_remove.clicked.connect(self.remove_file)
        btn_process = QPushButton("开始处理")
        btn_process.clicked.connect(self.start_processing)
        btn_stop = QPushButton("停止处理")
        btn_stop.clicked.connect(self.stop_processing)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addWidget(btn_process)
        btn_layout.addWidget(btn_stop)
        layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_label = QLabel("就绪")
        layout.addWidget(self.status_label)

        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setStyleSheet("background-color: #F5F5F5;")
        layout.addWidget(QLabel("处理结果："))
        layout.addWidget(self.result_view)

        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                self.file_queue.append(path)
                self.file_list.addItem(path)

    def add_file(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择文件")
        for p in paths:
            self.file_queue.append(p)
            self.file_list.addItem(p)

    def remove_file(self):
        row = self.file_list.currentRow()
        if row >= 0:
            removed = self.file_queue.pop(row)
            self.file_list.takeItem(row)

    def start_processing(self):
        if not self.file_queue:
            QMessageBox.warning(self, "提示", "请先添加文件")
            return
        self.stop_requested = False
        self.show_progress_signal.emit(True)
        self.progress_signal.emit(0)
        threading.Thread(target=self.process_files, daemon=True).start()

    def stop_processing(self):
        self.stop_requested = True
        self.status_signal.emit("用户请求停止处理")

    def process_files(self):
        try:
            for i, file_path in enumerate(self.file_queue.copy()):
                if self.stop_requested:
                    self.status_signal.emit("处理已停止")
                    break
                self.status_signal.emit(f"正在处理：{os.path.basename(file_path)}")
                try:
                    success, card = self.agent.learning_center.process_file(file_path)
                except Exception as e:
                    success, card = False, str(e)
                if success:
                    self.status_signal.emit(f"✅ {os.path.basename(file_path)} 完成")
                    # 通过信号发送结果，避免直接操作 UI
                    self.result_signal.emit(f"<b>{os.path.basename(file_path)}</b><br>{card}<hr>")
                else:
                    self.status_signal.emit(f"❌ {os.path.basename(file_path)} 失败：{card}")
                self.progress_signal.emit(i+1)
        except Exception as e:
            self.status_signal.emit(f"线程异常：{e}")
        finally:
            self.show_progress_signal.emit(False)
            self.status_signal.emit("全部处理完毕")

    def update_status_label(self, msg):
        self.status_label.setText(msg)

    def _delayed_init(self):
        """延迟初始化，在主事件循环启动后执行"""
        pass

