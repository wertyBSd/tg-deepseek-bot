import json
import time
import httpx
import re
from typing import List, Dict, Any, Optional, Tuple

# Абсолютные импорты от корня проекта
from config import settings
from utils import helpers, modes

_http_client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    """Создаёт или возвращает HTTP клиент"""
    global _http_client
    if _http_client is None:
        settings.logger.debug("🔧 Создание HTTP клиента")
        _http_client = httpx.AsyncClient(
            timeout=settings.LLM_TIMEOUT_S,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            follow_redirects=True
        )
    return _http_client


async def close_http_client():
    """Закрывает HTTP клиент"""
    global _http_client
    if _http_client:
        settings.logger.debug("🔧 Закрытие HTTP клиента")
        await _http_client.aclose()
        _http_client = None


async def query_deepseek(
        messages: List[Dict[str, str]],
        mode: str = "normal"
) -> Tuple[Optional[str], float]:
    """
    Отправляет запрос к DeepSeek
    Возвращает (ответ, время_генерации)
    """
    url = f"{settings.LLM_BASE_URL}/chat/completions"
    mode_settings = modes.get_mode_settings(mode)

    payload = {
        "model": settings.LLM_MODEL,
        "messages": messages,
        "stream": False,
        "max_tokens": mode_settings["max_tokens"],
        "temperature": mode_settings["temperature"],
        "top_p": settings.TOP_P,
        "top_k": settings.TOP_K,
        "repeat_penalty": settings.REPEAT_PENALTY,
        "options": {
            "num_ctx": 4096,
        }
    }

    settings.logger.debug(f"📤 DeepSeek запрос к {url}")
    settings.logger.debug(f"📤 Режим: {mode}, температура: {mode_settings['temperature']}")
    settings.logger.debug(f"📤 Сообщений: {len(messages)}")

    if settings.DEBUG:
        user_msgs = [m for m in messages if m["role"] == "user"]
        if user_msgs:
            settings.logger.debug(f"📤 Последний вопрос: {user_msgs[-1]['content'][:100]}...")

    client = await get_http_client()

    try:
        start_time = time.time()
        settings.logger.debug("⏳ Отправка запроса в DeepSeek...")

        response = await client.post(url, json=payload)
        elapsed = time.time() - start_time

        settings.logger.debug(f"📥 Статус ответа: {response.status_code}")
        settings.logger.debug(f"📥 Время ответа: {helpers.format_time(elapsed)}")

        if response.status_code != 200:
            settings.logger.error(f"❌ HTTP ошибка: {response.status_code}")
            settings.logger.error(f"❌ Ответ: {response.text[:500]}")
            response.raise_for_status()

        response.raise_for_status()
        data = response.json()

        settings.logger.debug("📥 Парсинг ответа DeepSeek...")

        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            content = choice.get("message", {}).get("content", "")

            settings.logger.debug(f"📥 Длина ответа: {len(content)} символов")

            if settings.DEBUG and content:
                settings.logger.debug(f"📥 Первые 200 символов: {content[:200]}")

            content = clean_response(content)

            time_str = helpers.format_time_detailed(elapsed)
            settings.logger.info(f"✅ Получен ответ, длина: {len(content)} символов, время: {time_str}")

            return content, elapsed
        else:
            settings.logger.error(f"❌ Странный ответ API: {data}")
            return None, elapsed

    except httpx.TimeoutException:
        settings.logger.error("⏱️ Таймаут DeepSeek")
        return None, 0
    except httpx.HTTPStatusError as e:
        settings.logger.error(f"🌐 HTTP ошибка {e.response.status_code}: {e.response.text[:200]}")
        return None, 0
    except Exception as e:
        settings.logger.error(f"❌ Ошибка DeepSeek: {e}", exc_info=True)
        return None, 0


def clean_response(text: str) -> str:
    """Очищает ответ от служебных тегов"""
    if not text:
        return text

    original_len = len(text)
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    text = re.sub(r'<reasoning>.*?</reasoning>', '', text, flags=re.DOTALL)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)

    if len(text) != original_len:
        settings.logger.debug(f"🧹 Очистка: {original_len} -> {len(text)} символов")

    return text.strip()