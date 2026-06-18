# clean_local_llm.py —— 用纯净版本替换 local_llm.py 及关键模块
import os, shutil

PROJECT = r"E:\LightAgent"

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已重写 {path}")

# ---------- 纯净版 local_llm.py ----------
pure_local_llm = r'''# intelligence/local_llm.py —— 纯净版（无任何外部注入）
import threading
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "qwen2.5-0.5b-instruct-q4_k_m.gguf"

class LocalBrain:
    def __init__(self, model_path=None, n_ctx=2048):
        path = model_path or MODEL_PATH
        self.llm = Llama(model_path=str(path), n_ctx=n_ctx, n_threads=4,
                         n_gpu_layers=16, verbose=False)
        self.lock = threading.Lock()

    def chat(self, messages, temperature=0.7, max_tokens=200):
        with self.lock:
            prompt = self._format(messages)
            out = self.llm(prompt, max_tokens=max_tokens, temperature=temperature,
                           top_p=0.9, repeat_penalty=1.1,
                           stop=["<|im_end|>", "<|user|>"], echo=False)
            return out["choices"][0]["text"].strip()

    def _format(self, messages):
        prompt = ""
        for m in messages:
            prompt += f"<|im_start|>{m['role']}\\n{m['content']}<|im_end|>\\n"
        prompt += "<|im_start|>assistant\\n"
        return prompt

_brain = None
def get_brain():
    global _brain
    if _brain is None:
        _brain = LocalBrain()
    return _brain
'''

# ---------- 纯净版 host_executor.py ----------
pure_host_executor = r'''# core/host_executor.py
import os
import subprocess
import webbrowser
import pyautogui
from pathlib import Path
import ast

ALLOWED_COMMANDS = ["dir", "echo", "calc", "notepad", "explorer", "tasklist", "ipconfig"]

class HostExecutor:
    def __init__(self, allowed_dir, logger=None):
        self.allowed_dir = Path(allowed_dir).resolve()
        self.logger = logger
        self.allowed_dir.mkdir(parents=True, exist_ok=True)

    def write_file(self, filename: str, content: str):
        full_path = (self.allowed_dir / filename).resolve()
        if not str(full_path).startswith(str(self.allowed_dir)):
            raise PermissionError("写入路径超出允许范围")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        if self.logger:
            self.logger.info(f"文件写入成功：{full_path}")

    def run_allowed_command(self, cmd: str):
        base_cmd = cmd.strip().split()[0].lower()
        if base_cmd not in ALLOWED_COMMANDS:
            raise PermissionError(f"命令 '{base_cmd}' 不在白名单中")
        subprocess.run(cmd, shell=True, check=False)

    def mouse_click(self, x: int, y: int):
        pyautogui.click(x, y)

    def keyboard_type(self, text: str):
        pyautogui.typewrite(text)

    def open_website(self, url: str):
        webbrowser.open(url)

    def execute_generated_code(self, code: str):
        allowed_funcs = {"write_file", "run_allowed_command", "mouse_click", "keyboard_type", "open_website"}
        try:
            tree = ast.parse(code)
        except SyntaxError:
            raise ValueError("代码语法错误")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id not in allowed_funcs:
                    raise PermissionError(f"不允许调用函数：{node.func.id}")
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                raise PermissionError("禁止 import 语句")
        exec_globals = {
            "write_file": self.write_file,
            "run_allowed_command": self.run_allowed_command,
            "mouse_click": self.mouse_click,
            "keyboard_type": self.keyboard_type,
            "open_website": self.open_website,
            "__builtins__": {"print": print}
        }
        exec(code, exec_globals)
'''

# 重写关键文件
safe_write("intelligence/local_llm.py", pure_local_llm)
safe_write("core/host_executor.py", pure_host_executor)

# 如果你还希望其他模块也恢复纯净，可同样重写
# 但 local_llm 和 host_executor 是之前出现 threading 问题的模块，重写它们足够

print("✅ 纯净版模块已就绪，请重启 LightAgent：python main.py")
print("   - 本地大脑将正常加载，不再有 threading 变量冲突")
print("   - 心跳上报已由 main.py 统一管理，无需在各模块内处理")
