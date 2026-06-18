# init_git.py —— 一键为 LightAgent 项目添加 Git 版本控制
import os, subprocess, sys, shutil

PROJECT = r"E:\LightAgent"

def run(cmd, cwd=PROJECT):
    """执行命令并打印输出"""
    print(f"🔧 执行: {cmd}")
    subprocess.run(cmd, shell=True, cwd=cwd, check=False)

# 1. 初始化 Git 仓库（如果还未初始化）
if not os.path.exists(os.path.join(PROJECT, ".git")):
    run("git init")
    print("✅ Git 仓库已初始化")
else:
    print("⚠️ Git 仓库已存在，跳过 init")

# 2. 设置用户信息（如果未全局设置，请手动替换为您的信息）
# 如果尚未设置，脚本会提示您输入
name = input("请输入您的 Git 用户名（如 ZhangYaoYao）: ")
email = input("请输入您的 Git 邮箱: ")
if name and email:
    run(f'git config user.name "{name}"')
    run(f'git config user.email "{email}"')
else:
    print("⚠️ 用户信息未填写，可稍后使用 git config 命令设置")

# 3. 创建 .gitignore 文件（忽略不需要版本控制的文件）
gitignore_content = """
# Python 缓存
__pycache__/
*.py[cod]
*.pyo

# 虚拟环境
venv/
env/

# 日志文件
Logs/
*.log

# 数据库和缓存
Cache/
chroma_db/
*.db
*.sqlite3

# 模型文件（体积大，建议单独管理）
models/
*.gguf

# 临时文件和备份
*.bak
*.backup
fix_*.py
repair_*.py
upgrade_*.py
install_*.py
final_*.py
diagnose_*.py
test_*.py
temp_*.py
*.zip

# 系统文件
Thumbs.db
Desktop.ini

# IDE 配置文件
.vscode/
.idea/
*.swp
*.swo

# 桌面日志和报告
Desktop/
LightAgent_*.txt

# 其它
web/mermaid.min.js
*.pkl
*.joblib
"""

with open(os.path.join(PROJECT, ".gitignore"), "w", encoding="utf-8") as f:
    f.write(gitignore_content)
print("✅ .gitignore 已创建（忽略临时文件、模型、日志等）")

# 4. 添加所有文件并提交
run("git add .")
# 检查是否有文件需要提交
status = subprocess.run("git status --porcelain", shell=True, cwd=PROJECT, capture_output=True, text=True)
if status.stdout.strip():
    run('git commit -m "🎉 LightAgent 项目首次提交：完整功能版，包含本地大脑、沙箱、进化系统等"')
    print("✅ 首次提交完成！")
else:
    print("⚠️ 没有文件变更，跳过提交")

# 5. 显示状态
print("\n📊 当前 Git 状态：")
run("git log --oneline -5")

print("\n🎉 Git 版本控制配置完成！")
print("以后您可以使用以下命令管理项目：")
print("  git add .                 # 添加所有变更")
print('  git commit -m "描述"      # 提交变更')
print("  git log                  # 查看历史记录")
print("  git checkout -- 文件名    # 撤销单个文件修改")
print("  git reset --hard HEAD    # 回退到上次提交")
print("\n💡 建议：每次修改重要功能前先 git commit，这样永远可以回退。")
