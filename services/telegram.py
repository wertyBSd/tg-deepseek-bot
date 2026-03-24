import time
import asyncio
import re
from aiogram import types

from config import settings
from utils import helpers

TELEGRAM_MAX = 4096


def chunk_text(text: str, max_length: int = TELEGRAM_MAX - 500) -> list:
    """Разбивает текст на части для Telegram"""
    if len(text) <= max_length:
        settings.logger.debug(f"Текст помещается в одно сообщение ({len(text)} симв.)")
        return [text]

    settings.logger.debug(f"Разбивка текста {len(text)} символов на части...")
    chunks = []
    current_chunk = ""

    sentences = re.split(r'([.!?]+)', text)

    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        punctuation = sentences[i + 1] if i + 1 < len(sentences) else ""
        full = sentence + punctuation

        if len(current_chunk) + len(full) <= max_length:
            current_chunk += full
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = full

    if current_chunk:
        chunks.append(current_chunk.strip())

    if not chunks:
        settings.logger.debug("Разбивка по предложениям не удалась, режем по символам")
        for i in range(0, len(text), max_length):
            chunks.append(text[i:i + max_length])

    settings.logger.debug(f"Получилось {len(chunks)} чанков")
    return chunks


async def send_response(message: types.Message, text: str, start_time: float):
    """Отправляет ответ пользователю"""
    if not text or len(text.strip()) == 0:
        settings.logger.warning("Попытка отправить пустой ответ")
        await message.answer("🤔 Модель не дала ответа.")
        return

    chunks = chunk_text(text)
    total_chunks = len(chunks)

    settings.logger.info(f"📦 Отправка {total_chunks} чанков...")

    for i, chunk in enumerate(chunks, 1):
        try:
            chunk_start = time.time()
            sent = await message.answer(chunk)
            chunk_time = time.time() - chunk_start

            settings.logger.info(
                f"✅ Чанк {i}/{total_chunks} | "
                f"длина: {len(chunk)} | "
                f"время: {chunk_time:.2f}с | "
                f"id: {sent.message_id}"
            )

            if i < total_chunks:
                await asyncio.sleep(0.5)

        except Exception as e:
            settings.logger.error(f"❌ Ошибка чанка {i}: {e}")
            try:
                await message.answer(chunk[:2000] + "...")
                settings.logger.info(f"✅ Отправлена урезанная версия чанка {i}")
            except:
                settings.logger.error(f"❌ Не удалось отправить даже урезанную версию")

    total_time = time.time() - start_time
    time_str = helpers.format_time_detailed(total_time)
    settings.logger.info(f"📊 Отправка завершена за {time_str}")