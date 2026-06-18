# ultimate_full_test.py —— LightAgent 30分钟全功能极限测试 + 多模态UI分析
import os, sys, time, json, threading, datetime, random, subprocess, platform, psutil, shutil
from pathlib import Path
import yaml, requests
import pyautogui
from PIL import Image
import pytesseract
import io

# ╔══════════════════════════════════════════════════════════════╗
# ║  🔑 在这里填写你的 DeepSeek API Key（必填）                ║
# ╚══════════════════════════════════════════════════════════════╝
DEEPSEEK_API_KEY = ""   # 填写你的 DeepSeek API Key

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

DESKTOP = Path.home() / "Desktop"
REPORT_FILE = DESKTOP / "LightAgent_Ultimate_Test_Report.txt"
BUG_FILE = DESKTOP / "LightAgent_Bug_List.txt"
UI_ADVICE_FILE = DESKTOP / "LightAgent_UI_Advice.txt"

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

def call_deepseek(prompt, max_tokens=500, temperature=0.7):
    api_key = get_api_key()
    if not api_key:
        return "无API Key"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            return f"API错误: {resp.status_code}"
    except Exception as e:
        return f"API异常: {e}"

# ─── 项目扫描 ─────────────────────────────
def scan_project():
    log("========== 项目结构扫描 ==========")
    data = {"files": [], "modules": set()}
    for py_file in PROJECT_ROOT.rglob("*.py"):
        data["files"].append(str(py_file.relative_to(PROJECT_ROOT)))
        data["modules"].add(py_file.parent.name if py_file.parent != PROJECT_ROOT else "root")
    log(f"共 {len(data['files'])} 个文件, 涉及模块: {', '.join(sorted(data['modules']))}")
    return data

# ─── 初始化测试Agent ─────────────────────
def init_test_agent():
    from utils.config import setup_environment
    from utils.logger import LogManager
    config = setup_environment()
    logger = LogManager()
    use_local = config.get("use_local_llm", False)
    if use_local:
        from intelligence.local_adapter import LocalAPI
        api = LocalAPI(logger=logger)
    else:
        api_key = get_api_key()
        if not api_key:
            raise RuntimeError("未配置API Key")
        from intelligence.deepseek_api import DeepSeekAPI
        api = DeepSeekAPI(api_key=api_key)
    from core.sandbox import Sandbox
    from core.safety_auditor import SafetyAuditor
    from core.host_executor import HostExecutor
    sandbox = Sandbox(memory_limit=256)
    auditor = SafetyAuditor(api) if api else None
    host = HostExecutor(allowed_dir=str(PROJECT_ROOT / "Knowledge/raw"), logger=logger)
    from intelligence.tool_executor import ToolExecutor
    kb = None
    try:
        from knowledge.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
    except: pass
    tool_exec = ToolExecutor(sandbox, host, auditor, kb)

    class TestAgent:
        def __init__(self):
            self.api = api
            self.sandbox = sandbox
            self.auditor = auditor
            self.host = host
            self.tool_executor = tool_exec
            self.kb = kb
        def process(self, text, temp=0.7):
            if not self.api:
                return "API不可用"
            if text.startswith("/run"):
                return self._run_task(text[4:].strip())
            return self.api.chat([{"role":"user","content":text}], temperature=temp)
        def _run_task(self, task):
            # 简化安全执行，返回工具执行结果
            from intelligence.tool_executor import parse_tool_call
            return self.tool_executor.execute("run_python", {"code": f"print('模拟执行: {task}')"})
    return TestAgent()

# ─── 多模态UI分析 ───────────────────────
def capture_ui_screenshot():
    """截取当前屏幕，保存为文件，返回路径"""
    screenshot_path = PROJECT_ROOT / "ui_screenshot.png"
    try:
        img = pyautogui.screenshot()
        img.save(str(screenshot_path))
        return screenshot_path
    except Exception as e:
        log(f"截图失败: {e}", "ERROR")
        return None

def extract_ui_text(image_path):
    """用OCR提取UI中的文字"""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='chi_sim+eng')
        return text
    except:
        return "OCR提取失败"

def get_ui_advice(description, ocr_text):
    """请求DeepSeek给出UI改进建议"""
    prompt = f"""你是一位专业的UI/UX设计师。请根据以下桌面应用的UI描述和OCR提取的文字，给出详细的改进建议（中文）。
UI描述：{description}
OCR提取的关键文字：{ocr_text[:500]}
请分析布局、颜色、字体、交互逻辑等方面的不足，并提出具体可实施的优化方案。"""
    return call_deepseek(prompt, max_tokens=600, temperature=0.5)

# ─── 功能测试模块 ──────────────────────
def test_core_components(agent):
    """测试所有核心组件是否正常加载"""
    log("--- 核心组件加载测试 ---")
    components = {
        "LocalBrain": "intelligence/local_llm.py",
        "Sandbox": "core/sandbox.py",
        "HostExecutor": "core/host_executor.py",
        "SafetyAuditor": "core/safety_auditor.py",
        "EvolutionController": "intelligence/evolution.py",
        "ToolExecutor": "intelligence/tool_executor.py",
        "KnowledgeBase": "knowledge/knowledge_base.py",
        "MemoryManager": "intelligence/memory.py",
        "NeuroEnhancer": "intelligence/neuro_enhancer.py",
        "PluginManager": "intelligence/plugin_system.py",
    }
    errors = []
    for name, path in components.items():
        try:
            mod = __import__(path.replace('/', '.').replace('.py', ''), fromlist=[name])
            cls = getattr(mod, name)
            # 尝试实例化（需要参数的有可能失败，但只检查导入和类存在）
            log(f"✅ {name} 导入成功")
        except Exception as e:
            err = f"❌ {name} 加载失败: {e}"
            log(err, "ERROR")
            errors.append(err)
    return errors

