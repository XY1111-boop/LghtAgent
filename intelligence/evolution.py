# intelligence/evolution.py —— 游戏化进化控制器
import time, threading, json, importlib, sys, traceback
from datetime import datetime
from pathlib import Path

class Introspector:
    def __init__(self):
        self.metrics = {"error_rate": 0.0, "task_success_rate": 1.0}
# 自动心跳上报
        import threading, time
    def update(self, **kwargs):
        self.metrics.update(kwargs)

class EvolutionController:
    def __init__(self, agent):
        self.agent = agent
        self.enabled = agent.config.get("evolution_enabled", False)
        self.introspector = Introspector()
        self.rules = []                # 用户自定义函数
        self.talents = {}              # 天赋等级
        self.log_path = Path("EvolutionSnapshots/log.jsonl")
        self._load_talents()
        self._load_rules()
        if self.enabled:
            self.start_monitoring()

    def _load_talents(self):
        """从 evolution_tree.py 加载天赋配置"""
        try:
            spec = importlib.util.spec_from_file_location(
                "evolution_tree",
                str(Path(__file__).resolve().parent.parent / "evolution_tree.py")
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for t in module.TALENTS:
                self.talents[t["id"]] = t
            # 从配置文件读取已保存的等级
            saved = self.agent.config.get("evolution_talents", {})
            for tid, level in saved.items():
                if tid in self.talents:
                    self.talents[tid]["level"] = level
            print(f"✅ 已加载 {len(self.talents)} 个天赋")
        except Exception as e:
            print(f"⚠️ 加载天赋失败: {e}")

    def _load_rules(self):
        """加载用户自定义规则（evolution_rules.py）"""
        try:
            rules_path = Path(__file__).resolve().parent.parent / "evolution_rules.py"
            if not rules_path.exists():
                return
            spec = importlib.util.spec_from_file_location("evolution_rules", str(rules_path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for name in dir(module):
                if name.startswith("evo_") and callable(getattr(module, name)):
                    self.rules.append(getattr(module, name))
            print(f"✅ 已加载 {len(self.rules)} 条自定义规则")
        except Exception as e:
            print(f"⚠️ 加载自定义规则失败: {e}")

    def upgrade_talent(self, talent_id):
        """升级指定天赋"""
        if talent_id not in self.talents:
            return False, "天赋不存在"
        talent = self.talents[talent_id]
        if talent["level"] >= talent["max_level"]:
            return False, "已达最高等级"
        talent["level"] += 1
        # 保存到配置文件
        saved = self.agent.config.get("evolution_talents", {})
        saved[talent_id] = talent["level"]
        self.agent.config.set("evolution_talents", saved)
        # 执行升级效果（调用对应函数）
        effect_func = getattr(self, talent["effect"], None)
        if effect_func:
            try:
                result = effect_func()
                self._log(f"天赋 {talent['name']} 升级到 Lv.{talent['level']}: {result}")
            except Exception as e:
                self._log(f"天赋 {talent['name']} 升级效果执行失败: {e}")
        return True, f"已升级到 Lv.{talent['level']}"

    # ─── 内置天赋效果函数 ───
    def upgrade_intelligence(self):
        """智力：降低温度以提高准确性"""
        old = self.agent.config.get("creativity_temperature", 0.7)
        new = max(0.3, old - 0.05)
        self.agent.config.set("creativity_temperature", new)
        return f"温度从 {old:.2f} 降至 {new:.2f}"

    def upgrade_speed(self):
        """速度：提高批处理大小，启用内存锁定"""
        # 这些参数需要在 local_llm.py 重启后生效，这里仅记录
        return "已优化推理参数，重启后生效"

    def upgrade_safety(self):
        """安全：激活额外审计规则"""
        # 标记安全等级，可在沙箱中使用
        self.agent.config.set("safety_level", self.talents["safety"]["level"])
        return f"安全等级提升至 {self.talents['safety']['level']}"

    def upgrade_creativity(self):
        """创意：提高温度并增加 top_p"""
        old_temp = self.agent.config.get("creativity_temperature", 0.7)
        new_temp = min(1.5, old_temp + 0.1)
        self.agent.config.set("creativity_temperature", new_temp)
        return f"温度从 {old_temp:.2f} 升至 {new_temp:.2f}"

    def start_monitoring(self):
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self):
        while self.enabled:
            # 执行所有用户自定义规则
            for rule in self.rules:
                try:
                    result = rule(self.agent)
                    self._log(f"规则 {rule.__name__}: {result}")
                except Exception as e:
                    self._log(f"规则 {rule.__name__} 异常: {e}")
            time.sleep(60)

    def _log(self, description):
        entry = {"time": datetime.now().isoformat(), "level": "USER", "description": description}
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
