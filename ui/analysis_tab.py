from PyQt5.QtGui import QTextCursor
# ui/analysis_tab.py
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
