# ultimate_analysis_v3.py —— LightAgent 全自动分析完美化脚本（最终版）
# 功能：扫描硬件、项目结构，使用 DeepSeek API 深度分析，生成桌面日志、HTML 报告、防火墙组件，
#        并集成到 LightAgent 主窗口中作为新标签页。同时确保心跳监控后端能正常启动。
# 作者：AI 助手
# 使用方法：直接运行 python ultimate_analysis_v3.py

import os, sys, json, time, datetime, platform, traceback, threading, re, shutil
from pathlib import Path
import requests
import yaml
import psutil
try:
    import GPUtil
except ImportError:
    GPUtil = None

# ╔══════════════════════════════════════════════════════════════╗
# ║  🔑 在这里填写你的 DeepSeek API Key（必填）                 ║
# ║  如果你已经在 config.yaml 中配置了 api_key，可以留空        ║
# ╚══════════════════════════════════════════════════════════════╝

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# 桌面日志路径
DESKTOP_LOG = Path.home() / "Desktop" / "LightAgent_Analysis_Log.txt"

# 超时设置
TIMEOUT = 120

# 颜色输出
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
    color = Colors.OK if level == "INFO" else Colors.WARNING if level == "WARNING" else Colors.FAIL
    print(f"{color}{text}{Colors.ENDC}")

def get_api_key():
    """获取 API Key：优先使用脚本中填写的，否则从 config.yaml 读取"""
        return API_KEY
    cfg_file = PROJECT_ROOT / "config.yaml"
    if cfg_file.exists():
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        key = cfg.get("api_key", "")
            return key
    return None

# ─── 硬件扫描 ───────────────────────────────
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
            for gpu in GPUtil.getGPUs():
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

# ─── 项目扫描 ───────────────────────────────
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
    py_files = list(PROJECT_ROOT.rglob("*.py"))
    data["文件总数"] = len(py_files)
    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
                data["代码总行数"] += len(lines)
            rel = f.relative_to(PROJECT_ROOT)
            module = rel.parts[0] if len(rel.parts) > 1 else "根目录"
            data["模块列表"].setdefault(module, []).append(str(rel))
        except:
            pass
    # 关键组件
    components = {
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
        "插件系统": "intelligence/plugin_system.py",
        "任务规划器": "intelligence/task_planner.py",
        "多模态感知": "intelligence/multimodal_perception.py",
        "A/B测试": "intelligence/ab_experiment.py",
        "联邦学习": "intelligence/federated_learning.py"
    }
    for name, path in components.items():
        if (PROJECT_ROOT / path).exists():
            data["关键组件"].append(name)
    # 依赖库
    try:
        import pkg_resources
        installed = {pkg.key for pkg in pkg_resources.working_set}
        wanted = ['PyQt5','requests','chromadb','llama-cpp-python','pyautogui',
                  'psutil','GPUtil','matplotlib','scikit-learn','numpy','yaml',
                  'torch','transformers','speechrecognition','pyttsx3','vosk']
        for lib in wanted:
            if lib.lower().replace('-','_') in installed:
                data["依赖库"].append(lib)
    except:
        data["依赖库"] = ["获取失败"]
    # 配置和数据库
    data["配置文件"] = [c.name for c in PROJECT_ROOT.glob("*.yaml")]
    cache_dir = PROJECT_ROOT / "Cache"
    if cache_dir.exists():
        data["数据库文件"] = [d.name for d in cache_dir.glob("*.db")]
    log("项目扫描完成")
    return data

# ─── 对话历史总结 ─────────────────────────────
CHAT_SUMMARY = """
本次对话核心历程（从零构建LightAgent的完整记录）：
1. 用户（零基础）在AI辅助下，用两天时间从零搭建了AI电脑管家LightAgent，包含PyQt5界面、本地大语言模型（Qwen2.5-0.5B→1.5B GGUF）、安全沙箱、知识库、记忆系统、进化系统、工具调用、训练中心、虚拟主播等数十个模块。
2. 解决了数百个工程问题：路径硬编码、线程安全、DLL缺失、编码乱码、API Key配置、模型下载等，最终在GTX 960M 2GB上稳定运行，所有功能完全离线可用。
3. 实现了动态神经增强框架（思维链、反思、经验学习）、游戏化进化看板、智能训练中心（利用DeepSeek生成操作样本，增量学习）、独立控制台监控、心跳监控后端等。
4. 新增模块：插件系统、任务规划器、多模态感知、A/B测试、联邦学习接口、混合知识检索、强化学习训练器。
5. 当前配置：Windows 10，GTX 960M 2GB，i5-4210H，12GB RAM，Python 3.11。
6. 最终目标：进一步提升智能水平，参加技术竞赛，获得行业认可。
"""