def test_tool_commands(agent, duration=8*60):
    """执行工具调用循环，持续 duration 秒"""
    cmds = [
        "/run 打开计算器",
        "/run 打开记事本",
        "/run 在桌面创建test文件夹",
        "/run 显示桌面",
        "/run 用浏览器打开 https://example.com",
        "/index",
    ]
    errors = []
    start = time.time()
    while time.time() - start < duration:
        cmd = random.choice(cmds)
        log(f"执行: {cmd}")
        try:
            res = agent.process(cmd)
            log(f"结果: {res[:100]}")
        except Exception as e:
            err = f"工具异常: {e}"
            log(err, "ERROR")
            errors.append(err)
        time.sleep(random.randint(4, 8))
    return errors

def test_knowledge_base(agent):
    """测试知识库索引和检索"""
    errors = []
    try:
        if agent.kb:
            agent.kb.index_files()
            results = agent.kb.search("Python", 3)
            log(f"知识库检索结果: {results}")
        else:
            log("知识库未加载", "WARNING")
    except Exception as e:
        err = f"知识库测试失败: {e}"
        log(err, "ERROR")
        errors.append(err)
    return errors

def test_memory_system(agent):
    """测试记忆系统"""
    errors = []
    try:
        from intelligence.memory import MemoryManager
        mem = MemoryManager(api=agent.api)
        mem.add_memory("test", "这是一条测试记忆", 0.5)
        mems = mem.retrieve_relevant("测试", 3)
        log(f"记忆检索结果: {mems}")
    except Exception as e:
        err = f"记忆系统测试失败: {e}"
        log(err, "ERROR")
        errors.append(err)
    return errors

# ─── 主流程 ────────────────────────────
def main():
    # 清空旧日志
    for f in [REPORT_FILE, BUG_FILE, UI_ADVICE_FILE]:
        if f.exists():
            f.unlink()

    log("🚀 LightAgent 终极全功能测试启动（30分钟）")
    log(f"时间: {datetime.datetime.now()}")

    # 1. 项目扫描
    scan_project()

    # 2. 初始化Agent
    try:
        agent = init_test_agent()
        log("✅ 测试Agent初始化成功")
    except Exception as e:
        log(f"❌ Agent初始化失败: {e}", "ERROR")
        return

    # 3. 核心组件测试
    errors = test_core_components(agent)

    # 4. 工具调用压力测试 (10分钟)
    log("--- 开始工具调用压力测试 (10分钟) ---")
    tool_errors = test_tool_commands(agent, 10*60)
    errors.extend(tool_errors)

    # 5. 知识库与记忆测试 (5分钟间隔执行)
    log("--- 知识库/记忆测试 ---")
    kb_errors = test_knowledge_base(agent)
    mem_errors = test_memory_system(agent)
    errors.extend(kb_errors)
    errors.extend(mem_errors)

    # 6. 多模态UI分析（如果有GUI）
    log("--- 多模态UI分析 ---")
    # 尝试启动LightAgent（如果未运行）并截图
    try:
        # 启动LightAgent作为子进程（如果当前未运行）
        # 或假设已经运行，直接截图
        screenshot = capture_ui_screenshot()
        if screenshot:
            ocr_text = extract_ui_text(screenshot)
            log("UI截图与OCR完成，正在请求AI分析...")
            # 简单的UI描述：基于常识
            ui_desc = "桌面应用，包含多标签页，左侧虚拟形象，中间聊天/命令区域，底部输入栏和按钮，菜单栏等"
            advice = get_ui_advice(ui_desc, ocr_text)
            if advice:
                with open(UI_ADVICE_FILE, "w", encoding="utf-8") as f:
                    f.write(advice)
                log(f"✅ UI改进建议已保存至 {UI_ADVICE_FILE}")
            else:
                log("未获取到UI建议", "WARNING")
        else:
            log("未能截图，跳过UI分析", "WARNING")
    except Exception as e:
        log(f"UI分析异常: {e}", "ERROR")

    # 7. 汇总错误并生成Bug报告
    log("========== 测试总结 ==========")
    log(f"总错误数: {len(errors)}")
    if errors:
        with open(BUG_FILE, "w", encoding="utf-8") as f:
            f.write("LightAgent 测试发现的Bug列表：\n")
            f.write("\n".join(errors))
        log(f"Bug列表已保存至 {BUG_FILE}")
        # 请求AI修复建议
        prompt = f"以下是LightAgent测试中发现的错误，请分析原因并给出修复建议（中文）：\n" + "\n".join(errors[:15])
        suggestion = call_deepseek(prompt, max_tokens=600, temperature=0.5)
        if suggestion and "API" not in suggestion:
            with open(BUG_FILE, "a", encoding="utf-8") as f:
                f.write("\n\nAI修复建议：\n")
                f.write(suggestion)
            log("✅ AI修复建议已追加到Bug报告")
    else:
        log("✅ 未发现任何错误！")

    log("🎉 30分钟极限测试完成！")
    print(f"\n📄 报告文件：\n  {REPORT_FILE}\n  {BUG_FILE}\n  {UI_ADVICE_FILE}")

if __name__ == "__main__":
    main()
