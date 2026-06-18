# core_upgrade.py —— LightAgent 核心能力升级与长期维护模块（修正版）
from pathlib import Path          # 必须放在最前面
import os, sys, shutil, json, time, hashlib, logging, subprocess
from datetime import datetime
from typing import Dict, Optional

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

LOG_DIR = PROJECT_ROOT / "Logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "core_upgrade.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("CoreUpgrade")

MIRRORS = [
    "https://hf-mirror.com",
    "https://hf.phiy.me",
    "https://huggingface-mirror.com",
    "https://huggingface.co"
]

MODEL_CATALOG = {
    "tiny": {
        "name": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size_gb": 0.5, "min_vram_gb": 1.0,
        "n_gpu_layers": 16, "context": 2048, "batch": 256,
        "repo": "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
    },
    "small": {
        "name": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "size_gb": 2.3, "min_vram_gb": 2.0,
        "n_gpu_layers": 24, "context": 2048, "batch": 512,
        "repo": "Qwen/Qwen2.5-1.5B-Instruct-GGUF"
    },
    "medium": {
        "name": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "size_gb": 3.5, "min_vram_gb": 4.0,
        "n_gpu_layers": 32, "context": 4096, "batch": 1024,
        "repo": "Qwen/Qwen2.5-3B-Instruct-GGUF"
    }
}

# ---------- 硬件扫描 ----------
def scan_hardware() -> Dict:
    info = {"cpu_cores": os.cpu_count(), "ram_total_gb": 0, "gpu_name": "None", "vram_gb": 0.0}
    try:
        import psutil
        info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
    except ImportError:
        logger.warning("psutil 未安装")
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            info["gpu_name"] = gpu.name
            info["vram_gb"] = gpu.memoryTotal / 1024.0
    except ImportError:
        logger.warning("GPUtil 未安装")
    except Exception as e:
        logger.warning(f"GPU 检测失败: {e}")
    return info

def recommend_model(hw: Dict) -> Dict:
    vram = hw["vram_gb"]
    if vram >= MODEL_CATALOG["medium"]["min_vram_gb"]:
        return MODEL_CATALOG["medium"]
    elif vram >= MODEL_CATALOG["small"]["min_vram_gb"]:
        return MODEL_CATALOG["small"]
    return MODEL_CATALOG["tiny"]

# ---------- 模型下载 ----------
def download_model(model_info: Dict, models_dir: Path) -> Path:
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / model_info["name"]
    if model_path.exists():
        logger.info(f"模型已存在: {model_info['name']}")
        return model_path

    url_path = f"{model_info['repo']}/resolve/main/{model_info['name']}"
    logger.info(f"开始下载 {model_info['name']} (约 {model_info['size_gb']}GB)")

    for mirror in MIRRORS:
        full_url = f"{mirror}/{url_path}"
        logger.info(f"尝试镜像: {mirror}")
        try:
            import requests
            headers = {"User-Agent": "Mozilla/5.0"}
            resume_pos = model_path.stat().st_size if model_path.exists() else 0
            if resume_pos:
                headers["Range"] = f"bytes={resume_pos}-"
            with requests.get(full_url, stream=True, timeout=120, headers=headers) as r:
                if r.status_code not in (200, 206):
                    continue
                total = int(r.headers.get('content-length', 0)) + resume_pos
                mode = 'ab' if resume_pos else 'wb'
                with open(model_path, mode) as f:
                    downloaded = resume_pos
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = min(100, int(downloaded / total * 100)) if total else 0
                            sys.stdout.write(f"\r  进度: {percent}% ")
                            sys.stdout.flush()
                print()
            logger.info(f"下载完成: {model_info['name']}")
            return model_path
        except Exception as e:
            logger.warning(f"镜像 {mirror} 失败: {e}")
            if model_path.exists() and model_path.stat().st_size == 0:
                model_path.unlink()
    raise RuntimeError("所有镜像下载失败")

