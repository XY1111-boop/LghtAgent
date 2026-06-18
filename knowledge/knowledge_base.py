# knowledge/knowledge_base.py —— 稳定版
import os, shutil, hashlib
from pathlib import Path
import chromadb
from chromadb.config import Settings
import numpy as np
from collections import Counter

def offline_embed(text):
    words = text.lower().split()
    common_words = set("the is of and a to in that it for on with as at from by".split())
    vec = Counter(w for w in words if w in common_words)
    np.random.seed(int(hashlib.md5(text.encode()).hexdigest()[:8], 16) % 2**32)
    v = np.random.randn(50)
    for w, c in vec.items():
        v[hash(w) % 50] += c
    norm = np.linalg.norm(v)
    return (v / norm).tolist() if norm > 0 else v.tolist()

class KnowledgeBase:
    def __init__(self, root_dir="E:/LightAgent/Knowledge"):
        self.root = Path(root_dir)
        self.raw = self.root / "raw"
        self.digested = self.root / "digested"
        self.raw.mkdir(parents=True, exist_ok=True)
        self.digested.mkdir(parents=True, exist_ok=True)
        self.chroma = chromadb.PersistentClient(
            path=str(self.root / "chroma_db"),
            settings=Settings(anonymized_telemetry=False))
        self.collection = self.chroma.get_or_create_collection(
            name="knowledge", embedding_function=None)
        print("✅ 知识库就绪")
# 自动心跳上报
        import threading, time

    def index_files(self):
        files = list(self.raw.glob("*"))
        print(f"🔍 索引 {len(files)} 个文件...")
        for f in files:
            if not f.is_file():
                continue
            try:
                from knowledge.file_processor import extract_text_from_file
                text = extract_text_from_file(str(f))
                if not text or "提取失败" in text:
                    continue
                chunks = [text[i:i+500] for i in range(0, len(text), 500)]
                for i, chunk in enumerate(chunks):
                    doc_id = f"{f.name}_chunk{i}"
                    if self.collection.get(ids=[doc_id])['ids']:
                        continue
                    emb = offline_embed(chunk)
                    self.collection.add(documents=[chunk], embeddings=[emb], ids=[doc_id])
                print(f"  ✅ {f.name} ({len(chunks)} 块)")
            except Exception as e:
                print(f"  ❌ {f.name}: {e}")
        print("🎉 索引完成")

    def search(self, query, top_k=3):
        try:
            emb = offline_embed(query)
            res = self.collection.query(query_embeddings=[emb], n_results=top_k)
            return res['documents'][0]
        except:
            return []

import numpy as np
from rank_bm25 import BM25Okapi
from collections import Counter

class HybridKnowledgeBase(KnowledgeBase):
    def __init__(self, root_dir="E:/LightAgent/Knowledge"):
        super().__init__(root_dir)
        self.bm25 = None
        self.corpus = []

    def build_bm25_index(self):
        self.corpus = [doc for docs in self.collection.get()['documents'] for doc in docs]
        if self.corpus:
            tokenized_corpus = [doc.split() for doc in self.corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)

    def hybrid_search(self, query, top_k=3):
        # 向量检索
        vec_results = self.search(query, top_k=top_k*2)
        # 关键词检索
        bm25_scores = []
        if self.bm25:
            tokenized_query = query.split()
            bm25_scores = self.bm25.get_scores(tokenized_query)
        # 融合（简单加权）
        combined = []
        for i, doc in enumerate(vec_results):
            score = 0.7 + 0.3 * (bm25_scores[i] if i < len(bm25_scores) else 0)
            combined.append((score, doc))
        combined.sort(reverse=True)
        return [doc for _, doc in combined[:top_k]]

    def start_auto_scan(self, interval=60):
        """每隔 interval 秒自动扫描 raw 目录并索引新文件"""
        import threading, time
        def scanner():
            while True:
                try:
                    self.index_files()
                except Exception as e:
                    print(f"自动扫描知识库出错: {e}")
                time.sleep(interval)
        threading.Thread(target=scanner, daemon=True).start()
