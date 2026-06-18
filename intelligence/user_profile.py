# intelligence/user_profile.py
import json, os
from pathlib import Path

class UserProfile:
    def __init__(self, path="user_profile.json"):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"frequent_commands": {}, "preferred_temperature": 0.7}

    def record_command(self, command):
        self.data["frequent_commands"][command] = self.data["frequent_commands"].get(command, 0) + 1
        self._save()

    def get_preference(self):
        return self.data["preferred_temperature"]

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