# ─── 构建 API 提示词 ─────────────────────────
def build_prompt(hw, proj):
    return f"""你是一位资深AI系统架构师与安全专家。请根据以下信息对LightAgent项目进行全面分析（用中文回复）：

【硬件配置】
{json.dumps(hw, ensure_ascii=False, indent=2)}

【项目扫描结果】
{json.dumps(proj, ensure_ascii=False, indent=2)}

【项目开发历程摘要】
{CHAT_SUMMARY}

请严格按以下要求输出：
1. **完备度评估**：列出已有功能模块并评价成熟度（高/中/低）。
2. **架构图（文字描述）**：用Mermaid或ASCII绘制当前系统架构图，标明数据流。
3. **缺失模块分析**：根据类似项目的最佳实践，列出至少5项应该添加但尚未实现的功能，每项给出理由。
4. **改进建议（只增不减）**：对现有模块提出至少5条优化方向，不删除任何功能。
5. **防卡死防火墙设计**：设计一个监控组件心跳的轻量级方案，包括前端显示面板（HTML+JS）和后端监控逻辑（Flask或纯Python）。
6. **JSON摘要**：将上述结论（完备度、缺失模块、改进建议、防火墙方案）封装为JSON对象，放在```json代码块中。

注意：所有建议必须只增加功能，绝不删除或简化现有模块。"""

# ─── 调用 DeepSeek API ─────────────────────
def call_deepseek(prompt):
    api_key = get_api_key()
    if not api_key:
        log("未找到有效的 DeepSeek API Key！请在脚本顶部的 API_KEY 变量中填写，或确保 config.yaml 中已配置。", "ERROR")
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4000
    }
    log("正在请求 DeepSeek API...")
    result = [None]
    def worker():
        try:
            resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=TIMEOUT)
            if resp.status_code == 200:
                result[0] = resp.json()["choices"][0]["message"]["content"]
            else:
                result[0] = f"ERROR: {resp.status_code} {resp.text}"
        except Exception as e:
            result[0] = f"EXCEPTION: {e}"
    t = threading.Thread(target=worker)
    t.start()
    waited = 0
    while t.is_alive() and waited < 90:
        time.sleep(5)
        waited += 5
        log(f"等待 API 响应中... ({waited}秒)")
    if t.is_alive():
        log("API 请求超时，强制返回", "ERROR")
        return None
    res = result[0]
    if res.startswith("ERROR"):
        log(f"API 调用失败: {res}", "ERROR")
        return None
    if res.startswith("EXCEPTION"):
        log(f"网络异常: {res}", "ERROR")
        return None
    log("DeepSeek 分析成功")
    return res

