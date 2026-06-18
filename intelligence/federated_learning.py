# intelligence/federated_learning.py —— 联邦学习接口
class FederatedClient:
    def __init__(self, agent):
        self.agent = agent

    def get_local_model_params(self):
        # 返回当前本地模型的参数摘要（模拟）
        return {"model": "Qwen2.5-0.5B", "weights_version": "v1"}

    def update_with_global_model(self, global_params):
        # 实际应合并参数，此处仅记录
        print(f"接收到全局模型参数: {global_params}")
