# intelligence/neuro_enhancers/experience_enhancer.py
from .base_enhancer import BaseEnhancer
from intelligence.experience_manager import ExperienceManager

class EXPERIENCEEnhancer(BaseEnhancer):
    def __init__(self, config):
        super().__init__(config)
        self.manager = ExperienceManager()

    def enhance(self, messages, params):
        user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        # 模糊搜索经验库
        matches = self.manager.search_similar(user_text, threshold=0.4)
        if matches:
            # 取最佳匹配
            best = matches[0]
            context = f"【历史成功经验】\n指令：{best['instruction']}\n代码：{best['code']}"
            for m in messages:
                if m["role"] == "system":
                    m["content"] += f"\n\n{context}"
                    break
            else:
                messages.insert(0, {"role": "system", "content": context})
            # 更新使用统计
            self.manager.record_success(best['instruction'])
        return messages, params
