# intelligence/neuro_enhancer.py —— 动态神经增强管道
import importlib, yaml, os
from pathlib import Path
from intelligence.neuro_enhancers.base_enhancer import BaseEnhancer

class NeuroEnhancer:
    def __init__(self, config_path=None, knowledge_base=None):
        if config_path is None:
            config_path = Path(__file__).resolve().parent.parent / "neuro_config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self.enhancers = []
        self._load_enhancers(knowledge_base)
# 自动心跳上报
        import threading, time

    def _load_enhancers(self, knowledge_base):
        enhancers_dir = Path(__file__).resolve().parent / "neuro_enhancers"
        for enh_conf in self.config.get("enhancers", []):
            if not enh_conf.get("enabled", True):
                continue
            name = enh_conf["name"]
            try:
                # 动态导入模块
                module_name = f"intelligence.neuro_enhancers.{name}_enhancer"
                module = importlib.import_module(module_name)
                # 自动查找继承自 BaseEnhancer 的类（排除 BaseEnhancer 本身）
                enh_class = None
                for attr in dir(module):
                    cls = getattr(module, attr)
                    if (isinstance(cls, type) and 
                        issubclass(cls, BaseEnhancer) and 
                        cls is not BaseEnhancer):
                        enh_class = cls
                        break
                if enh_class is None:
                    print(f"⚠️ 模块 {name}_enhancer 中未找到有效的增强器类，跳过")
                    continue
                # 特殊处理：RAG 需要传入 knowledge_base
                if name == "rag":
                    instance = enh_class(enh_conf, knowledge_base)
                else:
                    instance = enh_class(enh_conf)
                self.enhancers.append(instance)
                print(f"✅ 已加载增强器: {name} ({enh_class.__name__})")
            except Exception as e:
                print(f"⚠️ 加载增强器 {name} 失败: {e}")
    def enhance(self, messages, params):
        import signal
        def timeout_handler(signum, frame):
            raise TimeoutError("增强器执行超时")
        # 不实际使用 signal（Windows 限制），改为简单线程超时
        return self._enhance_with_timeout(messages, params)
    def _enhance_with_timeout(self, messages, params):
        import threading
        result = [None]
        def worker():
            try:
                for enh in self.enhancers:
                    messages, params = enh.enhance(messages, params)
                result[0] = (messages, params)
            except Exception as e:
                result[0] = e
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join(timeout=10)  # 每个增强器最多10秒
        if t.is_alive():
            print("⚠️ 增强器执行超时，跳过")
            return messages, params
        if isinstance(result[0], Exception):
            raise result[0]
        return result[0]
        """依次执行所有增强器，返回最终的 (messages, params)"""
        for enh in self.enhancers:
            try:
                messages, params = enh.enhance(messages, params)
            except Exception as e:
                print(f"⚠️ 增强器 {enh.__class__.__name__} 执行异常: {e}")
        return messages, params

# 全局单例
_enhancer = None

def get_enhancer(knowledge_base=None):
    global _enhancer
    if _enhancer is None:
        _enhancer = NeuroEnhancer(knowledge_base=knowledge_base)
    return _enhancer
