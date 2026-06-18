# intelligence/file_monitor.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import time, threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def start_monitor(knowledge_base, logger=None):
    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if event.is_directory:
                return
            path = event.src_path
            if Path(path).suffix.lower() in ['.txt', '.pdf', '.docx', '.md', '.pptx']:
                if logger:
                    logger.info(f"发现新文件，正在消化：{path}")
                knowledge_base.add_to_raw(path)

    observer = Observer()
    observer.schedule(Handler(), str(knowledge_base.raw), recursive=False)
    observer.start()
    return observer
