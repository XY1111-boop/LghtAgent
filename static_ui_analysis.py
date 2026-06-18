# static_ui_analysis.py —— 基于代码的 LightAgent UI 评估与生态系统建议
import os, sys, time, json, datetime, shutil, re
from pathlib import Path
import yaml, requests

# ╔══════════════════════════════════════════════════════════════╗
# ║  🔑 在这里填写你的 DeepSeek API Key（必填）                ║
# ║  或者留空，脚本会自动从 config.yaml 中读取                 ║
# ╚══════════════════════════════════════════════════════════════╝

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
DESKTOP = Path.home() / "Desktop"
REPORT_FILE = DESKTOP / "LightAgent_UI_Code_Review.txt"

# 颜色输出
class Colors:
    OK = '\033[92m'; WARN = '\033[93m'; FAIL = '\033[91m'; ENDC = '\033[0m'

def log(msg, level="INFO", logfile=REPORT_FILE):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"[{now}] [{level}] {msg}"
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    color = Colors.OK if level == "INFO" else Colors.WARN if level == "WARNING" else Colors.FAIL
    print(f"{color}{text}{Colors.ENDC}")

def get_api_key():
        return DEEPSEEK_API_KEY
    cfg = PROJECT_ROOT / "config.yaml"
    if cfg.exists():
        with open(cfg, "r", encoding="utf-8") as f:
            conf = yaml.safe_load(f)
        key = conf.get("api_key", "")
            return key
    return None

def call_deepseek(prompt, max_tokens=2000, temperature=0.3):
    api_key = get_api_key()
    if not api_key:
        return "❌ 未配置 API Key"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            log(f"API 错误: {resp.status_code}", "ERROR")
            return None
    except Exception as e:
        log(f"API 调用异常: {e}", "ERROR")
        return None

# ─── 步骤1：语法扫描与修复（可选）───
def syntax_scan_and_fix():
    log("========== 语法扫描（预处理） ==========")
    py_files = list(PROJECT_ROOT.rglob("*.py"))
    fixed_count = 0
    for fp in py_files:
        if "__pycache__" in str(fp):
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                code = f.read()
            compile(code, str(fp), "exec")
        except SyntaxError as e:
            log(f"语法错误: {fp.relative_to(PROJECT_ROOT)} - {e}", "WARNING")
            prompt = f"""你是 Python 修复专家。请修复以下文件的语法错误。
文件名: {fp.name}
错误: {e}
要求只返回完整正确代码，不要解释。
原始代码:
{code}"""
            fixed = call_deepseek(prompt, max_tokens=len(code)//4+800)
            if fixed and fixed != code:
                shutil.copy2(fp, str(fp)+".bak")
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(fixed)
                log(f"✅ 已修复: {fp.relative_to(PROJECT_ROOT)}")
                fixed_count += 1
            else:
                log(f"❌ 未能修复: {fp.relative_to(PROJECT_ROOT)}")
    return fixed_count

# ─── 步骤2：收集 UI 代码 ─────
def collect_ui_code():
    ui_dir = PROJECT_ROOT / "ui"
    code_snippets = []
    if ui_dir.exists():
        for py_file in ui_dir.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    code = f.read()
                # 仅保留前2000字符，避免 token 溢出
                snippet = f"===== {py_file.relative_to(PROJECT_ROOT)} =====\n{code[:2000]}\n"
                code_snippets.append(snippet)
            except:
                pass
    return "\n".join(code_snippets)

# ─── 步骤3：生成 UI 分析与生态建议 ─────
def generate_ui_report(ui_code):
    log("正在请求 DeepSeek 分析 UI 代码...")
    prompt = f"""你是一位资深的 Python + PyQt5 UI/UX 设计专家和 AI 系统架构师。请仔细分析下面的 LightAgent 桌面应用 UI 代码（所有标签页，包括控制台、浏览器、工作流、进化看板、学习中心、监控、记忆库、聊天室、训练中心等）。

请从以下维度给出详细的评估报告（中文，使用清晰的标题分隔）：
1. **整体布局与导航**：标签页组织是否合理？菜单栏、工具栏设计如何？
2. **控件使用与样式**：按钮、输入框、表格、文本框等是否一致？颜色、字体、间距是否美观？
3. **交互逻辑**：各组件之间信号/槽连接是否正确？是否存在阻塞 UI 线程的操作？
4. **缺陷与风险**：指出可能出现的界面卡顿、内存泄漏、跨线程操作等隐患。
5. **改进建议**：至少给出 8 条具体可操作的建议，按优先级排序。
6. **生态系统构建建议**：基于该项目的现有功能（本地 LLM、安全沙箱、进化系统、虚拟主播等），推荐可以扩展的外部设备（如 USB 传感器、摄像头）、软件集成（如智能家居平台、IDE 插件）、盈利模式（如订阅制、企业版）等。
7. **最终评分**：对 UI 整体质量打分（满分 10 分）。

以下是项目的 UI 核心代码片段：
{ui_code[:8000]}

请直接给出报告内容，不需要额外的客套话。"""
    return call_deepseek(prompt, max_tokens=2500)

# ─── 主流程 ────────────────────────────────
def main():
    log("🚀 LightAgent 静态 UI 分析与生态规划启动")
    # 1. 语法预处理
    fixed = syntax_scan_and_fix()
    log(f"语法修复完成，共修复 {fixed} 个文件")
    # 2. 收集 UI 代码
    ui_code = collect_ui_code()
    if not ui_code:
        log("未找到 UI 代码，无法分析", "ERROR")
        return
    # 3. 生成报告
    report = generate_ui_report(ui_code)
    if report:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(report)
        log("✅ UI 分析与生态系统建议已生成")
        print(f"📄 报告位置：{REPORT_FILE}")
    else:
        log("❌ 报告生成失败", "ERROR")

if __name__ == "__main__":
    main()