# ---------- 更新 local_llm.py ----------
def update_local_llm(model_info: Dict, models_dir: Path):
    llm_path = PROJECT_ROOT / "intelligence" / "local_llm.py"
    shutil.copy2(llm_path, llm_path.with_suffix(".bak"))
    code = f'''# intelligence/local_llm.py —— 自动优化版
from pathlib import Path
import threading
from llama_cpp import Llama

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "{model_info['name']}"

class LocalBrain:
    def __init__(self, model_path=None, n_ctx={model_info['context']}):
        path = model_path or MODEL_PATH
        self.llm = Llama(
            model_path=str(path), n_ctx=n_ctx, n_threads=4,
            n_gpu_layers={model_info['n_gpu_layers']}, n_batch={model_info['batch']},
            use_mlock=True, use_mmap=False, verbose=False
        )
        self.lock = threading.Lock()

    def chat(self, messages, temperature=0.7, max_tokens=200):
        with self.lock:
            prompt = self._format(messages)
            out = self.llm(prompt, max_tokens=max_tokens, temperature=temperature,
                           top_p=0.9, repeat_penalty=1.1,
                           stop=["<|im_end|>", "<|user|>"], echo=False)
            return out["choices"][0]["text"].strip()

    def tool_chat(self, messages):
        return self.chat(messages, temperature=0.2, max_tokens=150)

    def _format(self, messages):
        prompt = ""
        for m in messages:
            prompt += f"<|im_start|>{{m['role']}}\\n{{m['content']}}<|im_end|>\\n"
        prompt += "<|im_start|>assistant\\n"
        return prompt

_brain = None
def get_brain():
    global _brain
    if _brain is None:
        _brain = LocalBrain()
    return _brain
'''
    with open(llm_path, "w", encoding="utf-8") as f:
        f.write(code)
    logger.info("local_llm.py 已更新")

# ---------- 知识库增强 ----------
def upgrade_knowledge_base(hw: Dict):
    if hw["ram_total_gb"] < 8:
        logger.info("内存不足，保留轻量检索")
        return
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers", "-q"])
        logger.info("已安装 sentence-transformers")
    except Exception:
        logger.warning("安装失败，跳过语义检索")
        return
    # 可在此添加 BGE 嵌入替换逻辑，视需要而定

# ---------- 能力分析 ----------
def analyze_capabilities() -> Dict:
    from utils.config import ConfigManager
    config = ConfigManager(str(PROJECT_ROOT / "config.yaml"))
    report = {
        "timestamp": datetime.now().isoformat(),
        "local_llm": config.get("use_local_llm", False),
        "knowledge_base_size": len(list((PROJECT_ROOT / "Knowledge" / "raw").glob("*"))) if (PROJECT_ROOT / "Knowledge" / "raw").exists() else 0,
        "memory_entries": 0,
        "tools_available": []
    }
    mem_db = PROJECT_ROOT / "Cache" / "memory.db"
    if mem_db.exists():
        import sqlite3
        conn = sqlite3.connect(str(mem_db))
        report["memory_entries"] = conn.execute("SELECT COUNT(*) FROM permanent_memory").fetchone()[0]
        conn.close()
    try:
        from intelligence.tool_executor import TOOLS_DEF
        report["tools_available"] = [t["name"] for t in TOOLS_DEF]
    except ImportError:
        pass
    return report

def print_report(report: Dict):
    print("\n" + "="*50)
    print("📊 LightAgent 能力分析报告")
    print(f"生成时间: {report['timestamp']}")
    print(f"本地 LLM: {'已启用' if report['local_llm'] else '已禁用'}")
    print(f"知识库文件数: {report['knowledge_base_size']}")
    print(f"永久记忆条目: {report['memory_entries']}")
    print(f"可用工具: {', '.join(report['tools_available']) if report['tools_available'] else '无'}")
    print("="*50)

# ---------- 主流程 ----------
def main():
    logger.info("🚀 CoreUpgrade 启动")
    hw = scan_hardware()
    logger.info(f"硬件: GPU {hw['gpu_name']}, 显存 {hw['vram_gb']:.1f}GB, 内存 {hw['ram_total_gb']:.1f}GB")
    model = recommend_model(hw)
    logger.info(f"推荐模型: {model['name']}")
    try:
        model_path = download_model(model, PROJECT_ROOT / "models")
        update_local_llm(model, PROJECT_ROOT / "models")
    except Exception as e:
        logger.error(f"模型升级失败: {e}")
    upgrade_knowledge_base(hw)
    report = analyze_capabilities()
    print_report(report)
    logger.info("✅ 升级完成，请重启 LightAgent")

if __name__ == "__main__":
    main()
