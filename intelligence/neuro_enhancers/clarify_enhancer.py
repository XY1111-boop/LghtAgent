
from .base_enhancer import BaseEnhancer

class CLARIFYEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        # 简单规则：如果用户消息过短或包含模糊词汇，要求澄清
        vague_words = ["那个", "这个", "它", "搞一下", "弄弄", "帮忙", "处理一下"]
        if any(w in user_text for w in vague_words) or len(user_text) < 5:
            for m in messages:
                if m["role"] == "system":
                    m["content"] += "\n如果用户指令模糊，请先提出1-2个澄清问题，不要直接操作。"
                    break
        return messages, params
