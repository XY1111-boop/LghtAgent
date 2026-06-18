# project_paths.py —— 集中管理所有项目路径
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent

KNOWLEDGE_RAW = PROJECT_ROOT / "Knowledge/raw"
KNOWLEDGE_DIGESTED = PROJECT_ROOT / "Knowledge/digested"
LOGS_DIR = PROJECT_ROOT / "Logs"
CACHE_DIR = PROJECT_ROOT / "Cache"
MODELS_DIR = PROJECT_ROOT / "models"
EVOLUTION_DIR = PROJECT_ROOT / "EvolutionSnapshots"
BACKUP_DIR = PROJECT_ROOT / "Backup"

# 确保目录存在
for d in [KNOWLEDGE_RAW, KNOWLEDGE_DIGESTED, LOGS_DIR, CACHE_DIR, MODELS_DIR, EVOLUTION_DIR, BACKUP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 系统相关
IS_WINDOWS = os.name == 'nt'
IS_LINUX = os.name == 'posix'
