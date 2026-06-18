# intelligence/local_adapter.py
import os
from intelligence.local_llm import get_brain

class LocalAPI:
    def __init__(self, logger=None, knowledge_base=None):
        self.brain = get_brain()
        self.logger = logger
        # 保存模型名
        self._model_name = os.path.basename(self.brain.model_path) if hasattr(self.brain, 'model_path') else "本地模型"

    @property
    def model_name(self):
        return self._model_name

    def chat(self, messages, temperature=0.7, max_tokens=200):
        msgs = self._add_system(messages)
        return self.brain.chat(msgs, temperature, max_tokens)

    def call_with_prompt(self, prompt, temperature=0.7, max_tokens=200):
        return self.chat([{"role":"user","content":prompt}], temperature, max_tokens)

    def _add_system(self, messages):
        if not any(m["role"]=="system" for m in messages):
            sys_msg = {"role":"system","content":"你是张瑶瑶，17岁二次元少女，称呼用户为主人/前辈，用中文回答，萌系语气。"}
            return [sys_msg] + messages
        return messages
