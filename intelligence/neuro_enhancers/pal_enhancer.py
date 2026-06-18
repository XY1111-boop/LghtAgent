
from .base_enhancer import BaseEnhancer
import re

class PALEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        # 检测是否涉及数学计算或逻辑推理，引导使用代码
        user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        if re.search(r'计算|算|加|减|乘|除|阶乘|平方|多少|等于|逻辑|排序', user_text):
            for m in messages:
                if m["role"] == "system":
                    m["content"] += "\n如果问题涉及计算，请生成 Python 代码并用 run_python 工具执行，然后基于结果回答。"
                    break
        return messages, params
