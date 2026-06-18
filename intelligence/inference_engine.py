# inference_engine.py —— 推理引擎（替换 local_llm.py）
import threading, time, asyncio
from llama_cpp import Llama
from intelligence.model_modules import ModelManager
from intelligence.dynamic_dispatcher import Dispatcher

class InferenceEngine:
    def __init__(self, models_dir):
        self.mm = ModelManager(models_dir)
        self.model = self.mm.load_optimal_model()
        self.dispatcher = Dispatcher(self.mm)
        self.dispatcher.start_monitor()
        self.lock = threading.Lock()
        self.speculative_model = None  # 投机解码小模型（0.5B）

    def chat(self, messages, temperature=0.7, max_tokens=200):
        with self.lock:
            return self._generate(messages, temperature, max_tokens)

    def _generate(self, messages, temp, max_tok):
        prompt = self._format_chatml(messages)
        output = self.model(
            prompt,
            max_tokens=max_tok,
            temperature=temp,
            top_p=0.9,
            repeat_penalty=1.1,
            stop=["<|im_end|>", "<|user|>"],
            echo=False
        )
        return output["choices"][0]["text"].strip()

    def _format_chatml(self, messages):
        prompt = ""
        for m in messages:
            prompt += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
        prompt += "<|im_start|>assistant\n"
        return prompt

    def generate_with_tools(self, messages, tools, temperature=0.2):
        """Function calling 模式：要求模型输出 JSON 工具调用"""
        sys_msg = {"role": "system", "content": f"可用工具：{tools}\n请返回JSON格式：{{\"tool\": \"...\", \"params\": {{...}}}}"}
        msgs = [sys_msg] + messages
        return self.chat(msgs, temperature=temperature)
