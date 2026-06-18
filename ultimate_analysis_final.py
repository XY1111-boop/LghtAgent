# ultimate_analysis_final.py —— 最终全能分析完美化脚本
import os, sys, json, time, datetime, platform, traceback, threading, re, shutil
from pathlib import Path
import requests
import yaml
import psutil
try:
    import GPUtil
except ImportError:
    GPUtil = None

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
DESKTOP_LOG = Path.home() / "Desktop" / "LightAgent_Analysis_Log.txt"
TIMEOUT = 120

# ╔══════════════════════════════════════════════════════════════╗
# ║  🔑 在这里填写你的 DeepSeek API Key（也可以留空，在网页中填写） ║
# ╚══════════════════════════════════════════════════════════════╝
MANUAL_API_KEY = ""

def log(msg, level="INFO"):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"[{now}] [{level}] {msg}"
    with open(DESKTOP_LOG, "a", encoding="utf-8") as f:
        f.write(text + "\n")
    print(text)

def get_api_key():
        return MANUAL_API_KEY
    cfg_file = PROJECT_ROOT / "config.yaml"
    if cfg_file.exists():
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        key = cfg.get("api_key", "")
            return key
    return None

def scan_hardware():
    log("正在扫描硬件...")
    info = {
        "操作系统": platform.platform(),
        "主机名": platform.node(),
        "CPU": platform.processor(),
        "逻辑核心": psutil.cpu_count(logical=True),
        "内存(GB)": round(psutil.virtual_memory().total / (1024**3), 2),
        "磁盘剩余(GB)": round(psutil.disk_usage('C:/').free / (1024**3), 2) if os.name == 'nt' else 0,
        "GPU": []
    }
    if GPUtil:
        try:
            for g in GPUtil.getGPUs():
                info["GPU"].append({"名称": g.name, "显存(MB)": g.memoryTotal, "驱动": g.driver})
        except Exception as e:
            info["GPU"].append({"错误": str(e)})
    else:
        info["GPU"].append("无法获取")
    log("硬件扫描完成")
    return info

def scan_project():
    log("正在扫描项目...")
    data = {
        "Python版本": sys.version,
        "文件数": 0,
        "代码总行数": 0,
        "模块": {},
        "关键组件": [],
        "依赖库": [],
        "配置文件": [],
        "数据库": []
    }
    py_files = list(PROJECT_ROOT.rglob("*.py"))
    data["文件数"] = len(py_files)
    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
                data["代码总行数"] += len(lines)
            rel = f.relative_to(PROJECT_ROOT)
            module = rel.parts[0] if len(rel.parts) > 1 else "根"
            data["模块"].setdefault(module, []).append(str(rel))
        except:
            pass
    components = {
        "本地LLM": "intelligence/local_llm.py",
        "安全沙箱": "core/sandbox.py",
        "安全审计": "core/safety_auditor.py",
        "进化系统": "intelligence/evolution.py",
        "工具执行器": "intelligence/tool_executor.py",
        "知识库": "knowledge/knowledge_base.py",
        "神经增强": "intelligence/neuro_enhancer.py",
        "经验管理器": "intelligence/experience_manager.py",
        "训练引擎": "intelligence/training_engine.py",
        "虚拟主播": "intelligence/vtuber_engine.py",
        "插件系统": "intelligence/plugin_system.py",
        "任务规划器": "intelligence/task_planner.py",
        "多模态感知": "intelligence/multimodal_perception.py",
        "A/B测试": "intelligence/ab_experiment.py",
        "联邦学习": "intelligence/federated_learning.py"
    }
    for name, fname in components.items():
        if (PROJECT_ROOT / fname).exists():
            data["关键组件"].append(name)
    try:
        import pkg_resources
        installed = {p.key for p in pkg_resources.working_set}
        for lib in ['PyQt5','requests','chromadb','llama-cpp-python','pyautogui','psutil','GPUtil','matplotlib','scikit-learn','numpy','yaml','torch','transformers','speechrecognition','pyttsx3']:
            if lib.lower().replace('-','_') in installed:
                data["依赖库"].append(lib)
    except:
        data["依赖库"] = ["获取失败"]
    data["配置文件"] = [c.name for c in PROJECT_ROOT.glob("*.yaml")]
    cache_dir = PROJECT_ROOT / "Cache"
    if cache_dir.exists():
        data["数据库"] = [d.name for d in cache_dir.glob("*.db")]
    log("项目扫描完成")
    return data

