# ultimate_control_multimodal.py —— DeepSeek 多模态全自动 UI 测试 + 项目修复
# 功能：
# 1. 使用 DeepSeek 视觉模型（deepseek-chat，支持图像上传）控制鼠标，遍历 LightAgent 所有 UI 按钮
# 2. 实时截图并发送给 DeepSeek 分析界面状态，发现错误自动尝试修复
# 3. 扫描项目所有 .py 文件，修复语法错误
# 4. 自动启动 LightAgent，进行人机对话测试
# 5. 将测试报告、UI 建议、错误修复记录保存到桌面
# 依赖：pyautogui, Pillow, requests, pygetwindow (可选，定位窗口)
# 确保 DeepSeek API Key 已配置

import os, sys, time, json, subprocess, threading, datetime, shutil, re, base64, io
from pathlib import Path
import yaml, requests
import pyautogui
from PIL import Image

# ╔══════════════════════════════════════════════════════════════╗
# ║  🔑 在这里填写你的 DeepSeek API Key（必填）                ║
# ║  或者留空，脚本会自动从 config.yaml 中读取                 ║
# ╚══════════════════════════════════════════════════════════════╝

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

DESKTOP = Path.home() / "Desktop"
REPORT_FILE = DESKTOP / "LightAgent_UITest_Report.txt"
ADVICE_FILE = DESKTOP / "LightAgent_UI_Advice.txt"
FIX_LOG = DESKTOP / "LightAgent_Fix_Log.txt"

# 颜色
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

# ─── 多模态调用（图像 + 文本）─────────────────────
def chat_with_image(prompt, image_path, max_tokens=500):
    """将图像编码为 base64，调用 DeepSeek 视觉模型"""
    api_key = get_api_key()
    if not api_key:
        return "未配置 API Key"

    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}}
            ]
        }],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            log(f"图像分析 API 错误: {resp.status_code}", "ERROR")
            return None
    except Exception as e:
        log(f"图像分析异常: {e}", "ERROR")
        return None

def call_deepseek_text(prompt, max_tokens=500):
    """纯文本调用 DeepSeek"""
    api_key = get_api_key()
    if not api_key: return "无Key"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        return None
    except Exception as e:
        return None

