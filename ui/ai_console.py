from PyQt5.QtGui import QTextCursor
# ui/ai_console.py —— 含虚拟形象
import sys, re, threading, time
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLineEdit, QLabel, QFileDialog)
from PyQt5.QtCore import Qt, QTimer, QTimer
from PyQt5.QtGui import QFont, QPixmap
from PIL import Image
import io

class AIConsoleTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.stop_requested = False
        self.init_ui()
        self.update_avatar("neutral", 0.0)  # 初始表情

    def init_ui(self):
        layout = QVBoxLayout()
        # 虚拟形象
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(200, 200)
        self.avatar_label.setAlignment(Qt.AlignCenter)
        self.avatar_label.setStyleSheet("border: 2px solid #CCC; background-color: #FFF;")
        layout.addWidget(self.avatar_label)

        # 输入区
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入指令或点击语音/图片...")
        self.input_field.returnPressed.connect(self.send_command)
        self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_command)
        self.voice_btn = QPushButton("🎤 语音")
        self.voice_btn.clicked.connect(self.voice_input)
        self.img_btn = QPushButton("🖼️ 图片")
        self.img_btn.clicked.connect(self.image_input)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        input_layout.addWidget(self.voice_btn)
        input_layout.addWidget(self.img_btn)
        layout.addLayout(input_layout)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)
        self.setLayout(layout)

    def update_avatar(self, expression, lip_open):
        """更新虚拟形象"""
        try:
            if hasattr(self.agent.api, 'brain') and hasattr(self.agent.api.brain, 'render_avatar'):
                img = self.agent.api.brain.render_avatar(expression, lip_open)
                img.save("temp_avatar.png")
                self.avatar_label.setPixmap(QPixmap("temp_avatar.png"))
        except Exception as e:
            print(f"更新虚拟形象失败: {e}")

    def send_command(self):
        text = self.input_field.text().strip()
        if not text: return
        self.output_area.append(f"<b>▶ 指令：</b>{text}")
        self.input_field.clear()
        self.stop_requested = False
        self.update_avatar("listening", 0.5)
        threading.Thread(target=self._process, args=(text, 0.7), daemon=True).start()

    def voice_input(self):
        self.output_area.append("🎤 正在聆听...")
        self.update_avatar("listening", 0.8)
        threading.Thread(target=self._voice_thread, daemon=True).start()

    def _voice_thread(self):
        try:
            text = self.agent.api.brain.listen_and_process()
            self.output_area.append(f"识别: {text}")
            if text and "失败" not in text:
                reply = self.agent.process_user_input(text)
                self.output_area.append(f"AI: {reply}")
                if hasattr(self.agent.api.brain, 'speak_text'):
                    self.agent.api.brain.speak_text(reply)
        except Exception as e:
            self.output_area.append(f"语音异常: {e}")
        self.update_avatar("neutral", 0.0)

    def image_input(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            result = self.agent.api.brain.analyze_image(path)
            self.output_area.append(f"图像分析: {result}")
            self.update_avatar("happy", 0.3)

    def _process(self, text, temp):
        try:
            reply = self.agent.process_user_input(text, temperature=temp)
            if not self.stop_requested:
                self.output_area.append(f"<b style='color:#27AE60;'>🤖 AI 回答：</b>{reply}")
                try:
                    if hasattr(self.agent.api.brain, 'speak_text'):
                        self.agent.api.brain.speak_text(reply)
                except:
                    pass
        except Exception as e:
            self.output_area.append(f"<span style='color:#F44747;'>💥 内部错误: {e}</span>")
        reply = self.agent.process_user_input(text, temperature=temp)
        if not self.stop_requested:
            QTimer.singleShot(0, lambda: self.output_area.append(f"<b style='color:#27AE60;'>🤖 AI 回答：</b>{reply}"))
            try:
                if hasattr(self.agent.api.brain, 'speak_text'):
                    self.agent.api.brain.speak_text(reply)
            except:
                pass
            QTimer.singleShot(0, lambda: self.update_avatar("happy", 0.2))
        reply = self.agent.process_user_input(text, temperature=temp)
        if not self.stop_requested:
            self.output_area.append(f"<b style='color:#27AE60;'>🤖 AI 回答：</b>{reply}")
            try:
                if hasattr(self.agent.api.brain, 'speak_text'):
                    self.agent.api.brain.speak_text(reply)
            except:
                pass
            self.update_avatar("happy", 0.2)
