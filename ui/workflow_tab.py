# filename: E:\LightAgent\ui\workflow_tab.py
"""工作流编辑器 - 支持新建、编辑、导入导出 JSON 工作流，并可一键执行"""
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import json
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QPushButton, QTextEdit, QFileDialog, QMessageBox,
                             QInputDialog, QLabel)
from PyQt5.QtCore import Qt
import threading

class WorkflowTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.workflows = []  # 每个元素：{"name": str, "steps": list[str]}
        self.current_index = -1
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        # 工作流列表
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self.select_workflow)
        layout.addWidget(QLabel("工作流列表："))
        layout.addWidget(self.list_widget)

        # 步骤编辑区
        layout.addWidget(QLabel("步骤（每行一个自然语言指令或 /run 命令）："))
        self.steps_edit = QTextEdit()
        self.steps_edit.setPlaceholderText("例如：\n打开记事本\n/run 在桌面创建 test.txt 并写入 hello")
        layout.addWidget(self.steps_edit)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_new = QPushButton("新建")
        btn_new.clicked.connect(self.new_workflow)
        btn_delete = QPushButton("删除")
        btn_delete.clicked.connect(self.delete_workflow)
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_current)
        btn_run = QPushButton("执行当前工作流")
        btn_run.clicked.connect(self.run_workflow)
        btn_import = QPushButton("导入")
        btn_import.clicked.connect(self.import_workflow)
        btn_export = QPushButton("导出")
        btn_export.clicked.connect(self.export_workflow)
        btn_layout.addWidget(btn_new)
        btn_layout.addWidget(btn_delete)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_run)
        btn_layout.addWidget(btn_import)
        btn_layout.addWidget(btn_export)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def new_workflow(self):
        name, ok = QInputDialog.getText(self, "新建工作流", "输入工作流名称：")
        if ok and name:
            self.workflows.append({"name": name, "steps": []})
            self.list_widget.addItem(name)
            self.list_widget.setCurrentRow(len(self.workflows)-1)

    def delete_workflow(self):
        if self.current_index >= 0:
            del self.workflows[self.current_index]
            self.list_widget.takeItem(self.current_index)
            self.current_index = -1
            self.steps_edit.clear()

    def select_workflow(self, index):
        if index < 0 or index >= len(self.workflows):
            return
        self.current_index = index
        wf = self.workflows[index]
        self.steps_edit.setPlainText("\n".join(wf["steps"]))

    def save_current(self):
        if self.current_index < 0:
            return
        steps = self.steps_edit.toPlainText().strip().split("\n")
        steps = [s.strip() for s in steps if s.strip()]
        self.workflows[self.current_index]["steps"] = steps
        QMessageBox.information(self, "成功", "工作流已保存")

    def run_workflow(self):
        if self.current_index < 0:
            QMessageBox.warning(self, "提示", "请先选择一个工作流")
            return
        wf = self.workflows[self.current_index]
        if not wf["steps"]:
            QMessageBox.warning(self, "提示", "工作流没有步骤")
            return
        # 在后台依次执行每个步骤（调用 agent 处理）
        threading.Thread(target=self._execute_steps, args=(wf["steps"],), daemon=True).start()
        QMessageBox.information(self, "开始", "工作流已在后台开始执行，请查看控制台或监控面板。")

    def _execute_steps(self, steps):
        for step in steps:
            if step.startswith("/run"):
                task = step[4:].strip()
                self.agent.process_user_input(step, temperature=0.5)
            else:
                self.agent.process_user_input(step, temperature=0.7)

    def import_workflow(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入工作流", filter="JSON文件 (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.workflows.append(data)
            self.list_widget.addItem(data["name"])
            self.list_widget.setCurrentRow(len(self.workflows)-1)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败：{e}")

    def export_workflow(self):
        if self.current_index < 0:
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出工作流", filter="JSON文件 (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.workflows[self.current_index], f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "成功", "工作流已导出")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败：{e}")
