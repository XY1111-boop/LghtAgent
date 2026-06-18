# merge_vtuber_to_brain.py —— 将虚拟主播融入本地大脑，移除独立标签页
import os, shutil, re

PROJECT = r"E:\LightAgent"

def safe_delete(path):
    full = os.path.join(PROJECT, path)
    if os.path.exists(full):
        os.remove(full)
        print(f"🗑️ 已删除 {path}")

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 {path}")

# ─── 1. 删除独立的虚拟主播文件 ───
safe_delete("intelligence/vtuber_engine.py")
safe_delete("ui/vtuber_tab.py")

# ─── 2. 从 main_window.py 中移除虚拟主播标签页 ───
mainwin_path = os.path.join(PROJECT, "ui", "main_window.py")
if os.path.exists(mainwin_path):
    with open(mainwin_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 移除导入
    content = content.replace("from ui.vtuber_tab import VTuberTab\n", "")
    content = content.replace("from ui.vtuber_tab import VTuberTab", "")

    # 移除 TAB_CONFIG 中的条目
    content = content.replace('    ("🎤 虚拟主播", "ui.vtuber_tab", "VTuberTab"),\n', "")
    content = content.replace('    ("🎤 虚拟主播", "ui.vtuber_tab", "VTuberTab"),', "")

    with open(mainwin_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main_window.py 已移除虚拟主播标签页")

# ─── 3. 增强本地大脑：增加虚拟形象渲染和TTS ───
llm_path = os.path.join(PROJECT, "intelligence", "local_llm.py")
if os.path.exists(llm_path):
    with open(llm_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 添加简易虚拟形象渲染方法（用PIL生成动态表情）
    avatar_method = '''
    def render_avatar(self, expression="neutral", lip_open=0.0):
        """生成简易Live2D风格头像（PIL绘制）"""
        from PIL import Image, ImageDraw
        img = Image.new('RGBA', (200, 200), (255,255,255,0))
        draw = ImageDraw.Draw(img)
        # 脸
        draw.ellipse((30, 20, 170, 160), fill=(255, 220, 180))
        # 眼睛
        draw.ellipse((60, 60, 80, 80), fill=(0,0,0))
        draw.ellipse((120, 60, 140, 80), fill=(0,0,0))
        # 嘴巴（根据lip_open开合）
        mouth_y = 100
        mouth_h = int(10 + lip_open * 30)
        draw.ellipse((80, mouth_y, 120, mouth_y + mouth_h), fill=(200,100,100))
        return img
'''

    # 插入到类中
    if "def chat(self, messages, temperature=0.7, max_tokens=200):" in content:
        content = content.replace(
            "def chat(self, messages, temperature=0.7, max_tokens=200):",
            avatar_method + "\n    def chat(self, messages, temperature=0.7, max_tokens=200):"
        )
    else:
        # 追加到类末尾
        content += avatar_method

    with open(llm_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ local_llm.py 已融合虚拟形象渲染能力")

# ─── 4. 修改AI控制台，添加虚拟形象显示和TTS朗读 ───
console_path = os.path.join(PROJECT, "ui", "ai_console.py")
if os.path.exists(console_path):
    with open(console_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 在 init_ui 中添加一个 QLabel 用于显示虚拟形象
    if "avatar_label" not in content:
        # 在布局开头插入
        old_init = "def init_ui(self):"
        new_init = '''def init_ui(self):
        # 虚拟形象显示区
        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(200, 200)
        self.avatar_label.setStyleSheet("border: 2px solid #CCC; background-color: #FFF;")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.addWidget(self.avatar_label)'''
        content = content.replace(old_init, new_init)

    # 在发送消息时更新虚拟形象（简单随机表情）和TTS朗读
    if "def send_command(self):" in content:
        old_send = "def send_command(self):"
        new_send = '''def send_command(self):
        # 更新虚拟形象为聆听状态
        self.update_avatar("listening", 0.5)
        text = self.input_field.text().strip()
        if not text: return
        self.output_area.append(f"<b style='color:#6A9955;'>▶ 指令：</b>{text}")
        self.input_field.clear()
        self.stop_requested = False
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()'''
        content = content.replace(old_send, new_send)

    # 在 _process 中（原处理函数）添加朗读和恢复表情
    old_process = "def _process(self, text, temp):"
    new_process = '''def _process(self, text, temp):
        reply = self.agent.process_user_input(text, temperature=temp)
        if not self.stop_requested:
            self.append_output(f"<span style='color:#569CD6;'>🤖 AI 回答：</span>{reply}")
            # TTS朗读（如果本地大脑有speak_text方法）
            try:
                if hasattr(self.agent.api, 'brain') and hasattr(self.agent.api.brain, 'speak_text'):
                    self.agent.api.brain.speak_text(reply)
            except:
                pass
            # 更新虚拟形象为微笑
            self.update_avatar("happy", 0.2)'''
    content = content.replace(old_process, new_process)

    # 添加 update_avatar 方法
    avatar_update_method = '''
    def update_avatar(self, expression, lip_open):
        """更新虚拟形象显示"""
        try:
            if hasattr(self.agent.api, 'brain') and hasattr(self.agent.api.brain, 'render_avatar'):
                img = self.agent.api.brain.render_avatar(expression, lip_open)
                # 将PIL图像转为QPixmap
                from PyQt5.QtGui import QPixmap
                img.save("temp_avatar.png")
                self.avatar_label.setPixmap(QPixmap("temp_avatar.png"))
        except:
            pass
'''
    if "update_avatar" not in content:
        # 插入到类中
        class_end = content.rfind("def send_command(self):")
        if class_end != -1:
            content = content[:class_end] + avatar_update_method + "\n    " + content[class_end:]
        else:
            content += avatar_update_method

    with open(console_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ AI控制台已集成虚拟形象显示和TTS朗读")

# ─── 5. 确保本地大脑有 speak_text 方法（从之前的融合中可能已包含） ───
if os.path.exists(llm_path):
    with open(llm_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "def speak_text(self, text):" not in content:
        speak_method = '''
    def speak_text(self, text):
        """朗读文本（异步）"""
        import threading, pyttsx3
        def _speak():
            tts = pyttsx3.init()
            tts.say(text)
            tts.runAndWait()
        threading.Thread(target=_speak, daemon=True).start()
'''
        # 插入到类中
        if "def chat(self, messages, temperature=0.7, max_tokens=200):" in content:
            content = content.replace(
                "def chat(self, messages, temperature=0.7, max_tokens=200):",
                speak_method + "\n    def chat(self, messages, temperature=0.7, max_tokens=200):"
            )
        else:
            content += speak_method
        with open(llm_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ local_llm.py 补充了 TTS 朗读方法")

print("\n🎉 虚拟主播融合完成！重启 LightAgent：python main.py")
print("   - 虚拟主播标签页已移除")
print("   - AI控制台新增虚拟形象显示区")
print("   - 张瑶瑶现在会说话（TTS朗读回复），并有简单表情变化")
