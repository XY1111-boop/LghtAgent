# federated.py —— 联邦学习通信（简化版）
import requests, json, threading, time

class FederatedNode:
    def __init__(self, node_id, port=5000):
        self.node_id = node_id
        self.port = port
        self.peers = {}  # {node_id: "http://ip:port"}
        self.lora_weights = None

    def join_group(self, group_url):
        # 向组长注册
        resp = requests.post(f"{group_url}/join", json={"node_id": self.node_id, "port": self.port})
        if resp.ok:
            self.peers = resp.json()["peers"]
            print("已加入联邦小组")

    def sync_weights(self, weights):
        # 聚合权重（FedAvg）
        all_weights = [weights]
        for peer in self.peers.values():
            try:
                resp = requests.get(f"{peer}/weights")
                all_weights.append(resp.json())
            except:
                pass
        if all_weights:
            avg = {}
            for key in all_weights[0].keys():
                avg[key] = sum(w[key] for w in all_weights) / len(all_weights)
            self.lora_weights = avg
            return avg
        return weights
