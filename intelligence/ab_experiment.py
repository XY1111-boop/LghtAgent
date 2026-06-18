# intelligence/ab_experiment.py —— A/B测试管理
import json, time, random
from pathlib import Path

class ABTestManager:
    def __init__(self, db_path="ab_experiments.json"):
        self.db_path = Path(db_path)
        self.experiments = self._load()

    def _load(self):
        if self.db_path.exists():
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self):
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.experiments, f, ensure_ascii=False, indent=2)

    def create_experiment(self, name, variants):
        exp = {"name": name, "variants": variants, "results": {}, "created": time.time()}
        self.experiments.append(exp)
        self._save()
        return exp

    def record_trial(self, exp_name, variant, success):
        for exp in self.experiments:
            if exp["name"] == exp_name:
                if variant not in exp["results"]:
                    exp["results"][variant] = {"success": 0, "total": 0}
                exp["results"][variant]["total"] += 1
                if success:
                    exp["results"][variant]["success"] += 1
                self._save()
                return
