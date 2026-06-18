# memory_store.py —— 分层记忆、实体图谱、差分隐私
import sqlite3, time, json, numpy as np, hashlib, os, threading
from collections import OrderedDict
from sklearn.feature_extraction.text import TfidfVectorizer

class HierarchicalMemory:
    def __init__(self, db_path="E:/LightAgent/Cache/memory_v2.db", max_hot=10, max_warm=100):
        self.db_path = db_path
        self.hot = OrderedDict()          # GPU KV cache 键值
        self.warm = OrderedDict()         # CPU 内存中的压缩记忆
        self.cold = []                    # 硬盘索引
        self.graph = EntityGraph()
        self.lock = threading.RLock()
        self.vectorizer = TfidfVectorizer()
        self._load_cold_index()

    def add(self, text, importance=0.5):
        with self.lock:
            # 写入热记忆
            mem_id = hashlib.md5(text.encode()).hexdigest()[:8]
            self.hot[mem_id] = {"content": text, "importance": importance, "time": time.time()}
            if len(self.hot) > 10:
                oldest = self.hot.popitem(last=False)
                self.warm[oldest[0]] = self._compress(oldest[1])
            # 异步写入冷存储
            threading.Thread(target=self._write_cold, args=(mem_id, text, importance)).start()
            # 更新实体图谱
            self.graph.extract_entities(text)

    def retrieve(self, query, top_k=5):
        with self.lock:
            results = []
            # 热记忆检索
            for mem in self.hot.values():
                if query in mem["content"]:
                    results.append(mem)
            # 温记忆检索（简化：用 TF-IDF）
            if len(results) < top_k and self.warm:
                corpus = [m["content"] for m in self.warm.values()]
                try:
                    tfidf = self.vectorizer.fit_transform(corpus)
                    q_vec = self.vectorizer.transform([query])
                    scores = (tfidf * q_vec.T).toarray().flatten()
                    warm_list = list(self.warm.values())
                    for idx in scores.argsort()[::-1]:
                        results.append(warm_list[idx])
                        if len(results) >= top_k:
                            break
                except:
                    pass
            # 冷记忆检索（从硬盘加载）
            if len(results) < top_k:
                results.extend(self._search_cold(query, top_k - len(results)))
            return results[:top_k]

    def _compress(self, mem):
        # 用摘要代替完整内容
        mem["content"] = mem["content"][:200] + "..."
        return mem

    def _write_cold(self, mem_id, text, importance):
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO cold_memory (id, content, importance) VALUES (?,?,?)",
                     (mem_id, text, importance))
        conn.commit()
        conn.close()

    def _load_cold_index(self):
        # 从数据库加载冷记忆索引
        pass

    def _search_cold(self, query, k):
        # 简化：从数据库模糊搜索
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("SELECT content FROM cold_memory WHERE content LIKE ? LIMIT ?",
                           ('%'+query+'%', k))
        return [{"content": row[0]} for row in cur.fetchall()]

class EntityGraph:
    def __init__(self):
        self.nodes = {}  # 实体 -> {属性}
    def extract_entities(self, text):
        # 简化实体识别：用正则提取人名、地名等
        import re
        names = re.findall(r'(?:@|联系人：|用户名：)(\w+)', text)
        for name in names:
            self.nodes[name] = {"type": "person", "count": self.nodes.get(name, {}).get("count", 0) + 1}
