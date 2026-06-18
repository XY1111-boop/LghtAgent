
// suggestions.js —— 实时 AI 建议轮询
const SUGGESTIONS_API = 'http://localhost:5001/api/suggestions/list';
const suggestionsContainer = document.getElementById('suggestions-container');

async function fetchSuggestions() {
    if (!suggestionsContainer) return;
    try {
        const resp = await fetch(SUGGESTIONS_API + '?t=' + new Date().getTime());
        const data = await resp.json();
        let html = '<ul>';
        if (data.length === 0) {
            html += '<li style="color:gray;">暂无实时建议，请与 AI 对话并询问改进意见。</li>';
        } else {
            // 显示最近5条
            data.slice(-5).reverse().forEach(item => {
                const time = new Date(item.time * 1000).toLocaleTimeString();
                html += `<li style="margin-bottom:8px;"><span style="color:#888;">[${time}]</span> <b>${item.source}:</b> ${item.text.substring(0,200)}</li>`;
            });
        }
        html += '</ul>';
        suggestionsContainer.innerHTML = html;
    } catch (e) {
        suggestionsContainer.innerHTML = '<span style="color:orange;">无法连接建议服务</span>';
    }
}
setInterval(fetchSuggestions, 10000);
fetchSuggestions();