# ─── 生成输出文件 ───────────────────────────
def generate_output(response, hw, proj):
    log("正在生成分析报告...")
    # 桌面日志
    log("========== DeepSeek 分析结果 ==========")
    log(response)
    log("========== 分析结束 ==========")

    # 提取 JSON 摘要
    json_match = re.search(r"```json\n(.*?)\n```", response, re.DOTALL)
    summary = {}
    if json_match:
        try:
            summary = json.loads(json_match.group(1))
            with open(PROJECT_ROOT / "analysis_summary.json", "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            log("JSON 摘要已保存到 analysis_summary.json")
        except:
            log("JSON 摘要提取失败", "WARNING")

    # HTML 报告
    web_dir = PROJECT_ROOT / "web"
    web_dir.mkdir(exist_ok=True)
    html_body = response.replace("\n", "<br>").replace(" ", "&nbsp;")
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
        .status-error {{ color: red; font-weight: bold; }}
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
            <div id="firewall-status">检查中...</div>
            <button onclick="checkHeartbeat()">手动检测</button>
        </div>
    </div>
    <script src="firewall.js"></script>
</body>
</html>"""
    with open(web_dir / "analysis.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    log("HTML 报告已生成：web/analysis.html")

    # 防火墙 JS（真实后端版本）
    firewall_js = """
// firewall.js —— 真实后端心跳检测
const API_URL = 'http://localhost:5001/api/heartbeat/status';
const statusElem = document.getElementById('firewall-status');
async function checkHeartbeat() {
    if (!statusElem) return;
    try {
        const resp = await fetch(API_URL);
        const data = await resp.json();
        let html = '<ul>';
        for (const [name, info] of Object.entries(data)) {
            const cls = info.status === 'alive' ? 'status-ok' : 'status-error';
            const text = info.status === 'alive' ? '正常' : '异常';
            html += `<li>${name} : <span class="${cls}">${text}</span></li>`;
        }
        html += '</ul>';
        statusElem.innerHTML = html;
    } catch (e) {
        statusElem.innerHTML = '<span style="color:orange;">无法连接心跳服务</span>';
    }
}
setInterval(checkHeartbeat, 5000);
checkHeartbeat();
"""
    with open(web_dir / "firewall.js", "w", encoding="utf-8") as f:
        f.write(firewall_js)
    log("防火墙 JS 已生成：web/firewall.js")

    # 心跳监控后端（修复版，确保能启动）
    heartbeat_code = r'''# heartbeat_server.py —— 组件心跳监控后端（修复版）
import threading, time, json
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

heartbeat_status = {}
TIMEOUT = 30

@app.route('/api/heartbeat/status', methods=['GET'])
def get_status():
    return jsonify(heartbeat_status)

@app.route('/api/heartbeat/ping', methods=['POST'])
def ping():
    data = request.get_json()
    name = data.get('component')
    if name:
        heartbeat_status[name] = {
            'last_heartbeat': time.time(),
            'status': 'alive',
            'alerts': []
        }
        return jsonify({'ok': True})
    return jsonify({'error': 'Missing component name'}), 400

def monitor_loop():
    while True:
        now = time.time()
        for name, info in heartbeat_status.items():
            if now - info['last_heartbeat'] > TIMEOUT:
                info['status'] = 'dead'
                info.setdefault('alerts', []).append({
                    'time': now,
                    'message': f'Component {name} is DEAD'
                })
        time.sleep(10)

def start_server():
    threading.Thread(target=monitor_loop, daemon=True).start()
    print("✅ 心跳监控服务已启动，访问 http://localhost:5001")
    app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == '__main__':
    start_server()
'''
    with open(PROJECT_ROOT / "heartbeat_server.py", "w", encoding="utf-8") as f:
        f.write(heartbeat_code)
    log("心跳监控后端已修复：heartbeat_server.py")

# ─── 集成到 LightAgent 主窗口（添加标签页）─────────
def integrate_to_gui():
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        log("PyQtWebEngine 未安装，无法在 GUI 中显示网页。请运行：pip install PyQtWebEngine", "WARNING")
        return
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
    mainwin = PROJECT_ROOT / "ui" / "main_window.py"
    if not mainwin.exists():
        log("main_window.py 不存在，无法集成标签页", "ERROR")
        return
    with open(mainwin, "r", encoding="utf-8") as f:
        content = f.read()
    if "AnalysisReportTab" not in content:
        content = content.replace(
            "from ui.training_center import TrainingCenterTab",
            "from ui.training_center import TrainingCenterTab\nfrom ui.analysis_tab import AnalysisReportTab"
        )
        marker = "TAB_CONFIG = ["
        if marker in content:
            start = content.find(marker)
            end = content.find("]", start)
            new_tab = '    ("📊 分析报告", "ui.analysis_tab", "AnalysisReportTab"),\n'
            if new_tab not in content:
                content = content[:end] + new_tab + content[end:]
        with open(mainwin, "w", encoding="utf-8") as f:
            f.write(content)
        log("分析报告标签页已集成到主窗口")
    else:
        log("分析报告标签页已存在，跳过")

# ─── 主流程 ────────────────────────────────
def main():
    log("🚀 LightAgent 全能分析完美化启动")
    hw = scan_hardware()
    proj = scan_project()
    prompt = build_prompt(hw, proj)
    resp = call_deepseek(prompt)
    if not resp:
        log("无法获取分析结果，请检查 API Key 和网络。", "ERROR")
        return
    generate_output(resp, hw, proj)
    integrate_to_gui()
    log("🎉 全部完成！请查看桌面日志和 web/analysis.html。")
    log("提示：启动心跳监控服务请运行 python heartbeat_server.py，然后在 LightAgent 中打开分析报告标签页。")

if __name__ == "__main__":
    main()
