# vector_db.py —— 基于 FAISS 的本地向量索引
import faiss, numpy as np, os, json
from sentence_transformers import SentenceTransformer

class LightVectorDB:
    def __init__(self, dim=384):
        self.dim = dim
        self.index = faiss.IndexFlatL2(dim)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')  # 可替换为本地更小的模型
        self.documents = []  # 保存原始文本

    def add_documents(self, docs: list[str]):
        vectors = self.encoder.encode(docs)
        self.index.add(np.array(vectors).astype('float32'))
        self.documents.extend(docs)

    def search(self, query: str, k=3):
        q_vec = self.encoder.encode([query]).astype('float32')
        distances, indices = self.index.search(q_vec, k)
        results = []
        for i in indices[0]:
            if i < len(self.documents):
                results.append(self.documents[i])
        return results
