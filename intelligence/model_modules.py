# model_modules.py —— 低资源模型加载与量化支持
import os, sys, ctypes
from pathlib import Path
from typing import Optional
import llama_cpp

class ModelManager:
    """根据硬件自动选择最优模型与量化配置"""
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.vram_bytes = self._get_vram()
        self.ram_bytes = self._get_ram()
        self.model = None

    def _get_vram(self):
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                return gpus[0].memoryTotal * 1024 * 1024
        except:
            pass
        return 0

    def _get_ram(self):
        import psutil
        return psutil.virtual_memory().total

    def load_optimal_model(self) -> llama_cpp.Llama:
        # 根据显存选择模型大小
        if self.vram_bytes >= 2 * 1024 * 1024 * 1024:  # 2GB 显存
            model_file = "qwen2.5-1.5b-instruct-q4_k_m.gguf"
            n_gpu_layers = 24
            n_batch = 512
        else:
            model_file = "qwen2.5-0.5b-instruct-q4_k_m.gguf"
            n_gpu_layers = 16
            n_batch = 256

        path = self.models_dir / model_file
        if not path.exists():
            raise FileNotFoundError(f"模型文件 {model_file} 不存在")

        self.model = llama_cpp.Llama(
            model_path=str(path),
            n_gpu_layers=n_gpu_layers,
            n_batch=n_batch,
            n_ctx=8192,
            use_mlock=True,
            use_mmap=False,
            verbose=False
        )
        return self.model
