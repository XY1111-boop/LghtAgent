# utils/cache.py —— 独立版本
from pathlib import Path
import sqlite3
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class CacheManager:
    def __init__(self, db_path=None, max_entries=500):
        if db_path is None:
            db_path = str(PROJECT_ROOT / "Cache" / "lightagent_cache.db")
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""CREATE TABLE IF NOT EXISTS code_cache
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             task_text TEXT UNIQUE,
                             whitelist_version TEXT,
                             code TEXT,
                             output TEXT,
                             timestamp REAL)""")
        self.conn.commit()

    def lookup(self, task_text, whitelist_version):
        cur = self.conn.execute(
            "SELECT code, output FROM code_cache WHERE task_text=? AND whitelist_version=? ORDER BY timestamp DESC LIMIT 1",
            (task_text, whitelist_version))
        row = cur.fetchone()
        if row:
            self.conn.execute("UPDATE code_cache SET timestamp=? WHERE task_text=?", (time.time(), task_text))
            self.conn.commit()
            return row[0], row[1]
        return None, None

    def save(self, task_text, code, output, whitelist_version):
        self.conn.execute("DELETE FROM code_cache WHERE task_text=?", (task_text,))
        self.conn.execute("INSERT INTO code_cache (task_text, whitelist_version, code, output, timestamp) VALUES (?,?,?,?,?)",
                          (task_text, whitelist_version, code, output, time.time()))
        self.conn.commit()
        self._evict_lru()

    def _evict_lru(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM code_cache")
        count = cur.fetchone()[0]
        if count > self.max_entries:
            delete_count = count - self.max_entries
            self.conn.execute("DELETE FROM code_cache WHERE id IN (SELECT id FROM code_cache ORDER BY timestamp ASC LIMIT ?)",
                              (delete_count,))
            self.conn.commit()

    def delete(self, task_text):
        self.conn.execute("DELETE FROM code_cache WHERE task_text=?", (task_text,))
        self.conn.commit()
