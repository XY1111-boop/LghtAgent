# intelligence/neuro_enhancers/base_enhancer.py
from abc import ABC, abstractmethod

class BaseEnhancer(ABC):
    """增强器基类，所有自定义增强器需继承此类"""
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def enhance(self, messages, params):
        """对消息列表和推理参数进行增强，返回 (messages, params)"""
        pass
