# intelligence/memory.py —— 全新动态记忆系统 v2
import threading, sqlite3, time, logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger("MemoryV2")

class MemoryManager:
    def __init__(self, api, db_path="E:/LightAgent/Cache/memory.db", max_entries=10000):
        self.api = api
        self.db_path = db_path
        self.max_entries = max_entries
        self.lock = threading.RLock()  # 使用可重入锁，防止死锁
        self._init_db()
        logger.info("记忆系统初始化成功")

    def _init_db(self):
        """安全的数据库初始化，带重试机制"""
        for attempt in range(3):
            try:
                with self.lock:
                    conn = sqlite3.connect(self.db_path, check_same_thread=False)
                    conn.execute("""CREATE TABLE IF NOT EXISTS permanent_memory
                                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                     timestamp REAL,
                                     memory_type TEXT,
                                     content TEXT,
                                     importance_score REAL)""")
                    conn.commit()
                    conn.close()
                return
            except Exception as e:
                logger.warning(f"数据库初始化尝试 {attempt+1} 失败: {e}")
                time.sleep(0.5)
        raise RuntimeError("无法初始化记忆数据库")

    def _get_conn(self):
        """获取数据库连接（每次新建，避免跨线程问题）"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def add_memory(self, memory_type, content, importance=0.5):
        with self.lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "INSERT INTO permanent_memory (timestamp, memory_type, content, importance_score) VALUES (?,?,?,?)",
                    (time.time(), memory_type, content, importance))
                conn.commit()
            finally:
                conn.close()
        self._enforce_limit()

    def retrieve_relevant(self, query, top_k=5):
        with self.lock:
            conn = self._get_conn()
            try:
                cur = conn.execute("SELECT id, content, importance_score FROM permanent_memory")
                rows = cur.fetchall()
            finally:
                conn.close()

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
        if not self.api:
            return
        try:
            summary = self.api.call_with_prompt(
                f"请用一句话总结以下对话的关键信息：\n{conversation_text}",
                temperature=0.3, max_tokens=100
            )
            if summary:
                self.add_memory("conversation_summary", summary, importance=0.6)
        except Exception as e:
            logger.warning(f"记忆摘要失败：{e}")

    def _enforce_limit(self):
        with self.lock:
            conn = self._get_conn()
            try:
                cur = conn.execute("SELECT COUNT(*) FROM permanent_memory")
                count = cur.fetchone()[0]
                if count > self.max_entries:
                    delete_count = count - self.max_entries
                    conn.execute(
                        "DELETE FROM permanent_memory WHERE id IN (SELECT id FROM permanent_memory ORDER BY importance_score ASC, timestamp ASC LIMIT ?)",
                        (delete_count,))
                    conn.commit()
            finally:
                conn.close()
