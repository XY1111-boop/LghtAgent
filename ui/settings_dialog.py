# ui/settings_dialog.py
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QCheckBox, QSlider, QDialogButtonBox, QLabel
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("设置")
        self.setMinimumWidth(400)
        layout = QFormLayout()

        # 本地大脑开关
        self.local_check = QCheckBox()
        self.local_check.setChecked(config.get("use_local_llm", False))
        self.local_check.toggled.connect(self._on_local_toggled)
        layout.addRow("使用本地大脑 (张瑶瑶):", self.local_check)

        # API Key (云端)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setText(config.get("api_key", ""))
        self.api_key_edit.setPlaceholderText("使用云端DeepSeek时必填")
        layout.addRow("DeepSeek API Key:", self.api_key_edit)

        # Serper API Key
        self.serper_key_edit = QLineEdit()
        self.serper_key_edit.setText(config.get("serper_api_key", ""))
        layout.addRow("Serper API Key:", self.serper_key_edit)

        # 自进化开关
        self.evolution_check = QCheckBox()
        self.evolution_check.setChecked(config.get("evolution_enabled", False))
        layout.addRow("启用自进化:", self.evolution_check)

        # 进化激进程度
        self.aggressiveness_slider = QSlider(Qt.Horizontal)
        self.aggressiveness_slider.setRange(0, 100)
        self.aggressiveness_slider.setValue(int(config.get("evolution_aggressiveness", 0.5) * 100))
        layout.addRow("进化激进程度:", self.aggressiveness_slider)

        # 默认温度
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 200)
        self.temperature_slider.setValue(int(config.get("creativity_temperature", 0.7) * 100))
        layout.addRow("默认温度:", self.temperature_slider)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self.setLayout(layout)

        # 初始状态
        self._on_local_toggled(self.local_check.isChecked())

    def _on_local_toggled(self, checked):
        """如果启用了本地大脑，则云端API Key不必填"""
        self.api_key_edit.setEnabled(not checked)
        if checked:
            self.api_key_edit.setPlaceholderText("本地模式无需填写")
        else:
            self.api_key_edit.setPlaceholderText("使用云端DeepSeek时必填")

    def save_settings(self):
        self.config.set("use_local_llm", self.local_check.isChecked())
        self.config.set("api_key", self.api_key_edit.text())
        self.config.set("serper_api_key", self.serper_key_edit.text())
        self.config.set("evolution_enabled", self.evolution_check.isChecked())
        self.config.set("evolution_aggressiveness", self.aggressiveness_slider.value() / 100.0)
        self.config.set("creativity_temperature", self.temperature_slider.value() / 100.0)
        self.accept()
