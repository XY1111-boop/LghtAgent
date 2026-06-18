# streamline_local_brain.py —— 精简模块，并将多模态融入本地大脑
import os, shutil, re

PROJECT = r"E:\LightAgent"

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 {path}")

def safe_delete(path):
    full = os.path.join(PROJECT, path)
    if os.path.exists(full):
        os.remove(full)
        print(f"🗑️ 已删除 {path}")

# ─── 1. 删除独立的模块文件 ───
files_to_delete = [
    "intelligence/user_manager.py",
    "intelligence/api_gateway.py",
    "intelligence/task_scheduler.py",
    "intelligence/multimodal_io.py",
    "ui/user_manager_tab.py",
    "ui/api_gateway_tab.py",
    "ui/scheduler_tab.py",
    "ui/multimodal_tab.py",
]
for f in files_to_delete:
    safe_delete(f)

# ─── 2. 从 main.py 中移除相关初始化代码 ───
main_path = os.path.join(PROJECT, "main.py")
if os.path.exists(main_path):
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 移除 _init_user_manager, _init_api_gateway, _init_task_scheduler, _init_multimodal 方法
    for method in ["_init_user_manager", "_init_api_gateway", "_init_task_scheduler", "_init_multimodal"]:
        pattern = rf'    def {method}\(self\).*?(?=\n    def |\nclass |\Z)'
        content = re.sub(pattern, '', content, flags=re.DOTALL)

    # 移除对应的 _safe_init 调用
    for call in [
        'self._safe_init("用户管理", self._init_user_manager)',
        'self._safe_init("API网关", self._init_api_gateway)',
        'self._safe_init("任务调度器", self._init_task_scheduler)',
        'self._safe_init("多模态IO", self._init_multimodal)',
    ]:
        content = content.replace(call, '')

    with open(main_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main.py 已清理")

# ─── 3. 从 main_window.py 中移除相关标签页 ───
mainwin_path = os.path.join(PROJECT, "ui", "main_window.py")
if os.path.exists(mainwin_path):
    with open(mainwin_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 移除导入
    imports_to_remove = [
        "from ui.multimodal_tab import MultimodalTab",
        "from ui.scheduler_tab import SchedulerTab",
        "from ui.api_gateway_tab import APIGatewayTab",
        "from ui.user_manager_tab import UserManagerTab",
    ]
    for imp in imports_to_remove:
        content = content.replace(imp + "\n", "")
        content = content.replace(imp, "")

    # 移除 TAB_CONFIG 中的条目
    tabs_to_remove = [
        '("🎤 多模态", "ui.multimodal_tab", "MultimodalTab")',
        '("📋 任务", "ui.scheduler_tab", "SchedulerTab")',
        '("🌐 API网关", "ui.api_gateway_tab", "APIGatewayTab")',
        '("👥 用户", "ui.user_manager_tab", "UserManagerTab")',
    ]
    for tab in tabs_to_remove:
        content = content.replace(tab + ",", "")
        content = content.replace(tab, "")

    with open(mainwin_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main_window.py 已清理")

# ─── 4. 将多模态能力融入本地大脑 ───
# 我们修改 local_llm.py，让 LocalBrain 拥有听说的能力
llm_path = os.path.join(PROJECT, "intelligence", "local_llm.py")
if os.path.exists(llm_path):
    with open(llm_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 在 LocalBrain 类中添加多模态方法
    multimodal_methods = '''
    # 多模态能力
    def listen_and_process(self):
        """监听麦克风，返回识别文本"""
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source)
                print("🎤 正在聆听...")
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
            try:
                import vosk
                return r.recognize_vosk(audio, language="zh-CN")
            except:
                return r.recognize_google(audio, language="zh-CN")
        except Exception as e:
            return f"语音识别失败: {e}"

    def speak_text(self, text):
        """朗读文本（异步）"""
        import threading, pyttsx3
        def _speak():
            tts = pyttsx3.init()
            tts.say(text)
            tts.runAndWait()
        threading.Thread(target=_speak, daemon=True).start()

    def analyze_image(self, image_path):
        """分析图像内容"""
        try:
            from PIL import Image
            import pytesseract
            img = Image.open(image_path)
            info = f"尺寸: {img.size}, 模式: {img.mode}"
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            if text.strip():
                info += f"\\n识别文字: {text[:200]}"
            return info
        except Exception as e:
            return f"图像分析失败: {e}"
'''

    # 插入到 LocalBrain 类中（在 chat 方法之前）
    if "def chat(self, messages, temperature=0.7, max_tokens=200):" in content:
        content = content.replace(
            "def chat(self, messages, temperature=0.7, max_tokens=200):",
            multimodal_methods + "\n    def chat(self, messages, temperature=0.7, max_tokens=200):"
        )
        with open(llm_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ local_llm.py 已融合多模态能力")
    else:
        print("⚠️ 未找到 chat 方法，请手动添加多模态方法")

# ─── 5. 在 AI 控制台中添加语音/图像按钮（修改 ai_console.py） ───
console_path = os.path.join(PROJECT, "ui", "ai_console.py")
if os.path.exists(console_path):
    with open(console_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 添加语音按钮（在发送按钮旁边）
    if "语音" not in content:
        # 在 init_ui 的按钮布局中添加
        old_buttons = '''self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_command)'''
        new_buttons = '''self.send_btn = QPushButton("发送")
        self.send_btn.clicked.connect(self.send_command)
        self.voice_btn = QPushButton("🎤 语音")
        self.voice_btn.clicked.connect(self.voice_input)
        self.img_btn = QPushButton("🖼️ 图片")
        self.img_btn.clicked.connect(self.image_input)'''
        content = content.replace(old_buttons, new_buttons)

        # 添加按钮到布局
        if "input_layout.addWidget(self.send_btn)" in content:
            content = content.replace(
                "input_layout.addWidget(self.send_btn)",
                "input_layout.addWidget(self.send_btn)\n        input_layout.addWidget(self.voice_btn)\n        input_layout.addWidget(self.img_btn)"
            )

        # 添加语音和图像处理函数
        extra_methods = '''
    def voice_input(self):
        import threading
        self.output_area.append("🎤 正在聆听...")
        def listen():
            text = self.agent.api.brain.listen_and_process()
            self.output_area.append(f"识别: {text}")
            if text:
                reply = self.agent.process_user_input(text)
                self.output_area.append(f"AI: {reply}")
                if hasattr(self.agent.api.brain, 'speak_text'):
                    self.agent.api.brain.speak_text(reply)
        threading.Thread(target=listen, daemon=True).start()

    def image_input(self):
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            result = self.agent.api.brain.analyze_image(path)
            self.output_area.append(f"图像分析: {result}")
'''
        # 插入到类中
        if "class AIConsoleTab" in content:
            # 找到类的末尾，添加方法
            class_end = content.rfind("def send_command(self):")
            if class_end != -1:
                content = content[:class_end] + extra_methods + "\n    " + content[class_end:]
        with open(console_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ AI控制台已添加语音/图像按钮")

print("\n🎉 精简融合完成！重启 LightAgent：python main.py")
print("   - 用户管理、API网关、任务调度已移除")
print("   - 张瑶瑶现在会听（语音输入）、会说（TTS朗读）、会看（图像分析）")
print("   - AI控制台新增 🎤 语音 和 🖼️ 图片 按钮")
