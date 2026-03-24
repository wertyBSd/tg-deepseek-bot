#!/usr/bin/env python3
import asyncio
import sys
import os
import httpx
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import settings
from services import deepseek
from bot import handlers


async def check_ollama():
    """Проверяет доступность Ollama"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                model_names = [m.get("name", "") for m in models]

                settings.logger.info("✅ Ollama доступна")

                # Проверяем наличие нужной модели
                if not any(settings.LLM_MODEL in m for m in model_names):
                    settings.logger.warning(f"⚠️ Модель {settings.LLM_MODEL} не найдена!")
                    settings.logger.warning(f"📥 Загрузите: ollama pull {settings.LLM_MODEL}")
                else:
                    settings.logger.info(f"✅ Модель {settings.LLM_MODEL} доступна")

                return True
            else:
                settings.logger.error(f"❌ Ollama вернула статус {response.status_code}")
                return False
    except Exception as e:
        settings.logger.error(f"❌ Ollama не доступна: {e}")
        settings.logger.error("💡 Запустите: ollama serve")
        return False


async def on_startup(bot):
    """Действия при запуске бота"""
    settings.logger.info("=" * 60)
    settings.logger.info("🚀 ЗАПУСК БОТА")
    settings.logger.info("=" * 60)
    settings.logger.info(f"🤖 Модель: {settings.LLM_MODEL}")
    settings.logger.info(f"🌐 URL: {settings.LLM_BASE_URL}")
    settings.logger.info(f"👤 Admin ID: {settings.ADMIN_ID}")
    settings.logger.info("=" * 60)

    me = await bot.get_me()
    settings.logger.info(f"✅ Бот: @{me.username}")

    # Проверяем Ollama
    await check_ollama()

    # Даем время на подключение к серверам Telegram
    await asyncio.sleep(2)

    # Получаем список чатов через handlers (они уже должны быть загружены)
    chats_count = handlers.get_chats_count()
    settings.logger.info(f"📋 Загружено {chats_count} чатов из файла")

    if chats_count > 0:
        settings.logger.info(f"📨 Отправка уведомления о запуске в {chats_count} чатов...")
        await handlers.notify_all_chats(
            bot,
            "🚀 Бот запущен и готов к работе!",
            "🚀"
        )
    else:
        settings.logger.info("📭 Нет сохраненных чатов для уведомления")
        settings.logger.info("💡 Напишите боту любое сообщение, чтобы добавить чат в базу")


async def on_shutdown(bot):
    """Действия при остановке бота"""
    settings.logger.info("🛑 Остановка бота...")

    # Получаем список чатов
    chats_count = handlers.get_chats_count()
    settings.logger.info(f"📋 Всего чатов в базе: {chats_count}")

    if chats_count > 0:
        settings.logger.info(f"📨 Отправка уведомления об остановке в {chats_count} чатов...")
        await handlers.notify_all_chats(
            bot,
            "👋 Бот временно недоступен (перезапуск/обновление)",
            "👋"
        )
    else:
        settings.logger.info("📭 Нет сохраненных чатов для уведомления")

    # Даем время на отправку сообщений
    settings.logger.info("⏳ Ожидание отправки сообщений...")
    await asyncio.sleep(3)

    await deepseek.close_http_client()
    await bot.session.close()
    settings.logger.info("✅ Соединения закрыты")


async def main():
    """Главная функция"""
    bot = Bot(
        token=settings.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=None)
    )
    dp = Dispatcher()

    try:
        me = await bot.get_me()

        # СНАЧАЛА загружаем обработчики (они загрузят чаты из файла)
        await handlers.register_handlers(dp, bot, me.username)

        # ПОТОМ отправляем уведомление о запуске
        await on_startup(bot)

        settings.logger.info("🔄 Запуск polling...")
        settings.logger.info("ℹ️ Для остановки нажмите Ctrl+C")

        # Запускаем polling
        await dp.start_polling(bot)

    except Exception as e:
        settings.logger.error(f"❌ Ошибка: {e}")
    finally:
        await on_shutdown(bot)
        settings.logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        settings.logger.info("👋 Получен сигнал остановки (Ctrl+C)")
    except Exception as e:
        settings.logger.error(f"💥 Фатальная ошибка: {e}")