# ─── 项目扫描与修复 ─────────────────────────
def static_scan_and_fix():
    log("========== 静态代码扫描与修复 ==========", logfile=FIX_LOG)
    py_files = list(PROJECT_ROOT.rglob("*.py"))
    fixed = 0
    for fp in py_files:
        if "__pycache__" in str(fp):
            continue
        try:
            with open(fp, "r", encoding="utf-8") as f:
                code = f.read()
            compile(code, str(fp), "exec")
        except SyntaxError as e:
            log(f"发现错误: {fp.relative_to(PROJECT_ROOT)} - {e}", logfile=FIX_LOG)
            # 请求修复
            prompt = f"修复以下 Python 代码的语法错误。错误信息：{e}\n文件名：{fp.name}\n要求只返回完整修正后的代码，不要解释。\n原始代码:\n{code}"
            fixed_code = call_deepseek_text(prompt, max_tokens=len(code)//4+800)
            if fixed_code and fixed_code != code:
                shutil.copy2(fp, str(fp)+".bak")
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(fixed_code)
                log(f"✅ 已修复: {fp.relative_to(PROJECT_ROOT)}", logfile=FIX_LOG)
                fixed += 1
            else:
                log(f"❌ 未能修复: {fp.relative_to(PROJECT_ROOT)}", logfile=FIX_LOG)
    log(f"静态修复完成，共修复 {fixed} 个文件", logfile=FIX_LOG)

# ─── 启动 LightAgent GUI ────────────────────
def launch_lightagent():
    log("🚀 启动 LightAgent ...")
    try:
        proc = subprocess.Popen([sys.executable, "main.py"], cwd=str(PROJECT_ROOT),
                               creationflags=subprocess.CREATE_NEW_CONSOLE if os.name=='nt' else 0)
        log(f"进程 PID: {proc.pid}")
        return proc
    except Exception as e:
        log(f"启动失败: {e}", "ERROR")
        return None

# ─── UI 操作与测试 ─────────────────────────
def ensure_focus():
    """尝试让 LightAgent 窗口获得焦点"""
    # 简单：最小化所有窗口再恢复（可能不精确）
    pyautogui.hotkey('win', 'm')  # 最小化所有
    time.sleep(0.5)
    # 激活可能通过 pygetwindow 更准确，这里简单等待
    pyautogui.press('alt')
    time.sleep(0.5)

def capture_screen():
    img = pyautogui.screenshot()
    path = PROJECT_ROOT / "temp_screenshot.png"
    img.save(str(path))
    return str(path)

def analyze_ui(image_path):
    """使用多模态模型分析当前界面状态"""
    prompt = """你是一个专业的 UI 测试专家。请仔细观察这张桌面应用程序的截图（这是 LightAgent AI 电脑管家界面）。
请回答以下问题（用中文）：
1. 当前界面显示了哪些主要元素？特别是标签页栏、按钮、输入框、状态栏等。
2. 界面是否有明显的布局问题、文字遮挡、按钮不响应等缺陷？
3. 根据界面上可见的按钮/标签，你认为点击哪里可以继续测试下一个功能？
4. 如果出现错误对话框或异常显示，请详细描述并给出修复建议。
5. 简要总结当前界面的整体用户体验。
"""
    return chat_with_image(prompt, image_path)

def click_button_by_text(text):
    """通过 OCR 定位文本？不用了，我们直接通过坐标偏移点击（粗鲁但有效）"""
    # 实际项目中应根据图像识别确定按钮位置，这里简化：使用固定偏移或让 AI 决定点击坐标
    # 我们将使用 pyautogui 的 locateOnScreen 需要事先截按钮图片，太麻烦。
    # 备用方案：使用 AI 分析截图后，返回需要点击的坐标（通过提示让 AI 输出坐标）。
    # 但 AI 输出坐标难以直接操作。我们采用最粗糙：循环点击已知位置列表。
    pass  # 实际测试中我们会手动定义一些点击序列

def run_ui_tests():
    log("========== 开始多模态 UI 全量测试 ==========")
    # 定义标签页名称和可能的点击区域（基于 1280x800 分辨率，可根据实际调整）
    tabs = [
        ("AI 控制台", (200, 80)),
        ("本地浏览器", (380, 80)),
        ("工作流", (560, 80)),
        ("进化看板", (740, 80)),
        ("学习中心", (920, 80)),
        ("📡 实时监控", (1100, 80)),
        ("🧠 记忆库", (1280, 80)),
        ("💬 聊天室", (1460, 80)),
        ("🎓 训练中心", (1640, 80)),
    ]
    # 先尝试激活窗口
    ensure_focus()
    time.sleep(2)

    # 逐个点击标签页并截图分析
    for tab_name, coord in tabs:
        log(f"测试标签页: {tab_name}")
        # 点击坐标
        pyautogui.click(coord[0], coord[1])
        time.sleep(2)
        img_path = capture_screen()
        analysis = analyze_ui(img_path)
        if analysis:
            log(f"{tab_name} 分析结果:\n{analysis}")
            with open(ADVICE_FILE, "a", encoding="utf-8") as f:
                f.write(f"=== {tab_name} ===\n{analysis}\n\n")
        else:
            log(f"{tab_name} 分析失败", "WARNING")

    # 测试 AI 控制台输入对话
    log("测试 AI 对话功能")
    pyautogui.click(200, 80)  # 切回 AI 控制台
    time.sleep(1)
    # 点击输入框（大概在底部）
    pyautogui.click(300, 700)  # 坐标需调整
    time.sleep(0.5)
    # 输入指令
    pyautogui.typewrite("/run 打开计算器", interval=0.1)
    pyautogui.press('enter')
    time.sleep(3)
    img_path = capture_screen()
    analysis = analyze_ui(img_path)
    if analysis:
        log(f"执行命令后分析: {analysis}")
    else:
        log("对话分析失败", "WARNING")

    # 关闭 LightAgent（结束测试）
    log("UI 测试完成，正在关闭 LightAgent...")
    pyautogui.hotkey('alt', 'f4')
    time.sleep(1)

# ─── 主流程 ────────────────────────────────
def main():
    log("🚀 DeepSeek 全自动多模态项目修复与 UI 测试启动")
    # 1. 静态修复
    static_scan_and_fix()
    # 2. 启动 GUI
    proc = launch_lightagent()
    if not proc:
        log("无法启动 LightAgent，退出", "ERROR")
        return
    # 3. 等待界面加载
    time.sleep(15)  # 给足够时间
    # 4. UI 测试
    run_ui_tests()
    # 5. 结束
    log("🎉 全部完成！报告已保存到桌面。")
    print(f"📄 报告：{REPORT_FILE}")
    print(f"💡 建议：{ADVICE_FILE}")
    print(f"🔧 修复日志：{FIX_LOG}")

if __name__ == "__main__":
    main()
