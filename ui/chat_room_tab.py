# ui/chat_room_tab.py —— 稳定版
import threading, sqlite3, time
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLineEdit, QDialog, QTextBrowser)
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QTextCursor

CHAT_DB = "E:/LightAgent/Cache/chat_memory.db"

class ChatMemory:
    def __init__(self):
        self.conn = sqlite3.connect(CHAT_DB, check_same_thread=False)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS chat_log
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             timestamp REAL,
             role TEXT,
             content TEXT)""")
        self.conn.commit()

    def add(self, role, content):
        self.conn.execute("INSERT INTO chat_log (timestamp, role, content) VALUES (?,?,?)",
                         (time.time(), role, content))
        self.conn.commit()

    def get_all(self, limit=200):
        cur = self.conn.execute(
            "SELECT timestamp, role, content FROM chat_log ORDER BY timestamp ASC LIMIT ?", (limit,))
        return cur.fetchall()

class ChatRoomTab(QWidget):
    show_message = pyqtSignal(str, str)

    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.memory = ChatMemory()
        self.stop_requested = False
        self.init_ui()
        self.show_message.connect(self._add_message_safe)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5,5,5,5)

        self.chat_view = QTextEdit()
        self.chat_view.setReadOnly(True)
        self.chat_view.setFont(QFont("Segoe UI", 10))
        self.chat_view.setStyleSheet("background:#F7F7F7; border:1px solid #DDD; border-radius:8px; padding:10px;")
        layout.addWidget(self.chat_view)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入指令...")
        self.input_field.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("发送")
        self.send_btn.setStyleSheet("background:#4A90D9; color:white; border-radius:6px; padding:8px 16px;")
        self.send_btn.clicked.connect(self.send_message)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.setStyleSheet("background:#E74C3C; color:white; border-radius:6px; padding:8px 16px;")
        self.stop_btn.clicked.connect(self.stop)

        self.history_btn = QPushButton("📋 聊天记录")
        self.history_btn.clicked.connect(self.show_history)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.stop_btn)
        input_layout.addWidget(self.history_btn)
        layout.addLayout(input_layout)
        self.setLayout(layout)

    def send_message(self):
        text = self.input_field.text().strip()
        if not text: return
        self.show_message.emit("user", text)
        self.memory.add("user", text)
        self.input_field.clear()
        self.stop_requested = False
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        threading.Thread(target=self.process, args=(text,), daemon=True).start()

    def stop(self):
        self.stop_requested = True
        self.stop_btn.setEnabled(False)
        self.send_btn.setEnabled(True)

    def process(self, text):
        try:
            reply = self.agent.process_user_input(text)
            if reply and not self.stop_requested:
                self.show_message.emit("ai", reply)
                self.memory.add("ai", reply)
        except Exception as e:
            self.show_message.emit("ai", f"❌ 出错了：{e}")
        finally:
            self.send_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def _add_message_safe(self, sender, message):
        if sender == "user":
            color = "#4A90D9"
            prefix = "🧑 你"
        else:
            color = "#27AE60"
            prefix = "🤖 AI"
        html = f'<div style="margin:8px 0;"><b style="color:{color};">{prefix}:</b><div style="background:#FFFFFF; border-left:4px solid {color}; padding:8px; border-radius:4px; margin-top:4px;">{message}</div></div>'
        self.chat_view.append(html)
        cursor = self.chat_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_view.setTextCursor(cursor)

    def show_history(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("聊天记录")
        dlg.resize(600, 400)
        layout = QVBoxLayout()
        browser = QTextBrowser()
        records = self.memory.get_all()
        html = "<h3>最近聊天记录</h3><hr>"
        for ts, role, content in records:
            t = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            if role == "user":
                html += f"<p><b>[{t}] 你：</b>{content}</p>"
            else:
                html += f"<p><b style='color:#27AE60;'>[{t}] AI：</b>{content}</p>"
        browser.setHtml(html)
        layout.addWidget(browser)
        dlg.setLayout(layout)
        dlg.exec_()
