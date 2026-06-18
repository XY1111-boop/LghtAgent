# auto_repair_v3.py —— 自动删除干扰文件 + 基于 DeepSeek 修复错误
import os, sys, time, json, requests, shutil, traceback
from pathlib import Path

# ╔══════════════════════════════════════════════════════════╗
# ║  🔑 在这里填入你的 DeepSeek API Key（必填）               ║
# ╚══════════════════════════════════════════════════════════╝
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

PROJECT_ROOT = Path(__file__).resolve().parent

# 核心模块路径（这些目录下的文件才允许保留并修复）
CORE_DIRS = {
    "core", "intelligence", "knowledge", "ui", "utils", "plugins"
}
# 排除扫描的目录
EXCLUDE_DIRS = {"__pycache__", ".git", "chroma_db", "Logs", "Cache", "models", "EvolutionSnapshots", "Backup", "Knowledge/chroma_db"}
MAX_ROUNDS = 8
FAILED_FILES = set()

# ─── 清理干扰文件（非核心目录的 .py 文件直接删除） ───
def clean_temp_files():
    """删除所有非核心目录的临时脚本（如 backup_scripts、fix_* 等）"""
    deleted = 0
    for root, dirs, files in os.walk(PROJECT_ROOT):
        # 跳过核心目录和排除目录
        rel_root = Path(root).relative_to(PROJECT_ROOT)
        if rel_root.parts and rel_root.parts[0] in CORE_DIRS:
            continue
        if any(excluded in rel_root.parts for excluded in EXCLUDE_DIRS):
            continue
        # 删除该目录下所有 .py 文件（以及可能的 .bak 文件）
        for file in files:
            if file.endswith(".py") or file.endswith(".bak"):
                file_path = Path(root) / file
                # 保护自己不被删除
                if file_path.resolve() == Path(__file__).resolve():
                    continue
                try:
                    file_path.unlink()
                    deleted += 1
                    print(f"  🗑️ 已删除干扰文件: {file_path.relative_to(PROJECT_ROOT)}")
                except Exception as e:
                    print(f"  ⚠️ 无法删除 {file_path}: {e}")
    return deleted

# ─── 语法检查与修复 ───
def check_syntax(code: str, filename: str = "<test>"):
    try:
        compile(code, filename, "exec")
        return True, None
    except SyntaxError as e:
        return False, f"第 {e.lineno} 行: {e.msg}"

def ask_deepseek_to_fix(file_path: str, error_msg: str, original_code: str) -> str:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""你是一个 Python 代码修复专家。下面的文件存在语法错误，请根据错误信息修复它，并返回完整的修复后代码。
文件路径：{file_path}
错误信息：{error_msg}

要求：
1. 只返回修复后的 Python 代码，不要任何解释或 markdown 标记。
2. 保持原有功能不变，只修复语法错误。
3. 如果错误是因为缺少 `from pathlib import Path`，请在文件开头添加该导入。
4. 如果错误是因为 `PROJECT_ROOT` 未定义，请添加正确的定义（根据文件所在目录层级计算，例如 `PROJECT_ROOT = Path(__file__).resolve().parent.parent`）。
5. 修正缩进、括号、三引号等问题。
6. 确保修复后的代码能够成功编译。

原始代码：
```python
{original_code}
```"""
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=90)
        if resp.status_code == 200:
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
            if "```python" in reply:
                reply = reply.split("```python", 1)[1].split("```", 1)[0].strip()
            elif "```" in reply:
                reply = reply.split("```", 1)[1].split("```", 1)[0].strip()
            return reply
        else:
            print(f"    ❌ API 状态码 {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        print(f"    ❌ 网络错误: {e}")
        return None

def repair_core_files():
    """只扫描核心目录下的文件，修复语法错误"""
    round_num = 0
    total_fixed = 0
    while round_num < MAX_ROUNDS:
        round_num += 1
        errors_found = 0
        print(f"\n{'='*40}\n🔍 第 {round_num} 轮扫描核心文件...")
        for core_dir in CORE_DIRS:
            root_dir = PROJECT_ROOT / core_dir
            if not root_dir.exists():
                continue
            for file in root_dir.rglob("*.py"):
                # 跳过 __pycache__ 等
                if any(part.startswith("__") or part in EXCLUDE_DIRS for part in file.parts):
                    continue
                file_path = file
                if str(file_path) in FAILED_FILES:
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    ok, err = check_syntax(content, str(file_path))
                except Exception as e:
                    err = f"读取异常: {e}"
                    ok = False
                if not ok:
                    errors_found += 1
                    rel_path = file_path.relative_to(PROJECT_ROOT)
                    print(f"  ❌ {rel_path} : {err}")
                    print("     🧠 请求 AI 修复...")
                    fixed = ask_deepseek_to_fix(str(file_path), err, content)
                    if fixed:
                        ok_fixed, new_err = check_syntax(fixed, str(file_path))
                        if ok_fixed:
                            bak = file_path.with_suffix(file_path.suffix + ".bak")
                            shutil.copy2(file_path, bak)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(fixed)
                            print("     ✅ 修复成功")
                            total_fixed += 1
                            FAILED_FILES.discard(str(file_path))
                        else:
                            print(f"     ❌ AI 修复后仍有错误: {new_err}，标记为跳过")
                            FAILED_FILES.add(str(file_path))
                    else:
                        print("     ❌ AI 未返回有效代码，标记为跳过")
                        FAILED_FILES.add(str(file_path))
        if errors_found == 0:
            return True
        if len(FAILED_FILES) >= errors_found and errors_found > 0:
            print("⚠️ 所有剩余错误均无法自动修复，停止循环。")
            break
        time.sleep(1)
    return False

# ─── 集成到 main.py ───
def integrate_to_main():
    main_py = PROJECT_ROOT / "main.py"
    if not main_py.exists():
        print("❌ main.py 不存在")
        return
    with open(main_py, "r", encoding="utf-8") as f:
        content = f.read()
    if "auto_repair_v3" in content:
        print("✅ 已集成 auto_repair")
        return
    # 在 import 语句之后插入启动检查
    insert_code = """
# === 自动修补检查 ===
import os, sys, time
from pathlib import Path
try:
    from auto_repair_v3 import clean_temp_files, repair_core_files
    print("🔧 正在执行启动前修补...")
    clean_temp_files()
    repair_core_files()
    print("✅ 修补检查完成")
except Exception as e:
    print(f"⚠️ 修补器运行失败: {e}")
# ===================
"""
    lines = content.split("\n")
    # 寻找最后一个 import 行的位置
    last_import = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import = i
    lines.insert(last_import + 1, insert_code)
    new_content = "\n".join(lines)
    shutil.copy2(main_py, main_py.with_suffix(".bak"))
    with open(main_py, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("✅ auto_repair 已绑定到 main.py，每次启动自动运行。")

# ─── 主流程 ───
if __name__ == "__main__":
        print("❌ 请先在 auto_repair_v3.py 中填入有效的 DeepSeek API Key！")
        sys.exit(1)
    print("🚀 LightAgent 智能修补器 V3 启动")
    # 第一步：删除所有干扰文件
    deleted = clean_temp_files()
    print(f"✅ 共删除 {deleted} 个干扰文件")
    # 第二步：修复核心文件
    success = repair_core_files()
    # 第三步：集成
    integrate_to_main()
    if success:
        print("\n🎉 所有核心文件语法正确，项目已稳定！")
    else:
        print("\n⚠️ 修复完成，但以下文件仍存在错误（需手动处理）：")
        for f in FAILED_FILES:
            print(f"   - {f}")
    print("请运行 python main.py 启动 LightAgent。")
