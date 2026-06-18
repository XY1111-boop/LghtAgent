# dynamic_dispatcher.py —— CPU/GPU/核显 任务分配
import os, subprocess, psutil, threading, time

class Dispatcher:
    """将不同算子分配到最适合的设备"""
    def __init__(self, model_manager):
        self.mm = model_manager
        self.gpu_available = self.mm.vram_bytes > 0
        self.igpu_available = self._check_igpu()
        self.load_monitor_thread = None
        self.stop_monitor = False

    def _check_igpu(self):
        # 检查核显是否可用（通常通过 OpenCL 或 DirectX）
        try:
            import pyopencl
            platforms = pyopencl.get_platforms()
            for p in platforms:
                if "Intel" in p.name:
                    return True
        except:
            pass
        return False

    def start_monitor(self):
        self.stop_monitor = False
        self.load_monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.load_monitor_thread.start()

    def _monitor_loop(self):
        while not self.stop_monitor:
            # 监控资源，触发熔断
            cpu_percent = psutil.cpu_percent(interval=1)
            mem_percent = psutil.virtual_memory().percent
            if mem_percent > 90 or cpu_percent > 95:
                self._trigger_circuit_breaker("high_load")
            time.sleep(5)

    def _trigger_circuit_breaker(self, reason):
        # 通知自愈模块
        print(f"⚠️ 触发熔断: {reason}")
        # 这里与 self_healing.py 联动
