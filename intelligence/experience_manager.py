# intelligence/experience_manager.py —— 智能去重版
import json, os
from pathlib import Path
from threading import Lock

class ExperienceManager:
    def __init__(self, db_path="experience_db.json"):
        self.db_path = Path(db_path)
        self.lock = Lock()
        self.stats = {"total": 0, "used": 0, "last_used": None}
        self.data = []
        self._load()

    def _load(self):
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    saved = json.loads(content)
                    if isinstance(saved, dict) and "stats" in saved:
                        self.data = saved["data"]
                        self.stats = saved["stats"]
                    else:
                        self.data = saved
                        self.stats["total"] = len(self.data)
        else:
            self.data = []
            self.stats = {"total": 0, "used": 0, "last_used": None}

    def _save(self):
        output = {"data": self.data, "stats": self.stats}
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

    def add_experience(self, instruction, code, description=""):
        with self.lock:
            # 完全匹配去重
            if any(e["instruction"] == instruction for e in self.data):
                return False
            # 模糊匹配去重（相似度 > 0.8 则视为重复）
            if self.search_similar(instruction, threshold=0.8):
                return False
            self.data.append({
                "instruction": instruction,
                "code": code.strip(),
                "description": description,
                "success_count": 0
            })
            self.stats["total"] = len(self.data)
            self._save()
            return True

    def record_success(self, instruction):
        with self.lock:
            for exp in self.data:
                if exp["instruction"] == instruction:
                    exp["success_count"] = exp.get("success_count", 0) + 1
                    self.stats["used"] += 1
                    self.stats["last_used"] = instruction
                    self._save()
                    return

    def get_all(self):
        return self.data.copy()

    def search_similar(self, query, threshold=0.6):
        results = []
        for exp in self.data:
            common = len(set(query) & set(exp["instruction"]))
            score = common / max(len(set(query)), 1)
            if score >= threshold:
                results.append((score, exp))
        results.sort(reverse=True, key=lambda x: x[0])
        return [exp for _, exp in results]

    def count(self):
        return len(self.data)

    def get_stats(self):
        return {
            "total": self.stats["total"],
            "used": self.stats["used"],
            "last_used": self.stats["last_used"],
            "success_rate": round(self.stats["used"] / max(self.stats["total"], 1), 4)
        }

    def clear(self):
        with self.lock:
            self.data = []
            self.stats = {"total": 0, "used": 0, "last_used": None}
            self._save()
