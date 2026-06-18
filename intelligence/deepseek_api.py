# filename: E:\LightAgent\intelligence\deepseek_api.py
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import requests
import time
import json

class DeepSeekAPI:
    def __init__(self, api_key, model="deepseek-chat", base_url="https://api.deepseek.com/v1/chat/completions"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            })

    def chat(self, messages: list[dict], temperature=0.7, max_tokens=2000) -> str:
        if not self.api_key:
            raise Exception("❌ API Key 为空，请在 config.yaml 中填写 api_key 或通过设置菜单输入。")
        for attempt in range(3):
            try:
                resp = self.session.post(self.base_url, json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }, timeout=(10, 30))
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    err_msg = f"❌ API 返回错误 (状态码 {resp.status_code})"
                    try:
                        detail = resp.json()
                        err_msg += f": {detail}"
                    except:
                        err_msg += f": {resp.text}"
                    print(err_msg)
                    if resp.status_code == 401:
                        raise Exception("API Key 无效，请检查 config.yaml 中的 api_key 是否正确。")
                    elif resp.status_code == 402:
                        raise Exception("账户余额不足，请前往 platform.deepseek.com 充值。")
                    elif resp.status_code == 429:
                        print("请求频率过高，等待后重试...")
                        time.sleep(5)
                        continue
                    else:
                        raise Exception(err_msg)
            except requests.exceptions.ConnectionError:
                print("❌ 无法连接 DeepSeek 服务器，请检查网络或代理设置。")
                time.sleep(2)
            except Exception as e:
                print(f"API 异常 (尝试 {attempt+1}/3): {e}")
            time.sleep(1)
        raise Exception("DeepSeek API 请求失败，请根据上述提示检查。")

    def call_with_prompt(self, prompt: str, temperature=0.7, max_tokens=2000) -> str:
        return self.chat([{"role": "user", "content": prompt}], temperature, max_tokens)
