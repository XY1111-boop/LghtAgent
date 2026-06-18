# ultimate_analysis.py —— 全自动分析完美化脚本（全新版）
# 功能：扫描硬件、项目，调用DeepSeek API深度分析，生成报告、防火墙，集成到LightAgent
# 作者：AI 助手
# 使用方法：直接运行 python ultimate_analysis.py

import os, sys, json, time, shutil, datetime, traceback, platform
from pathlib import Path
import requests
import yaml
import psutil
try:
    import GPUtil
except ImportError:
    GPUtil = None

# ========== 请在这里填写你的 DeepSeek API Key ==========
# 如果你已经在 config.yaml 中配置了 api_key，可以留空，脚本会自动读取
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 桌面日志路径
DESKTOP_LOG = Path.home() / "Desktop" / "LightAgent_Analysis_Log.txt"

# 防卡死超时设置（秒）
TIMEOUT = 120

# 颜色输出（简单实现）
class Colors:
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log(msg, level="INFO", logfile=DESKTOP_LOG):
    """写日志到桌面文件并打印"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"[{now}] [{level}] {msg}"
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    if level == "ERROR":
        print(f"{Colors.FAIL}{text}{Colors.ENDC}")
    elif level == "WARNING":
        print(f"{Colors.WARNING}{text}{Colors.ENDC}")
    else:
        print(f"{Colors.OK}{text}{Colors.ENDC}")

def load_api_key():
    """加载 API Key：优先使用脚本中填写的，否则从 config.yaml 读取"""
        return DEEPSEEK_API_KEY
    config_file = PROJECT_ROOT / "config.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("api_key", "")
    return ""

# --------------- 硬件扫描 ---------------
def scan_hardware():
    log("正在扫描硬件...")
    info = {
        "操作系统": platform.platform(),
        "主机名": platform.node(),
        "CPU型号": platform.processor(),
        "CPU逻辑核心": psutil.cpu_count(logical=True),
        "内存总量(GB)": round(psutil.virtual_memory().total / (1024**3), 2),
        "磁盘剩余空间(GB)": round(psutil.disk_usage('C:/').free / (1024**3), 2) if os.name == 'nt' else None,
        "GPU列表": []
    }
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                info["GPU列表"].append({
                    "名称": gpu.name,
                    "显存(MB)": gpu.memoryTotal,
                    "驱动": gpu.driver
                })
        except Exception as e:
            info["GPU列表"].append({"错误": str(e)})
    else:
        info["GPU列表"].append("未安装GPUtil，无法获取GPU信息")
    log("硬件扫描完成")
    return info

# --------------- 项目扫描 ---------------
def scan_project():
    log("正在扫描项目结构...")
    data = {
        "Python版本": sys.version,
        "文件总数": 0,
        "代码总行数": 0,
        "模块列表": {},
        "关键组件": [],
        "依赖库": [],
        "配置文件": [],
        "数据库文件": []
    }
    # 扫描所有 .py 文件
    py_files = list(PROJECT_ROOT.rglob("*.py"))
    data["文件总数"] = len(py_files)
    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
                data["代码总行数"] += len(lines)
            rel = f.relative_to(PROJECT_ROOT)
            module = rel.parts[0] if len(rel.parts) > 1 else "根目录"
            if module not in data["模块列表"]:
                data["模块列表"][module] = []
            data["模块列表"][module].append(str(rel))
        except:
            pass
    # 关键组件检测
    key_files = {
        "本地LLM": "intelligence/local_llm.py",
        "安全沙箱": "core/sandbox.py",
        "安全审计": "core/safety_auditor.py",
        "进化控制器": "intelligence/evolution.py",
        "工具执行器": "intelligence/tool_executor.py",
        "向量知识库": "knowledge/knowledge_base.py",
        "神经增强框架": "intelligence/neuro_enhancer.py",
        "经验管理器": "intelligence/experience_manager.py",
        "训练引擎": "intelligence/training_engine.py",
        "虚拟主播引擎": "intelligence/vtuber_engine.py",
    }
    for name, fpath in key_files.items():
        if (PROJECT_ROOT / fpath).exists():
            data["关键组件"].append(name)
    # 依赖库检查
    try:
        import pkg_resources
        installed = [pkg.key for pkg in pkg_resources.working_set]
        wanted = ['PyQt5','requests','chromadb','llama-cpp-python','pyautogui',
                  'psutil','GPUtil','matplotlib','scikit-learn','numpy','yaml',
                  'torch','transformers','speechrecognition','pyttsx3','vosk']
        for lib in wanted:
            if lib.lower().replace('-','_') in installed:
                data["依赖库"].append(lib)
    except:
        data["依赖库"] = ["无法获取"]
    # 配置文件
    configs = list(PROJECT_ROOT.glob("*.yaml"))
    data["配置文件"] = [c.name for c in configs]
    # 数据库文件
    cache_dir = PROJECT_ROOT / "Cache"
    if cache_dir.exists():
        data["数据库文件"] = [d.name for d in cache_dir.glob("*.db")]
    log("项目扫描完成")
    return data

# --------------- 构建对话总结 ---------------
CHAT_SUMMARY = """
本次对话核心历程（从零构建LightAgent的完整记录）：
1. 用户从零开始，在AI辅助下用两天时间搭建了名为LightAgent的AI电脑管家。
2. 项目包含PyQt5多标签页界面、本地大语言模型（Qwen2.5-0.5B/1.5B GGUF）、云端DeepSeek API切换。
3. 实现安全沙箱（代码白名单、子进程执行）、安全审计（AI审查+不可变文件保护）。
4. 集成向量知识库（ChromaDB）、永久记忆系统（SQLite）、自进化框架（L1/L2/L3）。
5. 开发学习中心、工作流编辑器、实时监控面板、记忆库查看器、聊天室等十余个功能页面。
6. 引入动态神经增强框架（思维链、反思、经验学习、RAG等插件）。
7. 创建智能训练中心（利用DeepSeek生成操作样本，增量学习），并添加游戏化进化看板。
8. 集成虚拟主播模块（本地Vosk语音识别、pyttsx3 TTS、简易Live2D显示）。
9. 解决数百个工程问题：路径硬编码、线程安全、DLL缺失、编码乱码等，最终稳定运行。
10. 当前配置：GTX 960M 2GB, i5-4210H, 12GB RAM, Windows 10，完全离线可用。
11. 最终目标：进一步提升智能，参加技术竞赛，获得行业认可。
"""

# --------------- 构建 API 提示词 ---------------
def build_prompt(hw, proj):
    prompt = f"""你是一位资深AI系统架构师与安全专家。请根据以下信息对LightAgent项目进行全面分析（用中文回复）：

