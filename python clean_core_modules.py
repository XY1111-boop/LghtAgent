# clean_core_modules.py —— 替换所有被污染的核心模块为纯净版
import os, shutil

PROJECT = r"E:\LightAgent"

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已替换为纯净版: {path}")

# ═══════════════════════════════════════
# 1. 纯净版 local_llm.py
# ═══════════════════════════════════════
local_llm = r'''# intelligence/local_llm.py —— 纯净版
import threading
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).resolve().parent.parent / "models"

def find_model():
    models = list(MODEL_PATH.glob("*.gguf"))
    if models:
        return str(models[0])
    raise FileNotFoundError("未找到任何 .gguf 模型文件")

class LocalBrain:
    def __init__(self, model_path=None, n_ctx=2048):
        path = model_path or find_model()
        self.model_path = str(path)
        self.llm = Llama(model_path=self.model_path, n_ctx=n_ctx, n_threads=4,
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

# ═══════════════════════════════════════
# 2. 纯净版 memory.py
# ═══════════════════════════════════════
memory = r'''# intelligence/memory.py —— 纯净版
import threading
import sqlite3
import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

class MemoryManager:
    def __init__(self, api, db_path="E:/LightAgent/Cache/memory.db", max_entries=10000):
        self.api = api
        self.db_path = db_path
        self.max_entries = max_entries
        self.lock = threading.Lock()
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS permanent_memory
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             timestamp REAL,
                             memory_type TEXT,
                             content TEXT,
                             importance_score REAL)""")
        self.conn.commit()

    def add_memory(self, memory_type, content, importance=0.5):
        with self.lock:
            self.conn.execute(
                "INSERT INTO permanent_memory (timestamp, memory_type, content, importance_score) VALUES (?,?,?,?)",
                (time.time(), memory_type, content, importance))
            self.conn.commit()
        self._enforce_limit()

    def retrieve_relevant(self, query, top_k=5):
        with self.lock:
            cur = self.conn.execute("SELECT id, content, importance_score FROM permanent_memory")
            rows = cur.fetchall()
            if not rows:
                return []
            documents = [row[1] for row in rows]
            vectorizer = TfidfVectorizer(stop_words='english')
            try:
                tfidf_matrix = vectorizer.fit_transform(documents)
                query_vec = vectorizer.transform([query])
                similarities = (tfidf_matrix * query_vec.T).toarray().flatten()
            except ValueError:
                similarities = np.zeros(len(documents))
            scored = []
            for i, row in enumerate(rows):
                score = 0.7 * similarities[i] + 0.3 * row[2]
                scored.append({"content": row[1], "score": score})
            scored.sort(key=lambda x: x["score"], reverse=True)
            return scored[:top_k]

    def summarize_and_store(self, conversation_text):
        try:
            summary = self.api.call_with_prompt(
                f"请用一句话总结以下对话的关键信息：\n{conversation_text}",
                temperature=0.3, max_tokens=100
            )
            self.add_memory("conversation_summary", summary, importance=0.6)
        except Exception as e:
            print(f"记忆摘要失败：{e}")

    def _enforce_limit(self):
        with self.lock:
            cur = self.conn.execute("SELECT COUNT(*) FROM permanent_memory")
            count = cur.fetchone()[0]
            if count > self.max_entries:
                delete_count = count - self.max_entries
                self.conn.execute(
                    "DELETE FROM permanent_memory WHERE id IN (SELECT id FROM permanent_memory ORDER BY importance_score ASC, timestamp ASC LIMIT ?)",
                    (delete_count,))
                self.conn.commit()
'''

# ═══════════════════════════════════════
# 3. 纯净版 host_executor.py
# ═══════════════════════════════════════
host_executor = r'''# core/host_executor.py —— 纯净版
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

# ═══════════════════════════════════════
# 4. 纯净版 sandbox.py
# ═══════════════════════════════════════
sandbox = r'''# core/sandbox.py —— 纯净版
import multiprocessing
import sys
import os
import time
import traceback
import math
from io import StringIO
import psutil

SAFE_BUILTINS = {
    'print': print,
    'int': int, 'float': float, 'str': str, 'bool': bool,
    'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
    'range': range, 'len': len, 'min': min, 'max': max,
    'abs': abs, 'round': round, 'sorted': sorted,
    'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
    'type': type, 'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
    'True': True, 'False': False, 'None': None,
    'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
    'KeyError': KeyError, 'IndexError': IndexError,
    'math': math
}

def free_fall(t, g=9.8):
    return 0.5 * g * t ** 2

def collision_detect(x1, y1, r1, x2, y2, r2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 <= (r1 + r2) ** 2

SAFE_BUILTINS['free_fall'] = free_fall
SAFE_BUILTINS['collision_detect'] = collision_detect

class Sandbox:
    def __init__(self, memory_limit=256):
        self.memory_limit = memory_limit

    def run(self, code: str, timeout=5, trace=False) -> dict:
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=_sandbox_exec, args=(code, timeout, trace, self.memory_limit, result_queue))
        p.start()
        p.join(timeout + 1)
        if p.is_alive():
            p.terminate()
            p.join()
            return {"success": False, "output": "", "error": "执行超时", "timeout": True, "trace_data": None}
        if not result_queue.empty():
            return result_queue.get()
        return {"success": False, "output": "", "error": "子进程无返回", "timeout": False, "trace_data": None}

def _sandbox_exec(code, timeout, trace, mem_limit_mb, queue):
    stop_monitor = False
    def memory_monitor():
        process = psutil.Process(os.getpid())
        limit_bytes = mem_limit_mb * 1024 * 1024
        while not stop_monitor:
            try:
                mem = process.memory_info().rss
                if mem > limit_bytes:
                    os._exit(1)
            except:
                pass
            time.sleep(0.1)
    import threading
    monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
    monitor_thread.start()
    old_stdout = sys.stdout
    sys.stdout = output_capture = StringIO()
    trace_data = []
    start_time = time.time()
    try:
        exec_globals = {'__builtins__': SAFE_BUILTINS}
        if trace:
            def trace_func(frame, event, arg):
                if event == 'call':
                    trace_data.append({'event': 'call', 'function': frame.f_code.co_name, 'lineno': frame.f_lineno, 'time': time.time()-start_time})
                elif event == 'line':
                    local_vars = {k: str(v) for k, v in frame.f_locals.items() if not k.startswith('__')}
                    trace_data.append({'event': 'line', 'lineno': frame.f_lineno, 'locals': local_vars, 'time': time.time()-start_time})
                elif event == 'return':
                    trace_data.append({'event': 'return', 'function': frame.f_code.co_name, 'value': str(arg), 'time': time.time()-start_time})
                return trace_func
            sys.settrace(trace_func)
        exec(code, exec_globals)
        output = output_capture.getvalue()
        success = True
        error = None
    except Exception as e:
        output = output_capture.getvalue()
        success = False
        error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
        stop_monitor = True
        monitor_thread.join(timeout=1)
    queue.put({"success": success, "output": output, "error": error, "timeout": False, "trace_data": trace_data if trace else None})
'''

# 应用替换
safe_write("intelligence/local_llm.py", local_llm)
safe_write("intelligence/memory.py", memory)
safe_write("core/host_executor.py", host_executor)
safe_write("core/sandbox.py", sandbox)

print("\n🎉 核心模块已全部替换为纯净版。请重启 LightAgent：python main.py")
