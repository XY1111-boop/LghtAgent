# filename: E:\LightAgent\intelligence\web_search.py
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import os
import requests
from duckduckgo_search import DDGS
from cachetools import TTLCache
from intelligence.deepseek_api import DeepSeekAPI

search_cache = TTLCache(maxsize=100, ttl=300)

def search_web(query: str, max_results: int = 3) -> list:
    if query in search_cache:
        return search_cache[query]
    api_key = os.getenv("SERPER_API_KEY", "")
    if api_key:
        results = _call_serper(query, api_key, max_results)
    else:
        results = _call_duckduckgo(query, max_results)
    search_cache[query] = results
    return results

def _call_serper(query, api_key, max_results):
    resp = requests.post("https://google.serper.dev/search", json={"q": query, "num": max_results},
                         headers={"X-API-KEY": api_key}, timeout=10)
    if resp.status_code == 200:
        return [{"title": r["title"], "link": r["link"], "snippet": r.get("snippet","")} for r in resp.json().get("organic",[])]
    return []

def _call_duckduckgo(query, max_results):
    try:
        with DDGS() as ddgs:
            return [{"title": r["title"], "link": r["href"], "snippet": r["body"]} for r in ddgs.text(query, max_results=max_results)]
    except:
        return []

def fetch_page_content(url: str) -> str:
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.get_text()[:2000]
    except:
        return ""

def build_enhanced_prompt(user_query, search_results):
    context = "\n".join([f"- {r['title']}: {r['snippet']}" for r in search_results])
    return f"搜索结果：\n{context}\n\n用户问题：{user_query}"

def call_deepseek_api(prompt, api_key, model="deepseek-chat"):
    api = DeepSeekAPI(api_key, model)
    return api.call_with_prompt(prompt)

def needs_web_search(query):
    return any(k in query for k in ["最新", "新闻", "今天", "天气", "搜索"])

def main(query, enable_search=True):
    if enable_search and needs_web_search(query):
        results = search_web(query)
        if results:
            prompt = build_enhanced_prompt(query, results)
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            return call_deepseek_api(prompt, api_key)
    return "未执行搜索。"
