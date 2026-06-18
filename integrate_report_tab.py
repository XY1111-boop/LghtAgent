# integrate_report_tab.py —— 将分析报告网页添加到 LightAgent 主窗口
import os, shutil

PROJECT = r"E:\LightAgent"
MAINWIN = os.path.join(PROJECT, "ui", "main_window.py")

# 1. 创建分析报告标签页类
tab_code = '''# ui/analysis_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from pathlib import Path

class AnalysisReportTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        layout = QVBoxLayout()
        self.webview = QWebEngineView()
        self.webview.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parent.parent / "web" / "analysis.html")))
        layout.addWidget(self.webview)
        self.setLayout(layout)
'''
tab_file = os.path.join(PROJECT, "ui", "analysis_tab.py")
with open(tab_file, "w", encoding="utf-8") as f:
    f.write(tab_code)
print("✅ 分析报告标签页类已创建")

# 2. 修改 main_window.py，添加导入和标签页
if not os.path.exists(MAINWIN):
    print("❌ main_window.py 不存在")
    exit(1)

shutil.copy2(MAINWIN, MAINWIN + ".bak")
with open(MAINWIN, "r", encoding="utf-8") as f:
    content = f.read()

if "AnalysisReportTab" not in content:
    # 添加导入
    content = content.replace(
        "from ui.training_center import TrainingCenterTab",
        "from ui.training_center import TrainingCenterTab\nfrom ui.analysis_tab import AnalysisReportTab"
    )
    # 在 TAB_CONFIG 列表中添加标签页
    marker = "TAB_CONFIG = ["
    if marker in content:
        start = content.find(marker)
        end = content.find("]", start)
        new_tab = '    ("📊 分析报告", "ui.analysis_tab", "AnalysisReportTab"),\n'
        if new_tab not in content:
            content = content[:end] + new_tab + content[end:]
    with open(MAINWIN, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 分析报告标签页已添加到主窗口")
else:
    print("⚠️ 分析报告标签页已存在，跳过添加")

print("\n🎉 集成完成！请重启 LightAgent：python main.py")
print("确保心跳监控服务也在运行：python heartbeat_server.py")
