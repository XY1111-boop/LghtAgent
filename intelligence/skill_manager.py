# skill_manager.py —— 技能管理器（兼容旧 SkillManager）
import yaml, os, json
from pathlib import Path

class SkillManager:
    def __init__(self, skills_dir="skills"):
        self.skills_dir = Path(skills_dir)
        self.skills = {}
        self.load_skills()

    def load_skills(self):
        if self.skills_dir.exists():
            for yaml_file in self.skills_dir.glob("*.yaml"):
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self.skills[data["name"]] = data

    def find_skill(self, user_input):
        for skill in self.skills.values():
            if any(trigger in user_input for trigger in skill.get("triggers", [])):
                return skill
        return None

    def add_skill(self, skill_data):
        name = skill_data["name"]
        self.skills[name] = skill_data
        with open(self.skills_dir / f"{name}.yaml", "w", encoding="utf-8") as f:
            yaml.dump(skill_data, f, allow_unicode=True)
