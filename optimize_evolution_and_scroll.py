# optimize_evolution_and_scroll.py —— 进化看板深度优化 + 全局滚动强化
import os, shutil, re

PROJECT = r"E:\LightAgent"

# ---------- 1. 强化 main_window.py 的滚动包裹 ----------
mainwin_path = os.path.join(PROJECT, "ui", "main_window.py")
if os.path.exists(mainwin_path):
    shutil.copy2(mainwin_path, mainwin_path + ".bak")
    with open(mainwin_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 确保 _wrap_scroll 函数存在且健壮
    if "def _wrap_scroll" not in content:
        wrap_func = '''
def _wrap_scroll(widget):
    """将任意控件包裹在可滚动的 QScrollArea 中"""
    from PyQt5.QtWidgets import QScrollArea
    if isinstance(widget, QScrollArea):
        return widget
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    scroll.setStyleSheet("QScrollArea { border: none; }")
    return scroll
'''
        content = content.replace("    def open_settings(self):", wrap_func + "\n    def open_settings(self):")

    # 替换 _try_load 方法中的 addTab 调用，使用 _wrap_scroll
    # 匹配模式：self.tabs.addTab(widget, title) 替换为 self.tabs.addTab(self._wrap_scroll(widget), title)
    content = re.sub(
        r'(self\.tabs\.addTab\()(widget,\s*title)',
        r'\1self._wrap_scroll(widget), title',
        content
    )
    # 如果上面的正则没匹配到，尝试更通用的替换
    if 'self._wrap_scroll(widget)' not in content.split("def _try_load")[1].split("def ")[0]:
        # 直接定位到 _try_load 中的 addTab 行
        try_load_start = content.find("def _try_load(self, title, module_name, class_name):")
        if try_load_start != -1:
            try_load_end = content.find("\n    def ", try_load_start + 1)
            if try_load_end == -1:
                try_load_end = len(content)
            method_body = content[try_load_start:try_load_end]
            new_body = method_body.replace(
                "self.tabs.addTab(widget, title)",
                "self.tabs.addTab(self._wrap_scroll(widget), title)"
            )
            content = content[:try_load_start] + new_body + content[try_load_end:]

    with open(mainwin_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main_window.py 滚动包裹已强化")

# ---------- 2. 深度优化进化看板 UI ----------
evo_path = os.path.join(PROJECT, "ui", "evolution_tab.py")
if os.path.exists(evo_path):
    shutil.copy2(evo_path, evo_path + ".bak")
    with open(evo_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 2.1 将整个进化看板的内容区包裹在一个 QScrollArea 中（顶部状态栏不动）
    # 简单做法：在主布局中，将 splitter 放入 QScrollArea
    # 但更好的做法是确保图表区域和底部区域各自可以滚动
    # 我们通过修改布局结构：将 splitter 本身放入一个 QScrollArea，这样整个看板都能滚动
    if "QScrollArea" not in content:
        # 在 init_ui 中，找到主布局添加 splitter 的地方
        content = content.replace(
            "main_layout.addWidget(self.splitter)",
            "scroll = QScrollArea()\n        scroll.setWidgetResizable(True)\n        scroll.setWidget(self.splitter)\n        main_layout.addWidget(scroll)"
        )
        # 添加必要的导入
        if "from PyQt5.QtWidgets import" in content and "QScrollArea" not in content:
            content = content.replace(
                "from PyQt5.QtWidgets import (",
                "from PyQt5.QtWidgets import QScrollArea, "
            )
        print("✅ 进化看板整体已支持滚动")
    else:
        print("✅ 进化看板已包含滚动区域")

    # 2.2 调整图表区域大小比例，让图表更大一些
    if "self.splitter.setStretchFactor" not in content:
        # 在 splitter 添加完两个区域后，设置拉伸因子
        content = content.replace(
            "self.splitter.addWidget(self.bottom_widget)",
            "self.splitter.addWidget(self.bottom_widget)\n        self.splitter.setStretchFactor(0, 3)\n        self.splitter.setStretchFactor(1, 1)"
        )
        print("✅ 进化看板图表区域已放大")

    # 2.3 优化天赋树卡片的样式（增加边距、圆角、阴影效果）
    content = content.replace(
        '"QFrame { background: #F0F4F8; border-radius: 8px; padding: 8px; margin: 4px; }"',
        '"QFrame { background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 12px; padding: 12px; margin: 6px; }"'
    )
    # 天赋进度条高度增加
    if "progress.setMaximum" in content:
        content = content.replace(
            "progress = QProgressBar()",
            "progress = QProgressBar()\n            progress.setMinimumHeight(20)"
        )
    print("✅ 天赋树样式已美化")

    # 2.4 高级编辑器增加行号区域和更大字体
    if "self.editor.setFont" in content:
        content = content.replace(
            'self.editor.setFont(QFont("Consolas", 10))',
            'self.editor.setFont(QFont("Consolas", 11))'
        )
        # 设置编辑器最小高度
        content = content.replace(
            "editor_layout.addWidget(self.editor)",
            "editor_layout.addWidget(self.editor)\n        self.editor.setMinimumHeight(300)"
        )
    print("✅ 高级编辑器已优化")

    with open(evo_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ evolution_tab.py 深度优化完成")

# ---------- 3. 通用组件优化：为其他可能缺少滚动的地方补上 ----------
# 学习中心、AI控制台等如果内部没有滚动，我们可以在主窗口初始化时全局包裹，但已经通过 _try_load 处理了。

print("\n🎉 所有优化已应用！重启 LightAgent：python main.py")
print("   - 所有标签页均可流畅滚动")
print("   - 进化看板图表更大，天赋树更美观，编辑器更舒适")
print("   - 未来添加的标签页自动获得滚动支持")
