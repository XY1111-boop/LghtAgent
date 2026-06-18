# intelligence/neuro_enhancers/dynamic_temp_enhancer.py
from .base_enhancer import BaseEnhancer
import re

class DYNAMICTEMPEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        # 简单评估：包含“计算”“分析”“复杂”等词时降低温度
        if any(w in user_text for w in ["计算", "分析", "为什么", "证明", "复杂"]):
            params["temperature"] = 0.3
        else:
            params["temperature"] = self.config.get("base_temp", 0.7)
        return messages, params
