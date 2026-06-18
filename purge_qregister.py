import os, re

PROJECT = r"E:\LightAgent"

def clean_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split("\n")
    new_lines = []
    for line in lines:
        continue  # 删除该行
        new_lines.append(line)
    new_content = "\n".join(new_lines)
    if new_content != content:
        # 备份
        bak = filepath + ".bak"
        if not os.path.exists(bak):
            os.rename(filepath, bak)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"✅ 已清理 {os.path.relpath(filepath, PROJECT)}")
        return True
    return False

# 遍历所有 .py 文件
cleaned_count = 0
for root, dirs, files in os.walk(PROJECT):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            if clean_file(filepath):
                cleaned_count += 1

print(f"\n🎉 清理完成！共处理 {cleaned_count} 个文件。")
print("现在请运行 python main.py 启动 LightAgent。")