# heartbeat_service.py —— 纯 Python 心跳管理器
import threading, time, json, yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

heartbeat_status = {}
_lock = threading.Lock()
TIMEOUT = 15

def load_api_key():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("api_key", "")
    return ""

def save_api_key(key):
    cfg = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    cfg["api_key"] = key
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True)

def ping(component_name):
    with _lock:
        heartbeat_status[component_name] = {
            'last_heartbeat': time.time(),
            'status': 'alive'
        }

def get_status():
    with _lock:
        return dict(heartbeat_status)

def monitor_loop():
    while True:
        time.sleep(TIMEOUT)
        with _lock:
            now = time.time()
            for name, info in list(heartbeat_status.items()):
                if now - info['last_heartbeat'] > TIMEOUT:
                    info['status'] = 'dead'

threading.Thread(target=monitor_loop, daemon=True).start()
