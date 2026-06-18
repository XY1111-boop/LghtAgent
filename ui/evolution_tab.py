from PyQt5.QtGui import QTextCursor
# ui/evolution_tab.py —— 游戏化进化看板
import json, threading, importlib
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTextEdit, QMessageBox, QSplitter,
                             QFrame, QProgressBar, QScrollArea)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

class EvolutionTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.evo_log = "EvolutionSnapshots/log.jsonl"
        self.advanced_mode = False
        self.init_ui()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(5000)

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 模式切换按钮
        mode_layout = QHBoxLayout()
        self.mode_btn = QPushButton("🔧 高级模式 (代码编辑器)")
        self.mode_btn.clicked.connect(self.toggle_mode)
        mode_layout.addWidget(self.mode_btn)
        mode_layout.addStretch()
        main_layout.addLayout(mode_layout)

        # 状态栏
        self.status_label = QLabel("进化状态：检查中...")
        self.status_label.setStyleSheet("font-weight: bold; color: #4A90D9;")
        main_layout.addWidget(self.status_label)

        # 分割器
        self.splitter = QSplitter(Qt.Vertical)

        # ── 图表区域 ──
        chart_widget = QWidget()
        chart_layout = QVBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        chart_widget.setLayout(chart_layout)
        self.splitter.addWidget(chart_widget)

        # ── 天赋树/编辑器区域 ──
        self.bottom_widget = QWidget()
        self.bottom_layout = QVBoxLayout()

        # 天赋树界面（普通模式）
        self.talent_frame = QFrame()
        self.talent_layout = QVBoxLayout()
        self.talent_widgets = {}  # 存储天赋控件

        # 从 evolution_tree.py 加载天赋配置
        self.load_talents()

        self.talent_frame.setLayout(self.talent_layout)
        self.bottom_layout.addWidget(self.talent_frame)

        # 代码编辑器（高级模式，初始隐藏）
        self.editor_frame = QFrame()
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(QLabel("自定义进化规则 (以 evo_ 开头的函数会被自动执行)"))
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 10))
        self.editor.setStyleSheet("background-color: #1E1E1E; color: #D4D4D4;")
        rules_path = Path("evolution_rules.py")
        if rules_path.exists():
            self.editor.setPlainText(rules_path.read_text(encoding="utf-8"))
        editor_layout.addWidget(self.editor)
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存规则")
        save_btn.clicked.connect(self.save_rules)
        reload_btn = QPushButton("重新加载规则")
        reload_btn.clicked.connect(self.reload_rules)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reload_btn)
        editor_layout.addLayout(btn_layout)
        self.editor_frame.setLayout(editor_layout)
        self.editor_frame.setVisible(False)
        self.bottom_layout.addWidget(self.editor_frame)

        self.bottom_widget.setLayout(self.bottom_layout)
        self.splitter.addWidget(self.bottom_widget)

        main_layout.addWidget(self.splitter)
        self.setLayout(main_layout)
        self.refresh_all()

    def load_talents(self):
        """动态加载天赋树"""
        # 清空现有控件
        for i in reversed(range(self.talent_layout.count())):
            self.talent_layout.itemAt(i).widget().setParent(None)

        try:
            spec = importlib.util.spec_from_file_location(
                "evolution_tree",
                str(Path("evolution_tree.py").resolve())
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            talents = module.TALENTS
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法加载天赋树: {e}")
            return

        for talent in talents:
            frame = QFrame()
            frame.setStyleSheet("QFrame { background: #F0F4F8; border-radius: 8px; padding: 8px; margin: 4px; }")
            hbox = QHBoxLayout()

            # 信息区
            info_layout = QVBoxLayout()
            name_label = QLabel(f"{talent['name']} (Lv.{talent['level']}/{talent['max_level']})")
            name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            desc_label = QLabel(talent['desc'])
            desc_label.setWordWrap(True)
            info_layout.addWidget(name_label)
            info_layout.addWidget(desc_label)
            hbox.addLayout(info_layout)

            # 进度条
            progress = QProgressBar()
            progress.setMaximum(talent['max_level'])
            progress.setValue(talent['level'])
            progress.setStyleSheet("QProgressBar::chunk { background: #4A90D9; }")
            hbox.addWidget(progress)

            # 升级按钮
            upgrade_btn = QPushButton("⬆ 升级")
            upgrade_btn.setStyleSheet("background: #4A90D9; color: white; padding: 6px 12px; border-radius: 4px;")
            upgrade_btn.clicked.connect(lambda checked, tid=talent['id']: self.upgrade_talent(tid))
            hbox.addWidget(upgrade_btn)

            frame.setLayout(hbox)
            self.talent_layout.addWidget(frame)
            self.talent_widgets[talent['id']] = frame

    def upgrade_talent(self, talent_id):
        success, msg = self.agent.evolution_controller.upgrade_talent(talent_id)
        QMessageBox.information(self, "升级结果", msg)
        self.load_talents()  # 刷新显示
        self.refresh_all()

    def toggle_mode(self):
        self.advanced_mode = not self.advanced_mode
        self.talent_frame.setVisible(not self.advanced_mode)
        self.editor_frame.setVisible(self.advanced_mode)
        self.mode_btn.setText("🎮 普通模式 (天赋树)" if self.advanced_mode else "🔧 高级模式 (代码编辑器)")

    def refresh_all(self):
        # 状态
        evo_enabled = self.agent.config.get("evolution_enabled", False)
        self.status_label.setText("● 进化运行中" if evo_enabled else "○ 进化未启用")

        # 图表
        self.figure.clear()
        if not Path(self.evo_log).exists():
            ax = self.figure.add_subplot(111)
            ax.set_title("暂无进化事件")
            self.canvas.draw()
            return

        dates, levels = [], []
        with open(self.evo_log, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    dates.append(datetime.fromisoformat(entry["time"]))
                    levels.append(entry.get("level", "USER"))
                except:
                    pass
        if not dates:
            ax = self.figure.add_subplot(111)
            ax.set_title("无有效事件")
            self.canvas.draw()
            return

        ax1 = self.figure.add_subplot(211)
        level_counts = {}
        for lvl in levels:
            level_counts[lvl] = level_counts.get(lvl, 0) + 1
        ax1.bar(level_counts.keys(), level_counts.values(), color=['#4A90D9', '#F39C12', '#E74C3C'])
        ax1.set_title("进化事件统计")
        ax1.set_ylabel("次数")

        ax2 = self.figure.add_subplot(212)
        y = [1 if lvl=="L1" else (2 if lvl=="L2" else 3) for lvl in levels]
        ax2.plot(range(len(y)), y, 'o-', color='#4A90D9')
        ax2.set_title("进化等级时间线")
        ax2.set_xlabel("事件序号")
        ax2.set_ylabel("等级")

        self.figure.subplots_adjust(left=0.1, bottom=0.1, right=0.95, top=0.95, hspace=0.3)
        self.canvas.draw()

    def save_rules(self):
        new_code = self.editor.toPlainText()
        try:
            compile(new_code, "evolution_rules.py", "exec")
        except SyntaxError as e:
            QMessageBox.critical(self, "语法错误", f"规则代码存在语法错误：\n{e}")
            return
        with open("evolution_rules.py", "w", encoding="utf-8") as f:
            f.write(new_code)
        QMessageBox.information(self, "保存成功", "规则已保存，请点击“重新加载规则”使其生效。")

    def reload_rules(self):
        try:
            self.agent.evolution_controller._load_rules()
            QMessageBox.information(self, "成功", "规则已重新加载。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败：{e}")

    def load_history_log(self):
        """读取进化日志并返回最近50条"""
        if not os.path.exists(self.evo_log):
            return []
        with open(self.evo_log, "r", encoding="utf-8") as f:
            lines = f.readlines()[-50:]
        return [json.loads(line) for line in lines]
