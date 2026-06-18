# core/safety_auditor.py
import json
import re

IMMUTABLE_FILES = [
    "core/sandbox.py",
    "core/safety_auditor.py",
    "utils/config.py",
]

AUDIT_PROMPT = """你是一个代码安全审计专家。请审查以下 Python 代码是否安全。
返回 JSON：{"approved": true/false, "reason": "说明"}
代码：
{code}
"""

class SafetyAuditor:
    def __init__(self, deepseek_api):
        self.api = deepseek_api

    def audit(self, code: str, change_summary: str) -> (bool, str):
        for file_path in IMMUTABLE_FILES:
            if file_path in code and ("write" in code or "open" in code or "remove" in code):
                return False, f"尝试修改不可变文件 {file_path}"
        prompt = AUDIT_PROMPT.format(code=code)
        try:
            response = self.api.call_with_prompt(prompt, temperature=0.1, max_tokens=200)
            result = json.loads(response)
            # 容错处理：approved 字段可能是字符串
            approved = result.get("approved", False)
            if isinstance(approved, str):
                approved = approved.strip('"').strip("'").lower() in ("true", "approved", "yes")
            return approved, result.get("reason", "无原因")
        except Exception as e:
            return False, f"审计异常：{e}"

    def assess_risk(self, code: str) -> str:
        if any(w in code for w in ["os.system", "subprocess", "shutil.rmtree"]):
            return "medium"
        return "low"

    def check_output_sensitive(self, text):
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                return False, "输出可能包含敏感信息"
        return True, None
