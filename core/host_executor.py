# core/host_executor.py —— 纯净版
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
