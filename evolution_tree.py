# evolution_tree.py —— 进化天赋树配置
# 每个天赋是一个字典，包含名称、描述、等级上限、当前等级、升级效果函数名

TALENTS = [
    {
        "id": "intelligence",
        "name": "🧠 智力",
        "desc": "提升模型回答的逻辑性与准确性",
        "max_level": 5,
        "level": 1,
        "effect": "upgrade_intelligence"
    },
    {
        "id": "speed",
        "name": "⚡ 速度",
        "desc": "降低推理延迟，提高响应速度",
        "max_level": 5,
        "level": 1,
        "effect": "upgrade_speed"
    },
    {
        "id": "safety",
        "name": "🛡️ 安全",
        "desc": "增强代码审计与沙箱防护",
        "max_level": 5,
        "level": 1,
        "effect": "upgrade_safety"
    },
    {
        "id": "creativity",
        "name": "🎨 创意",
        "desc": "提高回答的多样性与想象力",
        "max_level": 5,
        "level": 1,
        "effect": "upgrade_creativity"
    }
]
