
from .base_enhancer import BaseEnhancer

class TOTEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        # 将用户问题改为要求先列出多种思路
        for m in reversed(messages):
            if m["role"] == "user":
                m["content"] = "问题：" + m["content"] + "\n请先想出至少两种不同的解决方法，然后选择最佳方案回答。"
                break
        params["max_tokens"] = min(params.get("max_tokens", 200) + 100, 500)
        return messages, params
