from PyQt5.QtGui import QTextCursor
# filename: E:\LightAgent\ui\console_tab.py
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLineEdit
import threading

class ConsoleTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        layout = QVBoxLayout()
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setStyleSheet("background-color: #FAFAFA;")
        layout.addWidget(self.chat_area)
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息，或 /run 任务...")
        self.input_field.returnPressed.connect(self.send_message)
        send_btn = QPushButton("发送")
        send_btn.setStyleSheet("background-color: #4A90D9; color: white;")
        send_btn.clicked.connect(self.send_message)
        brainstorm_btn = QPushButton("头脑风暴")
        brainstorm_btn.setStyleSheet("background-color: #FFA500; color: white;")
        brainstorm_btn.clicked.connect(self.brainstorm)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        input_layout.addWidget(brainstorm_btn)
        layout.addLayout(input_layout)
        self.setLayout(layout)

    def send_message(self):
        text = self.input_field.text().strip()
        if not text: return
        QTimer.singleShot(0, lambda: self.chat_area.append(f"<b>你:</b> {text}"))
        self.input_field.clear()
        threading.Thread(target=self._process, args=(text, 0.7), daemon=True).start()

    def brainstorm(self):
        text = self.input_field.text().strip()
        if not text: return
        QTimer.singleShot(0, lambda: self.chat_area.append(f"<b>你 (头脑风暴):</b> {text}"))
        self.input_field.clear()
        threading.Thread(target=self._process, args=(text, 1.0), daemon=True).start()

    def _process(self, text, temp):
        reply = self.agent.process_user_input(text, temperature=temp)
        QTimer.singleShot(0, lambda: self.chat_area.append(f"<b>LightAgent:</b> {reply}"))
