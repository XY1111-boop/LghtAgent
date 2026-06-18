# intelligence/local_llm.py —— 纯净版
import threading
from pathlib import Path
from llama_cpp import Llama

MODEL_PATH = Path(__file__).resolve().parent.parent / "models"

def find_model():
    models = list(MODEL_PATH.glob("*.gguf"))
    if models:
        return str(models[0])
    raise FileNotFoundError("未找到任何 .gguf 模型文件")

class LocalBrain:
    def __init__(self, model_path=None, n_ctx=2048):
        path = model_path or find_model()
        self.model_path = str(path)
        self.llm = Llama(model_path=self.model_path, n_ctx=n_ctx, n_threads=4,
                         n_gpu_layers=16, verbose=False)
        self.lock = threading.Lock()

    def chat(self, messages, temperature=0.7, max_tokens=200):
        with self.lock:
            prompt = self._format(messages)
            out = self.llm(prompt, max_tokens=max_tokens, temperature=temperature,
                           top_p=0.9, repeat_penalty=1.1,
                           stop=["<|im_end|>", "<|user|>"], echo=False)
            return out["choices"][0]["text"].strip()

    def _format(self, messages):
        prompt = ""
        for m in messages:
            prompt += f"<|im_start|>{m['role']}\\n{m['content']}<|im_end|>\\n"
        prompt += "<|im_start|>assistant\\n"
        return prompt

_brain = None
def get_brain():
    global _brain
    if _brain is None:
        _brain = LocalBrain()
    return _brain
