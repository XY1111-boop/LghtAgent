# intelligence/neuro_enhancers/cot_enhancer.py
from .base_enhancer import BaseEnhancer

class CoTEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        template = self.config.get("template", "请逐步思考并回答以下问题：\n{user_message}")
        for msg in reversed(messages):
            if msg["role"] == "user":
                msg["content"] = template.format(user_message=msg["content"])
                break
        return messages, params
