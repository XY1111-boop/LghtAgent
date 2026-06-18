# intelligence/training_engine.py —— 完整稳定版
import threading, json, re
from intelligence.experience_manager import ExperienceManager

class TrainingEngine:
    def __init__(self, api, manager):
        self.api = api
        self.manager = manager
        self.running = False
        self.progress = 0
        self.total = 0
        self.status = "空闲"
        self.stats = {"generated": 0, "passed": 0, "failed": 0, "skipped": 0}
        self.seen_instructions = set()
        self.callback = None
        self.sample_callback = None
# 自动心跳上报
        import threading, time

    def set_callback(self, func):
        self.callback = func

    def set_sample_callback(self, func):
        self.sample_callback = func

    def generate_samples(self, categories, samples_per_category=5):
        self.running = True
        self.total = len(categories) * samples_per_category
        self.progress = 0
        self.status = "生成中..."
        for category in categories:
            prompt = f"""你是一个 Windows 系统自动化专家。请生成 {samples_per_category} 条典型的用户指令，以及对应的安全 Python 代码。
指令类别：{category}
要求：
1. 代码只能使用以下函数：run_allowed_command(cmd), open_website(url), write_file(filename, content), mouse_click(x,y), keyboard_type(text)
2. 每条指令和代码用 JSON 数组格式返回，例如：
[
  {{"instruction": "打开计算器", "code": "run_allowed_command('calc')"}},
  ...
]
3. 直接返回 JSON，不要任何解释。"""
            try:
                if not self.running:
                    break
                response = self.api.call_with_prompt(prompt, temperature=0.7, max_tokens=2000)
                # 提取所有可能的 JSON 数组（容忍前后多余字符）
                json_candidates = re.findall(r'\[.*?\]', response, re.DOTALL)
                items = []
                for candidate in json_candidates:
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, list):
                            items.extend(parsed)
                    except json.JSONDecodeError:
                        continue
                if not items:
                    try:
                        full = json.loads(response)
                        if isinstance(full, list):
                            items = full
                        elif isinstance(full, dict) and 'data' in full:
                            items = full['data']
                    except:
                        pass
                if items:
                    for item in items:
                        if not self.running:
                            break
                        self.stats["generated"] += 1
                        instruction = item["instruction"]
                        # 短期记忆去重：本次训练中已生成过则跳过
                        if instruction in self.seen_instructions:
                            self.stats["skipped"] += 1
                            if self.sample_callback:
                                self.sample_callback(
                                    "⏭️ 跳过重复（本次已生成）",
                                    f"指令: {instruction}"
                                )
                            self.progress += 1
                            continue
                        self.seen_instructions.add(instruction)
                        code = item["code"]
                        # 代码合法性检查
                        if not self._validate_code(code):
                            self.stats["failed"] += 1
                            if self.sample_callback:
                                self.sample_callback(
                                    "❌ 代码不合法",
                                    f"指令: {instruction}\n"
                                    f"原因: 代码包含危险操作或缺少允许函数\n"
                                    f"代码:\n{code}"
                                )
                            self.progress += 1
                            continue
                        # 高阈值二次检查（防止模糊去重漏过）
                        if self.manager.search_similar(instruction, threshold=0.9):
                            self.stats["skipped"] += 1
                            if self.sample_callback:
                                self.sample_callback(
                                    "⏭️ 跳过重复（预过滤）",
                                    f"指令: {instruction}\n原因: 与已有样本高度相似"
                                )
                            self.progress += 1
                            continue
                        # 尝试添加（经验管理器会做模糊去重）
                        added = self.manager.add_experience(instruction, code, category)
                        if added:
                            self.stats["passed"] += 1
                            if self.sample_callback:
                                self.sample_callback(
                                    "✅ 已学习",
                                    f"指令: {instruction}\n代码:\n{code}"
                                )
                        else:
                            self.stats["skipped"] += 1
                            if self.sample_callback:
                                self.sample_callback(
                                    "⏭️ 跳过重复",
                                    f"指令: {instruction}\n"
                                    f"原因: 与已有样本相似度过高\n"
                                    f"代码:\n{code}"
                                )
                        self.progress += 1
                        if self.callback:
                            self.callback(self.manager.get_stats())
                else:
                    self.status = f"类别 {category} 返回格式错误"
                    if self.sample_callback:
                        self.sample_callback("⚠️ 格式错误", f"类别 {category} 返回的数据无法解析")
            except Exception as e:
                self.status = f"生成失败: {e}"
                if self.sample_callback:
                    self.sample_callback("💥 API异常", str(e))
            if not self.running:
                break
        self.running = False
        self.status = "完成" if self.progress >= self.total else "已停止"

    def _validate_code(self, code):
        allowed = ["run_allowed_command", "open_website", "write_file", "mouse_click", "keyboard_type"]
        dangerous = ["import", "exec(", "eval(", "subprocess", "os.system", "__"]
        for d in dangerous:
            if d in code:
                return False
        return any(func in code for func in allowed)

    def start(self, categories=None):
        if categories is None:
            categories = ["系统操作", "文件管理", "浏览器使用", "文本编辑", "Python编程辅助"]
        threading.Thread(target=self.generate_samples, args=(categories,), daemon=True).start()

    def stop(self):
        self.running = False

import random

class RLTrainer:
    def __init__(self, agent):
        self.agent = agent
        self.memory = []  # 经验回放

    def record_step(self, state, action, reward):
        self.memory.append((state, action, reward))

    def simple_q_learn(self, episodes=10):
        # 模拟强化学习更新策略（极简示例）
        for _ in range(episodes):
            action = random.choice(["增加温度", "降低温度", "保持不变"])
            reward = random.random()  # 模拟环境反馈
            print(f"动作: {action}, 奖励: {reward:.2f}")

class CurriculumTrainer:
    def __init__(self, agent):
        self.agent = agent
        self.level = 1

    def generate_curriculum(self):
        if self.level == 1:
            return ["简单系统操作", "基础文件管理"]
        elif self.level == 2:
            return ["复杂系统配置", "多步骤文件操作"]
        else:
            return ["高级自动化脚本", "安全渗透测试模拟"]
