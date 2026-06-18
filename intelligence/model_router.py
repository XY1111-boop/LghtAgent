# intelligence/model_router.py
class ModelRouter:
    def __init__(self, agent):
        self.agent = agent

    def select_model(self, task):
        complexity = len(task) + sum(1 for c in task if c in "计算证明分析")
        if complexity > 20:
            return "cloud"  # 复杂任务使用云端大模型
        return "local"       # 简单任务使用本地模型
