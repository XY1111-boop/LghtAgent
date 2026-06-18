# intelligence/neuro_enhancers/rag_enhancer.py
from .base_enhancer import BaseEnhancer

class RAGEnhancer(BaseEnhancer):
    """将知识库相关内容注入到提示中"""
    def __init__(self, config, knowledge_base):
        super().__init__(config)
        self.kb = knowledge_base

    def enhance(self, messages, params):
        user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        if self.kb:
            try:
                docs = self.kb.search(user_text, top_k=self.config.get("top_k", 2))
                if docs:
                    context = "\n\n".join(docs)
                    for msg in messages:
                        if msg["role"] == "system":
                            msg["content"] += f"\n\n【参考知识】\n{context}"
                            break
                    else:
                        messages.insert(0, {"role": "system", "content": f"【参考知识】\n{context}"})
            except:
                pass
        return messages, params
