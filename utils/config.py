# utils/config.py —— 修复版
from pathlib import Path
import os
import sys
import platform
import shutil
import yaml
import psutil
import GPUtil
import socket
import getpass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

def setup_environment():
    if not CONFIG_PATH.exists() or not (PROJECT_ROOT / "Logs").exists():
        print("首次运行，正在初始化...")
        _first_run_wizard()
    return ConfigManager(str(CONFIG_PATH))

def _first_run_wizard():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in ["core", "intelligence", "knowledge", "ui", "utils", "plugins",
                "Knowledge/raw", "Knowledge/digested", "Knowledge/neurons",
                "Logs", "Cache", "EvolutionSnapshots"]:
        (PROJECT_ROOT / sub).mkdir(parents=True, exist_ok=True)

    hw_info = _scan_hardware()
    default_config = {
        "hardware": hw_info,
        "api_key": "",
        "model": "deepseek-chat",
        "serper_api_key": "",
        "evolution_enabled": False,
        "evolution_aggressiveness": 0.5,
        "creativity_temperature": 0.7,
        "brainstorm_temperature": 1.0,
        "log_retention_days": 30,
        "knowledge_raw_dir": str(PROJECT_ROOT / "Knowledge/raw"),
        "max_memory_entries": 10000,
        "cache_size": 500,
        "sandbox_memory_limit_mb": 256,
        "host_executor_allowed_dir": str(PROJECT_ROOT / "Knowledge/raw"),
        "theme": "light",
    }
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True)

    # 桌面快捷方式创建（仅 Windows 尝试）
    if os.name == 'nt':
        try:
            import winshell
            from win32com.client import Dispatch
            desktop = Path(winshell.desktop())
            shortcut_path = desktop / "LightAgent.lnk"
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{PROJECT_ROOT / "main.py"}"'
            shortcut.WorkingDirectory = str(PROJECT_ROOT)
            shortcut.save()
        except Exception:
            pass

def _scan_hardware():
    info = {
        "os": platform.platform(),
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "cpu": platform.processor(),
        "cpu_cores_physical": psutil.cpu_count(logical=False),
        "cpu_cores_logical": psutil.cpu_count(logical=True),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "disk_total_gb": round(psutil.disk_usage('C:/').total / (1024**3), 2),
        "gpu": []
    }
    try:
        gpus = GPUtil.getGPUs()
        for gpu in gpus:
            info["gpu"].append({
                "name": gpu.name,
                "driver": gpu.driver,
                "memory_total_mb": gpu.memoryTotal,
                "memory_free_mb": gpu.memoryFree,
            })
    except Exception:
        info["gpu"].append({"name": "Unknown"})
    return info

class ConfigManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.data = yaml.safe_load(f) or {}

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def save(self):
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.data, f, allow_unicode=True)
