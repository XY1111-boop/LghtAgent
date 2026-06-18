# intelligence/task_planner.py —— 任务规划与调度
import threading, queue, time, json

class TaskPlanner:
    def __init__(self, agent):
        self.agent = agent
        self.task_queue = queue.Queue()
        self.running = False

    def plan_and_schedule(self, goal):
        # 简单将目标拆分为子任务（实际可用 LLM 拆分）
        subtasks = [goal]  # 简化示例
        for task in subtasks:
            self.task_queue.put(task)
        if not self.running:
            self.running = True
            threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        while self.running and not self.task_queue.empty():
            task = self.task_queue.get()
            try:
                result = self.agent.process_user_input(task)
                print(f"✅ 任务完成: {task[:30]}... -> {result[:50]}")
            except Exception as e:
                print(f"❌ 任务失败: {e}")
            time.sleep(1)
        self.running = False
