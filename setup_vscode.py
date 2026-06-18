# setup_vscode.py —— 自动为 LightAgent 生成 VS Code 工作区配置
import os, json

PROJECT = r"E:\LightAgent"
VSCODE_DIR = os.path.join(PROJECT, ".vscode")
os.makedirs(VSCODE_DIR, exist_ok=True)

# settings.json
settings = {
    "python.defaultInterpreterPath": "C:/Program Files/Python311/python.exe",
    "python.analysis.extraPaths": [
        "E:/LightAgent"
    ],
    "python.analysis.diagnosticSeverityOverrides": {
        "reportMissingImports": "none",        # 关闭导入报错（实际运行没问题）
        "reportInvalidTypeForm": "none",       # 关闭类型标注警告
        "reportReturnType": "none"             # 关闭返回值类型警告
    },
    "python.languageServer": "Pylance",
    "editor.formatOnSave": True,
    "python.formatting.provider": "autopep8",
    "[python]": {
        "editor.defaultFormatter": "ms-python.python"
    }
}
with open(os.path.join(VSCODE_DIR, "settings.json"), "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=4)

print("✅ VS Code 工作区配置已生成。请重新加载窗口（Ctrl+Shift+P → Reload Window）。")
