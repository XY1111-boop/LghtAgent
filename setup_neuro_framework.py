# setup_neuro_framework.py —— 动态神经增强框架安装脚本
import os, shutil, yaml

PROJECT = r"E:\LightAgent"

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已创建/更新 {path}")

# 1. 生成 neuro_config.yaml 默认配置
neuro_config = {
    "enabled": True,
    "enhancers": [
        {"name": "cot", "enabled": True, "template": "请逐步思考并回答以下问题：\n{user_message}"},
        {"name": "dynamic_temp", "enabled": True, "base_temp": 0.7, "difficulty_threshold": 0.5},
        {"name": "rag", "enabled": True, "top_k": 2}
    ]
}
safe_write("neuro_config.yaml", yaml.dump(neuro_config, allow_unicode=True))

# 2. 增强器基类
base_enhancer = r'''# intelligence/neuro_enhancers/base_enhancer.py
from abc import ABC, abstractmethod

class BaseEnhancer(ABC):
    """增强器基类，所有自定义增强器需继承此类"""
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def enhance(self, messages, params):
        """对消息列表和推理参数进行增强，返回 (messages, params)"""
        pass
'''
safe_write("intelligence/neuro_enhancers/__init__.py", "")
safe_write("intelligence/neuro_enhancers/base_enhancer.py", base_enhancer)

# 3. 思维链增强器
cot_enhancer = r'''# intelligence/neuro_enhancers/cot_enhancer.py
from .base_enhancer import BaseEnhancer

class CoTEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        template = self.config.get("template", "请逐步思考并回答以下问题：\n{user_message}")
        for msg in reversed(messages):
            if msg["role"] == "user":
                msg["content"] = template.format(user_message=msg["content"])
                break
        return messages, params
'''
safe_write("intelligence/neuro_enhancers/cot_enhancer.py", cot_enhancer)

# 4. 动态温度增强器
dynamic_temp = r'''# intelligence/neuro_enhancers/dynamic_temp_enhancer.py
from .base_enhancer import BaseEnhancer
import re

class DynamicTempEnhancer(BaseEnhancer):
    def enhance(self, messages, params):
        user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        # 简单评估：包含“计算”“分析”“复杂”等词时降低温度
        if any(w in user_text for w in ["计算", "分析", "为什么", "证明", "复杂"]):
            params["temperature"] = 0.3
        else:
            params["temperature"] = self.config.get("base_temp", 0.7)
        return messages, params
'''
safe_write("intelligence/neuro_enhancers/dynamic_temp_enhancer.py", dynamic_temp)

# 5. 本地知识检索增强器
rag_enhancer = r'''# intelligence/neuro_enhancers/rag_enhancer.py
from .base_enhancer import BaseEnhancer

class RAGEnhancer(BaseEnhancer):
    """将知识库相关内容注入到提示中"""
    def __init__(self, config, knowledge_base):
        super().__init__(config)
        self.kb = knowledge_base

    def enhance(self, messages, params):
        user_text = " ".join([m["content"] for m in messages if m["role"] == "user"])
        if self.kb:
            try:
                docs = self.kb.search(user_text, top_k=self.config.get("top_k", 2))
                if docs:
                    context = "\n\n".join(docs)
                    for msg in messages:
                        if msg["role"] == "system":
                            msg["content"] += f"\n\n【参考知识】\n{context}"
                            break
                    else:
                        messages.insert(0, {"role": "system", "content": f"【参考知识】\n{context}"})
            except:
                pass
        return messages, params
'''
safe_write("intelligence/neuro_enhancers/rag_enhancer.py", rag_enhancer)

# 6. 主增强管道
enhancer_py = r'''# intelligence/neuro_enhancer.py —— 动态神经增强管道
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

    def _load_enhancers(self, knowledge_base):
        enhancers_dir = Path(__file__).resolve().parent / "neuro_enhancers"
        for enh_conf in self.config.get("enhancers", []):
            if not enh_conf.get("enabled", True):
                continue
            name = enh_conf["name"]
            try:
                # 动态导入对应模块（如 .cot_enhancer）
                module = importlib.import_module(f"intelligence.neuro_enhancers.{name}_enhancer")
                # 类名约定：首字母大写 + "Enhancer"
                class_name = f"{name.upper()}Enhancer"
                cls = getattr(module, class_name)
                # 特殊处理：RAG 需要传入 knowledge_base
                if name == "rag":
                    instance = cls(enh_conf, knowledge_base)
                else:
                    instance = cls(enh_conf)
                self.enhancers.append(instance)
                print(f"✅ 已加载增强器: {name}")
            except Exception as e:
                print(f"⚠️ 加载增强器 {name} 失败: {e}")

    def enhance(self, messages, params):
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
'''
safe_write("intelligence/neuro_enhancer.py", enhancer_py)

