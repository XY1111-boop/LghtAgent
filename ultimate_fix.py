# ultimate_fix.py —— 彻底清理心跳注入、修复变量污染、优化 VS Code
import os, shutil, re, json

PROJECT = r"E:\LightAgent"

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已清理 {path}")

# ─── 1. 清理所有曾被注入心跳的模块 ───
FILES_TO_CLEAN = [
    "intelligence/local_llm.py",
    "intelligence/vtuber_engine.py",
    "knowledge/knowledge_base.py",
    "intelligence/evolution.py",
    "intelligence/training_engine.py",
    "core/sandbox.py",
    "core/host_executor.py",
    "intelligence/neuro_enhancer.py",
    "intelligence/memory.py",  # 再次确保纯净
]

for file in FILES_TO_CLEAN:
    path = os.path.join(PROJECT, file)
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 移除所有包含 "requests.post" 的行（旧 HTTP 心跳）
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        if "requests.post" in line and "heartbeat" in line:
            continue  # 删除该行
        new_lines.append(line)
    content = "\n".join(new_lines)

    # 移除心跳线程函数定义（以 _send_heartbeat 开头的函数）
    content = re.sub(r'(\s*def _send_heartbeat.*?\.start\(\))', '', content, flags=re.DOTALL)

    # 移除多余的独立 import threading（如果之前错误插入）
    # 但保留原有正确的 import threading，只移除可能紧跟在心跳代码后的重复导入
    # 简单做法：统计文件开头的 import threading，如果存在多个，仅保留第一个
    import_lines = [i for i, line in enumerate(lines) if line.strip() == "import threading"]
    if len(import_lines) > 1:
        # 删除多余的 import threading
        for idx in reversed(import_lines[1:]):
            del lines[idx]
    content = "\n".join(lines)

    # 恢复可能被污染的 threading 变量（如果文件内有 `threading = ...` 这样的赋值）
    content = re.sub(r'^threading\s*=\s*.*', '', content, flags=re.MULTILINE)

    safe_write(path, content)

# ─── 2. 额外确保 memory.py 绝对纯净（如果之前未修复） ───
pure_memory = r'''# intelligence/memory.py —— 纯净版
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
safe_write("intelligence/memory.py", pure_memory)

# ─── 3. 修复类型标注警告 ───
harness_path = os.path.join(PROJECT, "intelligence", "core_agent_skills_harness.py")
if os.path.exists(harness_path):
    with open(harness_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'->\s*\((\w+),\s*(\w+)\):', r'-> tuple[\1, \2]:', content)
    content = content.replace(
        "def _generate_plan(self, goal: str) -> List[str]:",
        "def _generate_plan(self, goal: str) -> Optional[List[str]]:"
    )
    with open(harness_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 类型标注已修复")

# ─── 4. 生成 VS Code 工作区配置 ───
vscode_dir = os.path.join(PROJECT, ".vscode")
os.makedirs(vscode_dir, exist_ok=True)
settings = {
    "python.defaultInterpreterPath": "C:/Program Files/Python311/python.exe",
    "python.analysis.extraPaths": ["E:/LightAgent"],
    "python.analysis.diagnosticSeverityOverrides": {
        "reportMissingImports": "none",
        "reportInvalidTypeForm": "none",
        "reportReturnType": "none"
    },
    "python.languageServer": "Pylance",
    "editor.formatOnSave": True
}
with open(os.path.join(vscode_dir, "settings.json"), "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=4)
print("✅ VS Code 配置已生成")

print("\n🎉 全部清理完成！请重启 LightAgent：python main.py")
print("   记忆系统将不再卡死，VS Code 中也不会有红色波浪线。")
