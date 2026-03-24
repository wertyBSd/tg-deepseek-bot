from typing import Dict, Any, Optional

# Режимы ответов
RESPONSE_MODES = {
    "brief": {
        "name": "🔹 Краткий",
        "description": "Короткие и ёмкие ответы",
        "system_prompt": "Ты — дружелюбный чат-бот. Отвечай максимально кратко, 1-3 предложения. Только суть.",
        "temperature": 0.5,
        "max_tokens": 256
    },
    "normal": {
        "name": "🔸 Обычный",
        "description": "Сбалансированные ответы",
        "system_prompt": "Ты — дружелюбный чат-бот. Отвечай кратко и понятно.",
        "temperature": 0.7,
        "max_tokens": 1024
    },
    "detailed": {
        "name": "📚 Подробный",
        "description": "Развёрнутые ответы с объяснениями",
        "system_prompt": "Ты — эксперт, который даёт подробные объяснения. Отвечай развёрнуто, с примерами и пояснениями.",
        "temperature": 0.8,
        "max_tokens": 2048
    },
    "creative": {
        "name": "🎨 Творческий",
        "description": "Креативные и нестандартные ответы",
        "system_prompt": "Ты — творческий помощник с богатым воображением. Отвечай креативно, используй метафоры.",
        "temperature": 0.9,
        "max_tokens": 2048
    },
    "professional": {
        "name": "💼 Профессиональный",
        "description": "Деловой и формальный стиль",
        "system_prompt": "Ты — профессиональный консультант. Отвечай формально, структурированно, по делу.",
        "temperature": 0.4,
        "max_tokens": 1024
    }
}

# Ключевые слова для смены режима
MODE_KEYWORDS = {
    "brief": ["кратко", "короче", "сжато", "краткий ответ", "коротко"],
    "detailed": ["подробно", "подробнее", "развернуто", "поподробнее", "детально", "объясни подробно"],
    "creative": ["креативно", "творчески", "интересно", "необычно", "оригинально"],
    "professional": ["профессионально", "формально", "деловой стиль", "официально"],
    "normal": ["обычно", "нормально", "стандартно", "как обычно"]
}

def detect_mode_from_text(text: str) -> Optional[str]:
    """Определяет режим по ключевым словам"""
    text_lower = text.lower()
    for mode, keywords in MODE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return mode
    return None

def get_mode_settings(mode: str) -> Dict[str, Any]:
    """Возвращает настройки режима"""
    return RESPONSE_MODES.get(mode, RESPONSE_MODES["normal"])