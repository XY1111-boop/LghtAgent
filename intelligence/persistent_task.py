# intelligence/persistent_task.py
import json, os
from pathlib import Path

class TaskStateManager:
    def __init__(self, save_path="task_states.json"):
        self.path = Path(save_path)
        self.states = self._load()

    def _load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_state(self, task_id, state):
        self.states[task_id] = state
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.states, f, ensure_ascii=False, indent=2)

    def get_state(self, task_id):
        return self.states.get(task_id)
