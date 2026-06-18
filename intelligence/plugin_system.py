# intelligence/plugin_system.py —— 插件系统
import importlib, os, json
from pathlib import Path

class PluginManager:
    def __init__(self, plugin_dir="plugins"):
        self.plugin_dir = Path(__file__).resolve().parent.parent / plugin_dir
        self.plugins = {}
        self._load_plugins()

    def _load_plugins(self):
        if not self.plugin_dir.exists():
            return
        for py_file in self.plugin_dir.glob("*.py"):
            if py_file.name.startswith("_"): continue
            name = py_file.stem
            try:
                spec = importlib.util.spec_from_file_location(f"plugin_{name}", str(py_file))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "run"):
                    self.plugins[name] = module.run
                    print(f"✅ 加载插件: {name}")
            except Exception as e:
                print(f"❌ 插件 {name} 加载失败: {e}")

    def execute(self, plugin_name, *args, **kwargs):
        if plugin_name in self.plugins:
            return self.plugins[plugin_name](*args, **kwargs)
        else:
            return f"插件 {plugin_name} 未找到"
