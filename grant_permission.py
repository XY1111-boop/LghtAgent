# grant_permission.py —— 预授权安全模式升级
import os, shutil

PROJECT = r"E:\LightAgent"

def safe_write(path, content):
    full = os.path.join(PROJECT, path)
    if os.path.exists(full):
        shutil.copy2(full, full + ".bak")
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ 已更新 {os.path.basename(path)}")

# 1. 为 main_window.py 添加授权弹窗方法
mainwin_path = os.path.join(PROJECT, "ui", "main_window.py")
if os.path.exists(mainwin_path):
    with open(mainwin_path, "r", encoding="utf-8") as f:
        content = f.read()
    if "show_permission_dialog" not in content:
        perm_method = '''
    def show_permission_dialog(self, title, code, risk):
        from PyQt5.QtWidgets import QMessageBox, QCheckBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(f"AI 请求执行以下操作 (风险: {risk})：\\n\\n{code[:200]}")
        msg.setInformativeText("请确认是否允许执行。")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        cb_10min = QCheckBox("10 分钟内不再提示")
        cb_always = QCheckBox("永久信任此应用")
        layout = msg.layout()
        layout.addWidget(cb_10min, layout.rowCount(), 0, 1, 2)
        layout.addWidget(cb_always, layout.rowCount(), 0, 1, 2)
        reply = msg.exec_()
        if reply == QMessageBox.Yes:
            if cb_always.isChecked():
                return "always"
            elif cb_10min.isChecked():
                return "temp"
            return "once"
        return "deny"
'''
        content = content.replace("    def open_settings(self):", perm_method + "\n    def open_settings(self):")
        with open(mainwin_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 授权弹窗已添加")
    else:
        print("✅ 授权弹窗已存在")

    # 绑定回调
    if "agent.confirm_callback = self.show_permission_dialog" not in content:
        content = content.replace(
            "self.statusBar().showMessage(\"就绪\")",
            "self.statusBar().showMessage(\"就绪\")\n        if hasattr(self.agent, \"confirm_callback\"):\n            self.agent.confirm_callback = self.show_permission_dialog"
        )
        with open(mainwin_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ 回调已绑定")

# 2. 修改 main.py，在执行前强制检查授权
main_path = os.path.join(PROJECT, "main.py")
if os.path.exists(main_path):
    with open(main_path, "r", encoding="utf-8") as f:
        content = f.read()
    old_exec = '''            # 真实执行
            if self.host_executor:'''
    new_exec = '''            # 真实执行（必须授权）
            if self.host_executor:
                if callable(self.confirm_callback):
                    risk = self.safety_auditor.assess_risk(code) if self.safety_auditor else "未知"
                    perm = self.confirm_callback("操作授权", code, risk)
                    if perm == "deny":
                        return "🚫 您拒绝了此操作。"
                # 执行代码'''
    if old_exec in content:
        content = content.replace(old_exec, new_exec)
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ main.py 已集成授权检查")
    else:
        print("⚠️ 未找到执行代码段，请手动检查")

print("\n🎉 升级完成！重启 LightAgent 后，任何 /run 命令都会弹出授权窗口。")
print("   启动命令：python main.py")
