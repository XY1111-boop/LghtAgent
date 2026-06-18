from PyQt5.QtGui import QTextCursor
# ui/memory_viewer_tab.py —— 稳定版
import sqlite3, time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLineEdit, QMessageBox,
                             QHeaderView)
from PyQt5.QtCore import Qt

class MemoryViewerTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.db_path = "E:/LightAgent/Cache/memory.db"
        self.init_ui()
        self.load_memories()

    def init_ui(self):
        layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入关键词搜索记忆...")
        self.search_input.returnPressed.connect(self.load_memories)
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.load_memories)
        refresh_btn = QPushButton("刷新全部")
        refresh_btn.clicked.connect(lambda: self.load_memories(reset=True))
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(refresh_btn)
        search_layout.addWidget(delete_btn)
        layout.addLayout(search_layout)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "时间", "类型", "内容"])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_memories(self, reset=False):
        search_text = "" if reset else self.search_input.text().strip()
        try:
            conn = sqlite3.connect(self.db_path)
            if search_text:
                cur = conn.execute(
                    "SELECT id, timestamp, memory_type, content FROM permanent_memory WHERE content LIKE ? ORDER BY timestamp DESC LIMIT 200",
                    (f'%{search_text}%',))
            else:
                cur = conn.execute(
                    "SELECT id, timestamp, memory_type, content FROM permanent_memory ORDER BY timestamp DESC LIMIT 200")
            rows = cur.fetchall()
            conn.close()
            self.table.setRowCount(0)
            for row in rows:
                r = self.table.rowCount()
                self.table.insertRow(r)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[0])))
                ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row[1]))
                self.table.setItem(r, 1, QTableWidgetItem(ts))
                self.table.setItem(r, 2, QTableWidgetItem(row[2]))
                self.table.setItem(r, 3, QTableWidgetItem(row[3][:200]))
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取记忆失败：{e}")

    def delete_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "提示", "请先选中要删除的记忆行")
            return
        row = selected[0].row()
        mem_id = self.table.item(row, 0).text()
        reply = QMessageBox.question(self, "确认", f"确定要删除记忆 ID={mem_id} 吗？",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("DELETE FROM permanent_memory WHERE id=?", (mem_id,))
                conn.commit()
                conn.close()
                self.load_memories()
                if hasattr(self.agent, "logger"):
                    self.agent.logger.info(f"已删除记忆 ID={mem_id}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"删除失败：{e}")