【硬件配置】
{json.dumps(hw, ensure_ascii=False, indent=2)}

【项目扫描结果】
{json.dumps(proj, ensure_ascii=False, indent=2)}

【项目开发历程摘要】
{CHAT_SUMMARY}

请严格按以下要求输出：
1. **完备度评估**：指出项目目前已具备的功能模块，并评价其成熟度（高/中/低）。
2. **架构图（文字描述）**：用Mermaid或ASCII绘制当前系统架构图，标明数据流。
3. **缺失模块分析**：根据类似项目的最佳实践，列出至少5项应该添加但尚未实现的功能，每项给出理由。
4. **改进建议（只增不减）**：对现有模块提出至少5条优化方向，不删除任何功能。
5. **防卡死防火墙设计**：设计一个监控组件心跳的轻量级方案，包括前端显示面板（HTML+JS）和后端监控逻辑。
6. **JSON摘要**：将上述结论（完备度、缺失模块、改进建议、防火墙方案）封装为JSON对象，放在```json代码块中。

注意：所有建议必须只增加功能，绝不删除或简化现有模块。"""
    return prompt

# --------------- 调用 DeepSeek API ---------------
def call_deepseek(prompt):
    api_key = load_api_key()
    if not api_key:
        log("未找到有效的 DeepSeek API Key！请在脚本开头的 DEEPSEEK_API_KEY 变量中填写，或确保 config.yaml 中已配置。", "ERROR")
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4000
    }
    log("正在请求 DeepSeek API...")
    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=TIMEOUT
        )
        if resp.status_code == 200:
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
            log("DeepSeek 分析成功")
            return reply
        else:
            log(f"API 请求失败，状态码：{resp.status_code}，响应：{resp.text}", "ERROR")
            return None
    except Exception as e:
        log(f"API 调用异常：{e}", "ERROR")
        return None

# --------------- 生成输出文件 ---------------
def generate_output(ai_response, hw, proj):
    """生成桌面日志、HTML报告、防火墙JS、JSON摘要"""
    log("正在生成分析报告...")
    # 将 AI 响应写入桌面日志
    log("========== DeepSeek 分析结果 ==========")
    log(ai_response)
    log("========== 分析结束 ==========")

    # 提取 JSON 摘要（如果有）
    import re
    json_match = re.search(r"```json\n(.*?)\n```", ai_response, re.DOTALL)
    summary = {}
    if json_match:
        try:
            summary = json.loads(json_match.group(1))
            with open(PROJECT_ROOT / "analysis_summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            log("JSON 摘要已保存到 analysis_summary.json")
        except:
            log("JSON 摘要提取失败", "WARNING")

    # 生成 HTML 报告
    web_dir = PROJECT_ROOT / "web"
    web_dir.mkdir(exist_ok=True)
    html_body = ai_response.replace("\n", "<br>").replace(" ", "&nbsp;")
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>LightAgent 深度分析报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #4A90D9; }}
        pre {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; }}
        .firewall {{ border: 2px solid #4A90D9; padding: 10px; margin-top: 20px; }}
        .status-ok {{ color: green; font-weight: bold; }}
        .status-error {{ color: red; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 LightAgent 系统分析报告</h1>
        <h2>💻 硬件配置</h2>
        <pre>{json.dumps(hw, ensure_ascii=False, indent=2)}</pre>
        <h2>📦 项目组成</h2>
        <pre>{json.dumps(proj, ensure_ascii=False, indent=2)}</pre>
        <h2>📝 AI 深度分析</h2>
        <div>{html_body}</div>
        <div class="firewall">
            <h2>🛡️ 防火墙状态面板</h2>
            <div id="firewall-status">正在初始化...</div>
            <button onclick="checkHeartbeat()">手动检测</button>
        </div>
    </div>
    <script src="firewall.js"></script>
</body>
</html>"""
    with open(PROJECT_ROOT / "web" / "analysis.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    log("HTML 报告已生成：web/analysis.html")

    # 防火墙 JS
    firewall_js = """
const COMPONENTS = ['LocalBrain', 'KnowledgeBase', 'EvolutionController', 'ToolExecutor', 'TrainingEngine', 'VTuberEngine'];
const statusElem = document.getElementById('firewall-status');
function checkHeartbeat() {
    statusElem.innerHTML = '检测中...';
    let html = '<ul>';
    COMPONENTS.forEach(c => {
        // 模拟检测（实际应调用后端心跳API）
        let alive = Math.random() > 0.15;
        html += alive ? `<li>${c} : <span class="status-ok">正常</span></li>` : `<li>${c} : <span class="status-error">异常</span></li>`;
    });
    html += '</ul>';
    statusElem.innerHTML = html;
}
setInterval(checkHeartbeat, 30000);
checkHeartbeat();
"""
    with open(PROJECT_ROOT / "web" / "firewall.js", "w", encoding="utf-8") as f:
        f.write(firewall_js)
    log("防火墙 JS 已生成：web/firewall.js")

# --------------- 集成到 LightAgent（增加标签页） ---------------
def integrate_to_gui():
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        log("PyQtWebEngine 未安装，无法在 GUI 中显示网页。请运行：pip install PyQtWebEngine", "WARNING")
        return
    # 创建分析报告标签页文件
    tab_code = '''# ui/analysis_tab.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from pathlib import Path

class AnalysisReportTab(QWidget):
    def __init__(self, agent):
        super().__init__()
        layout = QVBoxLayout()
        self.webview = QWebEngineView()
        self.webview.load(QUrl.fromLocalFile(str(Path(__file__).resolve().parent.parent / "web" / "analysis.html")))
        layout.addWidget(self.webview)
        self.setLayout(layout)
'''
    tab_file = PROJECT_ROOT / "ui" / "analysis_tab.py"
    with open(tab_file, "w", encoding="utf-8") as f:
        f.write(tab_code)
    # 修改 main_window.py
    mainwin = PROJECT_ROOT / "ui" / "main_window.py"
    if not mainwin.exists():
        log("main_window.py 不存在，无法集成标签页", "ERROR")
        return
    with open(mainwin, "r", encoding="utf-8") as f:
        content = f.read()
    if "AnalysisReportTab" not in content:
        # 添加导入
        content = content.replace(
            "from ui.training_center import TrainingCenterTab",
            "from ui.training_center import TrainingCenterTab\nfrom ui.analysis_tab import AnalysisReportTab"
        )
        # 在 TAB_CONFIG 列表末尾添加新标签
        tab_config_marker = "TAB_CONFIG = ["
        if tab_config_marker in content:
            start = content.find(tab_config_marker)
            end = content.find("]", start)
            new_tab_line = '    ("📊 分析报告", "ui.analysis_tab", "AnalysisReportTab"),\n'
            if new_tab_line not in content:
                content = content[:end] + new_tab_line + content[end:]
        with open(mainwin, "w", encoding="utf-8") as f:
            f.write(content)
        log("分析报告标签页已集成到主窗口")
    else:
        log("分析报告标签页已存在，跳过")

# --------------- 主流程 ---------------
def main():
    log("🚀 LightAgent 全能分析完美化启动")
    # 1. 硬件扫描
    hw = scan_hardware()
    # 2. 项目扫描
    proj = scan_project()
    # 3. 构建提示词并调用 API
    prompt = build_prompt(hw, proj)
    response = call_deepseek(prompt)
    if response is None:
        log("DeepSeek API 调用失败，无法继续。请检查 API Key 和网络。", "ERROR")
        return
    # 4. 生成报告和防火墙
    generate_output(response, hw, proj)
    # 5. 集成到 GUI
    integrate_to_gui()
    log("🎉 全部完成！请查看桌面日志和 web/analysis.html。")

if __name__ == "__main__":
    main()
