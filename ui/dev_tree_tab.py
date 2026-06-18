# ui/dev_tree_tab.py
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTreeView, QFileSystemModel,
                             QLineEdit, QPushButton, QHBoxLayout, QHeaderView)
from PyQt5.QtCore import QDir, Qt, QSortFilterProxyModel

class DevTreeTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.model = QFileSystemModel()
        root_path = str(agent.config.get("project_root", "E:/LightAgent"))
        self.model.setRootPath(root_path)
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setRecursiveFilteringEnabled(True)

        self.tree = QTreeView()
        self.tree.setModel(self.proxy_model)
        self.tree.setRootIndex(self.proxy_model.mapFromSource(
            self.model.index(root_path)))
        self.tree.setAnimated(True)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)

        # 修复 Pylance 警告：检查 header() 是否为 None
        header = self.tree.header()
        if header is not None:
            header.setSectionResizeMode(0, QHeaderView.Stretch)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索文件或文件夹...")
        self.search_input.textChanged.connect(self.filter_tree)

        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_tree)

        layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(refresh_btn)
        layout.addLayout(search_layout)
        layout.addWidget(self.tree)
        self.setLayout(layout)

    def filter_tree(self, text):
        self.proxy_model.setFilterFixedString(text)

    def refresh_tree(self):
        root_path = str(self.agent.config.get("project_root", "E:/LightAgent"))
        self.model.setRootPath(root_path)