CHAT_SUMMARY = "用户（零基础）在AI辅助下，从零搭建了AI电脑管家LightAgent，包含本地LLM、安全沙箱、知识库、记忆系统、进化系统、工具调用、训练中心、虚拟主播等数十个模块，解决了数百个工程问题，最终在GTX 960M 2GB上稳定运行。"

def build_prompt(hw, proj):
    return f"""你是一位资深AI系统架构师。请对LightAgent项目进行全面分析（中文）：
硬件：{json.dumps(hw, ensure_ascii=False)}
项目：{json.dumps(proj, ensure_ascii=False)}
历程：{CHAT_SUMMARY}

请输出：
1. 完备度评估（表格）
2. Mermaid架构图
3. 缺失模块（至少5项）
4. 改进建议（至少5条，只增不减）
5. 防卡死防火墙设计（前端HTML+JS+后端Flask）
6. JSON摘要（```json块）"""

def call_deepseek(prompt):
    api_key = get_api_key()
    if not api_key:
        log("未配置API Key，跳过AI分析。可在网页中配置后手动触发。", "WARNING")
        return None
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 4000}
    log("请求DeepSeek分析...")
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=TIMEOUT)
        if resp.status_code == 200:
            log("分析完成")
            return resp.json()["choices"][0]["message"]["content"]
        else:
            log(f"API失败: {resp.status_code} {resp.text}", "ERROR")
            return None
    except Exception as e:
        log(f"API异常: {e}", "ERROR")
        return None

def generate_output(response, hw, proj):
    # 写入桌面日志
    if response:
        log("========== AI 分析结果 ==========")
        log(response)
    # 生成 HTML（集成API设置界面）
    web_dir = PROJECT_ROOT / "web"
    web_dir.mkdir(exist_ok=True)
    html = create_html(hw, proj, response or "AI 分析未执行，请先在页面中配置 API Key。")
    with open(web_dir / "analysis.html", "w", encoding="utf-8") as f:
        f.write(html)
    log("HTML 报告已生成")
    # 生成防火墙 JS
    with open(web_dir / "firewall.js", "w", encoding="utf-8") as f:
        f.write(get_firewall_js())
    log("防火墙 JS 已生成")
    # 确保心跳服务代码正确
    with open(PROJECT_ROOT / "heartbeat_server.py", "w", encoding="utf-8") as f:
        f.write(get_heartbeat_server_code())
    log("心跳服务代码已更新")

