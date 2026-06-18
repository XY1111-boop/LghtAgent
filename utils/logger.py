# utils/logger.py —— 修正缩进版
from pathlib import Path
import logging
import os
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class LogManager(QObject):
    status_signal = pyqtSignal(str)

    def __init__(self, log_dir=None, retention_days=30):
        super().__init__()
        if log_dir is None:
            log_dir = str(PROJECT_ROOT / "Logs")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.logger = logging.getLogger("LightAgent")
        self.logger.setLevel(logging.DEBUG)

        log_file = self.log_dir / f"lightagent_{datetime.now().strftime('%Y-%m-%d')}.log"
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        self._clean_old_logs()

    def _clean_old_logs(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for f in self.log_dir.glob("lightagent_*.log"):
            try:
                file_date = datetime.strptime(f.stem.split('_')[1], '%Y-%m-%d')
                if file_date < cutoff:
                    f.unlink()
            except Exception:
                pass

    def set_status_callback(self, callback):
        self.status_signal.connect(callback)

    def info(self, msg):
        self.logger.info(msg)
        self.status_signal.emit(msg)

    def warning(self, msg):
        self.logger.warning(msg)
        self.status_signal.emit(f"警告: {msg}")

    def error(self, msg):
        self.logger.error(msg)
        self.status_signal.emit(f"错误: {msg}")
