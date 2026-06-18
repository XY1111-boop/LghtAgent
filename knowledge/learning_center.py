from pathlib import Path
from pathlib import Path
from pathlib import Path
# filename: E:\LightAgent\knowledge\learning_center.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
from pathlib import Path
from knowledge.file_processor import extract_text_from_file

class LearningCenter:
    def __init__(self, api, knowledge_base, memory):
        self.api = api
        self.kb = knowledge_base
        self.memory = memory

    def process_file(self, file_path):
        text = extract_text_from_file(file_path)
        if not text: return False, "无法提取文本"
        prompt = f"为以下文档生成知识卡片（标题、关键概念、摘要）：\n{text[:3000]}"
        try:
            card = self.api.call_with_prompt(prompt, temperature=0.3, max_tokens=500)
            digest_path = self.kb.digested / (Path(file_path).stem + "_digest.txt")
            digest_path.write_text(card, encoding='utf-8')
            self.memory.add_memory("knowledge", f"消化文件 {Path(file_path).name}: {card[:100]}", importance=0.7)
            return True, card
        except Exception as e:
            return False, str(e)
