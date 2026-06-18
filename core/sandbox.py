# core/sandbox.py —— 纯净版
import multiprocessing
import sys
import os
import time
import traceback
import math
from io import StringIO
import psutil

SAFE_BUILTINS = {
    'print': print,
    'int': int, 'float': float, 'str': str, 'bool': bool,
    'list': list, 'dict': dict, 'set': set, 'tuple': tuple,
    'range': range, 'len': len, 'min': min, 'max': max,
    'abs': abs, 'round': round, 'sorted': sorted,
    'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter,
    'type': type, 'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
    'True': True, 'False': False, 'None': None,
    'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
    'KeyError': KeyError, 'IndexError': IndexError,
    'math': math
}

def free_fall(t, g=9.8):
    return 0.5 * g * t ** 2

def collision_detect(x1, y1, r1, x2, y2, r2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 <= (r1 + r2) ** 2

SAFE_BUILTINS['free_fall'] = free_fall
SAFE_BUILTINS['collision_detect'] = collision_detect

class Sandbox:
    def __init__(self, memory_limit=256):
        self.memory_limit = memory_limit

    def run(self, code: str, timeout=5, trace=False) -> dict:
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=_sandbox_exec, args=(code, timeout, trace, self.memory_limit, result_queue))
        p.start()
        p.join(timeout + 1)
        if p.is_alive():
            p.terminate()
            p.join()
            return {"success": False, "output": "", "error": "执行超时", "timeout": True, "trace_data": None}
        if not result_queue.empty():
            return result_queue.get()
        return {"success": False, "output": "", "error": "子进程无返回", "timeout": False, "trace_data": None}

def _sandbox_exec(code, timeout, trace, mem_limit_mb, queue):
    stop_monitor = False
    def memory_monitor():
        process = psutil.Process(os.getpid())
        limit_bytes = mem_limit_mb * 1024 * 1024
        while not stop_monitor:
            try:
                mem = process.memory_info().rss
                if mem > limit_bytes:
                    os._exit(1)
            except:
                pass
            time.sleep(0.1)
    import threading
    monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
    monitor_thread.start()
    old_stdout = sys.stdout
    sys.stdout = output_capture = StringIO()
    trace_data = []
    start_time = time.time()
    try:
        exec_globals = {'__builtins__': SAFE_BUILTINS}
        if trace:
            def trace_func(frame, event, arg):
                if event == 'call':
                    trace_data.append({'event': 'call', 'function': frame.f_code.co_name, 'lineno': frame.f_lineno, 'time': time.time()-start_time})
                elif event == 'line':
                    local_vars = {k: str(v) for k, v in frame.f_locals.items() if not k.startswith('__')}
                    trace_data.append({'event': 'line', 'lineno': frame.f_lineno, 'locals': local_vars, 'time': time.time()-start_time})
                elif event == 'return':
                    trace_data.append({'event': 'return', 'function': frame.f_code.co_name, 'value': str(arg), 'time': time.time()-start_time})
                return trace_func
            sys.settrace(trace_func)
        exec(code, exec_globals)
        output = output_capture.getvalue()
        success = True
        error = None
    except Exception as e:
        output = output_capture.getvalue()
        success = False
        error = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
    finally:
        sys.stdout = old_stdout
        stop_monitor = True
        monitor_thread.join(timeout=1)
    queue.put({"success": success, "output": output, "error": error, "timeout": False, "trace_data": trace_data if trace else None})
