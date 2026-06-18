# self_healing.py —— 系统健康监控与自动降级
import psutil, GPUtil, time, threading, logging

class SelfHealing:
    def __init__(self):
        self.state = "normal"  # normal, degraded, recovering
        self.logger = logging.getLogger("SelfHealing")
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def _monitor(self):
        while True:
            mem = psutil.virtual_memory().percent
            cpu = psutil.cpu_percent(interval=1)
            gpu_mem = 0
            try:
                gpu = GPUtil.getGPUs()[0]
                gpu_mem = gpu.memoryUtil * 100
            except:
                pass

            if mem > 90 or cpu > 95 or gpu_mem > 90:
                self.degrade("资源超限")
            elif self.state == "degraded" and mem < 70 and cpu < 70:
                self.recover()
            time.sleep(10)

    def degrade(self, reason):
        if self.state != "degraded":
            self.state = "degraded"
            self.logger.warning(f"降级: {reason}")
            # 停止投机解码、卸载温记忆等（通过回调）

    def recover(self):
        self.state = "normal"
        self.logger.info("恢复正常")
