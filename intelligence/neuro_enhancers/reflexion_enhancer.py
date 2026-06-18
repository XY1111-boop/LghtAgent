
from .base_enhancer import BaseEnhancer

class REFLEXIONEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        # 在消息末尾追加反思提示
        last_user = None
        for m in reversed(messages):
            if m["role"] == "user":
                last_user = m
                break
        if last_user:
            last_user["content"] += "\n\n请你在回答完毕后，再花30个字简要检查一下你自己的答案是否正确。"
        return messages, params