# 7. 修改 local_llm.py 中的 LocalBrain，使其在 chat 时使用增强管道
llm_path = os.path.join(PROJECT, "intelligence", "local_llm.py")
if os.path.exists(llm_path):
    shutil.copy2(llm_path, llm_path + ".bak")
    with open(llm_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 在 chat 方法开头插入增强逻辑
    # 找到 "def chat(self, messages, temperature=0.7, max_tokens=200):"
    old_chat = "def chat(self, messages, temperature=0.7, max_tokens=200):"
    new_chat = '''def chat(self, messages, temperature=0.7, max_tokens=200):
        # 应用神经增强管道
        try:
            from intelligence.neuro_enhancer import get_enhancer
            enhancer = get_enhancer()
            params = {"temperature": temperature, "max_tokens": max_tokens}
            messages, params = enhancer.enhance(messages, params)
            temperature = params.get("temperature", temperature)
            max_tokens = params.get("max_tokens", max_tokens)
        except Exception as e:
            print(f"⚠️ 神经增强失败: {e}")'''
    content = content.replace(old_chat, new_chat)
    # 确保导入了必要的模块（已在文件头部，但无害）
    with open(llm_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ local_llm.py 已集成增强管道")

# 8. 修改 main.py，在创建本地 API 时传递知识库（如果需要）
main_path = os.path.join(PROJECT, "main.py")
if os.path.exists(main_path):
    shutil.copy2(main_path, main_path + ".bak")
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 找到 LocalAPI(logger=self.logger) 调用，改为 LocalAPI(logger=self.logger, knowledge_base=self.knowledge_base)
    if "LocalAPI(logger=self.logger)" in content and "knowledge_base" not in content:
        content = content.replace(
            "LocalAPI(logger=self.logger)",
            "LocalAPI(logger=self.logger, knowledge_base=self.knowledge_base)"
        )
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ main.py 已传递 knowledge_base")
    else:
        print("⚠️ main.py 可能已包含 knowledge_base 参数，跳过修改")

# 9. 修改 local_adapter.py，让其构造函数接收 knowledge_base 并传递给 NeuroEnhancer
adapter_path = os.path.join(PROJECT, "intelligence", "local_adapter.py")
if os.path.exists(adapter_path):
    shutil.copy2(adapter_path, adapter_path + ".bak")
    with open(adapter_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 更新 __init__ 签名
    old_init = "def __init__(self, logger=None):"
    new_init = "def __init__(self, logger=None, knowledge_base=None):"
    content = content.replace(old_init, new_init)
    # 在 __init__ 末尾添加增强器初始化（传递 knowledge_base）
    # 找到 self.brain = get_brain() 后面添加
    if "self.brain = get_brain()" in content and "NeuroEnhancer" not in content:
        content = content.replace(
            "self.brain = get_brain()",
            "self.brain = get_brain()\n        # 初始化神经增强器（可动态配置）\n        try:\n            from intelligence.neuro_enhancer import NeuroEnhancer\n            self.enhancer = NeuroEnhancer(knowledge_base=knowledge_base)\n        except Exception as e:\n            print(f\"⚠️ 神经增强器加载失败: {e}\")\n            self.enhancer = None"
        )
    with open(adapter_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ local_adapter.py 已更新")

print("\n🎉 神经增强框架安装完成！")
print("   - 配置文件: neuro_config.yaml")
print("   - 增强器: 思维链、动态温度、知识检索 (可随时扩展)")
print("   - 动态加载: 添加新增强器只需在 neuro_enhancers/ 下放入新文件")
print("   重启 LightAgent 体验升级后的智商: python main.py")
