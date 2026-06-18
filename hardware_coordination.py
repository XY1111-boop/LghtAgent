# hardware_coordination.py —— 核显/独显任务分配
import os

def apply_hardware_coordination():
    """设置环境变量，让LLM用独显，其他用CPU/核显"""
    # 让PyTorch使用CUDA（独显）
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # 使用第一块NVIDIA GPU
    # 让OpenCV/OpenGL使用核显（不设置，默认通常会使用核显）
    # 禁用OneDNN使用MKL等CPU优化
    os.environ["OMP_NUM_THREADS"] = "2"  # 限制CPU线程数
    print("✅ 硬件协同环境已配置")
