from typing import Dict, Any, Deque
from collections import deque
import time
from aiogram import types

# Заменяем относительный импорт на абсолютный
from config import settings

Hist = Deque[Dict[str, str]]
_histories: Dict[str, Hist] = {}
_user_status: Dict[int, Dict[str, Any]] = {}
_user_modes: Dict[str, str] = {}


def get_history_key(msg: types.Message) -> str:
    """Ключ для истории: зависит от настроек"""
    if settings.HISTORY_SCOPE == "chat":
        return f"chat:{msg.chat.id}"
    return f"user:{msg.from_user.id}"


def get_mode_key(msg: types.Message) -> str:
    """Ключ для режима: в группе общий, в личке персональный"""
    if msg.chat.type in ["group", "supergroup"]:
        return f"chat:{msg.chat.id}"
    return f"user:{msg.from_user.id}"


def get_history(key: str) -> Hist:
    """Получает историю по ключу"""
    if key not in _histories:
        _histories[key] = deque(maxlen=settings.HISTORY_MAX_TURNS * 2)
    return _histories[key]


def get_user_mode(key: str) -> str:
    """Получает режим пользователя/чата"""
    return _user_modes.get(key, "normal")


def set_user_mode(key: str, mode: str) -> bool:
    """Устанавливает режим"""
    if mode in ["brief", "normal", "detailed", "creative", "professional"]:
        _user_modes[key] = mode
        return True
    return False


def is_user_processing(user_id: int) -> bool:
    """Проверяет, обрабатывается ли запрос пользователя"""
    return user_id in _user_status


def set_user_processing(user_id: int, status: bool = True):
    """Устанавливает статус обработки"""
    if status:
        _user_status[user_id] = {"processing": True, "time": time.time()}
    elif user_id in _user_status:
        del _user_status[user_id]


def append_to_history(hist: Hist, role: str, content: str):
    """Добавляет сообщение в историю с обрезкой"""
    hist.append({"role": role, "content": content})

    # Обрезаем по символам
    total_chars = sum(len(m["content"]) for m in hist)
    while total_chars > settings.HISTORY_MAX_CHARS and hist:
        removed = hist.popleft()
        total_chars -= len(removed["content"])