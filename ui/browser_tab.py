# filename: E:\LightAgent\ui\browser_tab.py
"""本地文件浏览器 - 支持预览、右键菜单、拖拽加入知识库"""
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import os
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeView, QMenu, QAction,
                             QFileSystemModel, QMessageBox, QInputDialog, QLineEdit,
                             QTextEdit, QSplitter, QLabel)
from PyQt5.QtCore import Qt, QDir, QUrl
from PyQt5.QtGui import QDesktopServices

class BrowserTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.model = QFileSystemModel()
        self.model.setRootPath("E:/")
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(agent.config.get("knowledge_raw_dir", str(PROJECT_ROOT / "Knowledge/raw")))))
        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.doubleClicked.connect(self.open_file)

        # 预览面板
        self.preview_label = QLabel("文件预览将显示在此处")
        self.preview_label.setWordWrap(True)
        self.preview_label.setAlignment(Qt.AlignTop)
        self.preview_label.setStyleSheet("background-color: #F5F5F5; padding: 10px;")

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tree)
        splitter.addWidget(self.preview_label)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def show_context_menu(self, position):
        indexes = self.tree.selectedIndexes()
        if not indexes:
            return
        file_path = self.model.filePath(indexes[0])
        menu = QMenu()

        act_open = QAction("打开文件")
        act_open.triggered.connect(lambda: self.open_file(indexes[0]))
        menu.addAction(act_open)

        act_open_folder = QAction("在资源管理器中打开")
        act_open_folder.triggered.connect(lambda: subprocess.Popen(f'explorer /select,"{file_path}"'))
        menu.addAction(act_open_folder)

        act_add_kb = QAction("加入知识库")
        act_add_kb.triggered.connect(lambda: self.agent.knowledge_base.add_to_raw(file_path))
        menu.addAction(act_add_kb)

        act_preview = QAction("预览内容")
        act_preview.triggered.connect(lambda: self.preview_file(file_path))
        menu.addAction(act_preview)

        menu.exec_(self.tree.viewport().mapToGlobal(position))

    def open_file(self, index=None):
        if index is None:
            indexes = self.tree.selectedIndexes()
            if not indexes:
                return
            index = indexes[0]
        file_path = self.model.filePath(index)
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件：{e}")

    def preview_file(self, file_path):
        """预览文本或图片信息"""
        if not os.path.isfile(file_path):
            self.preview_label.setText("请选择一个文件")
            return
        try:
            size = os.path.getsize(file_path)
            info = f"文件名：{os.path.basename(file_path)}\n大小：{size} 字节"
            # 简单显示文本文件前1000字符
            if file_path.lower().endswith(('.txt', '.md', '.py', '.json', '.yaml', '.csv')):
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1000)
                info += f"\n\n内容预览：\n{content}"
            self.preview_label.setText(info)
        except Exception as e:
            self.preview_label.setText(f"预览失败：{e}")
