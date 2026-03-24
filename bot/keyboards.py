from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.modes import RESPONSE_MODES  # Убираем точки, делаем абсолютный импорт


def get_mode_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора режима"""
    keyboard = []
    row = []

    for i, (mode_id, mode) in enumerate(RESPONSE_MODES.items()):
        btn = InlineKeyboardButton(
            text=mode["name"],
            callback_data=f"mode_{mode_id}"
        )
        row.append(btn)

        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([
        InlineKeyboardButton(text="❓ Текущий режим", callback_data="mode_current")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)