def create_html(hw, proj, ai_response):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>LightAgent 分析报告</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; background: #f5f5f5; margin: 20px; }}
        .container {{ max-width: 1000px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #4A90D9; }}
        pre {{ background: #1e1e1e; color: #d4d4d4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        .api-section, .firewall, .suggestions {{ border: 2px solid #4A90D9; padding: 15px; margin: 15px 0; border-radius: 8px; }}
        input[type="text"] {{ padding: 8px; width: 300px; }}
        button {{ padding: 8px 16px; background: #4A90D9; color: white; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }}
        .status-ok {{ color: green; font-weight: bold; }}
        .status-error {{ color: red; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 LightAgent 系统分析报告</h1>
        <div class="api-section">
            <h3>🔑 DeepSeek API Key 设置</h3>
            <input type="text" id="api-key-input" placeholder="输入你的 API Key" />
            <button onclick="saveApiKey()">保存</button>
            <span id="api-status" style="margin-left:10px;color:gray;"></span>
        </div>
        <h2>💻 硬件配置</h2>
        <pre>{json.dumps(hw, ensure_ascii=False, indent=2)}</pre>
        <h2>📦 项目组成</h2>
        <pre>{json.dumps(proj, ensure_ascii=False, indent=2)}</pre>
        <h2>📝 AI 深度分析</h2>
        <div>{ai_response}</div>
        <div class="firewall">
            <h2>🛡️ 防火墙状态面板</h2>
            <div id="firewall-status">检查中...</div>
            <button onclick="checkHeartbeat()">手动检测</button>
        </div>
        <div class="suggestions">
            <h3>💡 AI 实时建议</h3>
            <div id="suggestions-content">等待心跳数据...</div>
        </div>
    </div>
    <script src="firewall.js"></script>
</body>
</html>"""

def get_firewall_js():
    return r"""
const API_BASE = 'http://localhost:5001';
const statusElem = document.getElementById('firewall-status');
const suggestionsElem = document.getElementById('suggestions-content');
const apiInput = document.getElementById('api-key-input');
const apiStatus = document.getElementById('api-status');

async function loadApiKey() {
    try {
        const resp = await fetch(API_BASE + '/api/config');
        const data = await resp.json();
        apiStatus.textContent = data.api_key ? '已配置 (' + data.api_key + ')' : '未配置';
    } catch (e) {
        apiStatus.textContent = '无法连接配置服务';
    }
}
async function saveApiKey() {
    const key = apiInput.value.trim();
    if (!key) return;
    await fetch(API_BASE + '/api/config', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({api_key: key}) });
    apiInput.value = '';
    loadApiKey();
}

async function checkHeartbeat() {
    try {
        const resp = await fetch(API_BASE + '/api/heartbeat/status?t=' + Date.now());
        const data = await resp.json();
        let html = '<ul>';
        for (const [name, info] of Object.entries(data)) {
            html += `<li>${name} : <span class="${info.status==='alive'?'status-ok':'status-error'}">${info.status==='alive'?'正常':'异常'}</span></li>`;
        }
        statusElem.innerHTML = html + '</ul>';
        fetchSuggestions(data);
    } catch (e) {
        statusElem.innerHTML = '<span style="color:orange;">无法连接心跳服务</span>';
    }
}
async function fetchSuggestions(heartbeatData) {
    try {
        const resp = await fetch(API_BASE + '/api/suggestions', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({statuses: heartbeatData}) });
        const data = await resp.json();
        suggestionsElem.textContent = data.suggestions || '暂无建议';
    } catch (e) {
        suggestionsElem.textContent = '💡 无法获取建议';
    }
}
setInterval(checkHeartbeat, 5000);
checkHeartbeat();
loadApiKey();
"""

def get_heartbeat_server_code():
    return r'''# heartbeat_server.py —— 带API设置和建议的心跳服务
import threading, time, json, yaml
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from pathlib import Path

app = Flask(__name__)
CORS(app)

PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"

heartbeat_status = {}
TIMEOUT = 30

def load_api_key():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("api_key", "")
    return ""

def save_api_key(key):
    cfg = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    cfg["api_key"] = key
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True)

@app.route('/api/heartbeat/status')
def get_status():
    return jsonify(heartbeat_status)

@app.route('/api/heartbeat/ping', methods=['POST'])
def ping():
    data = request.get_json()
    name = data.get('component')
    if name:
        heartbeat_status[name] = {'last_heartbeat': time.time(), 'status': 'alive', 'alerts': []}
        return jsonify({'ok': True})
    return jsonify({'error': 'Missing component name'}), 400

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    if request.method == 'GET':
        key = load_api_key()
        return jsonify({'api_key': key[:8] + '***' if key else ''})
    elif request.method == 'POST':
        save_api_key(request.get_json().get('api_key', ''))
        return jsonify({'ok': True})

@app.route('/api/suggestions', methods=['POST'])
def suggestions():
    api_key = load_api_key()
    if not api_key:
        return jsonify({'suggestions': '请先配置 API Key'}), 401
    statuses = request.get_json().get('statuses', {})
    prompt = f"根据以下组件状态给出1-2条简短健康建议（中文，50字内）：\n{json.dumps(statuses, ensure_ascii=False)}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 100}
    try:
        resp = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            result = resp.json()["choices"][0]["message"]["content"].strip()
            return jsonify({'suggestions': result})
        return jsonify({'suggestions': f'AI服务异常: {resp.status_code}'}), 500
    except Exception as e:
        return jsonify({'suggestions': f'请求失败: {e}'}), 500

def monitor_loop():
    while True:
        now = time.time()
        for name, info in heartbeat_status.items():
            if now - info['last_heartbeat'] > TIMEOUT:
                info['status'] = 'dead'
        time.sleep(10)

if __name__ == '__main__':
    threading.Thread(target=monitor_loop, daemon=True).start()
    print("✅ 心跳监控服务已启动")
    app.run(host='0.0.0.0', port=5001, debug=False)
'''

def main():
    log("🚀 最终分析脚本启动")
    hw = scan_hardware()
    proj = scan_project()
    prompt = build_prompt(hw, proj)
    resp = call_deepseek(prompt)
    generate_output(resp, hw, proj)
    log("🎉 全部完成！请查看桌面日志和 web/analysis.html")
    log("启动心跳服务：python heartbeat_server.py")
    log("启动 LightAgent：python main.py")

if __name__ == "__main__":
    main()
