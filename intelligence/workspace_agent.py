# workspace_agent.py —— AI 编程工作区 Agent
import os, json
from pathlib import Path

class WorkspaceAgent:
    def __init__(self, workspace_dir):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def scan_project(self):
        files = []
        for p in self.workspace.rglob("*"):
            if p.is_file():
                files.append(str(p.relative_to(self.workspace)))
        return files

    def read_file(self, path):
        full = self.workspace / path
        if full.exists():
            return full.read_text(encoding="utf-8")
        return ""

    def write_file(self, path, content):
        full = self.workspace / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        return f"文件 {path} 已保存"
