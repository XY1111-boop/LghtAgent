
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
