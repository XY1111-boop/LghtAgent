# restore_main.py —— 从备份恢复 main.py
import os, shutil

PROJECT = r"E:\LightAgent"

# 1. 查找 main.py.bak 备份文件
bak_path = os.path.join(PROJECT, "main.py.bak")
if not os.path.exists(bak_path):
    # 尝试在其他备份目录查找
    for root, dirs, files in os.walk(PROJECT):
        if "main.py.bak" in files:
            bak_path = os.path.join(root, "main.py.bak")
            break
    else:
        print("❌ 未找到 main.py 的备份文件，需要重新生成。")
        # 这里会提供一个最新的 main.py 内容作为备选
        print("正在生成最新的 main.py ...")
        with open(os.path.join(PROJECT, "main.py"), "w", encoding="utf-8") as f:
            f.write(LATEST_MAIN_CONTENT)  # 下面提供
        print("✅ main.py 已重新生成（基于最终稳定版）")
        import sys
        sys.exit(0)

# 恢复备份
shutil.copy2(bak_path, os.path.join(PROJECT, "main.py"))
print("✅ main.py 已从备份恢复。")

# 同时清理 .bak 文件，避免再次被误删
for root, dirs, files in os.walk(PROJECT):
    for f in files:
        if f.endswith(".bak"):
            os.remove(os.path.join(root, f))
print("✅ 已清理所有 .bak 文件，防止循环误删。")