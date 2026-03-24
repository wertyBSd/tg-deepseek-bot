import time
import asyncio
import json
import os
from aiogram import types
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery

from config import settings
from services import deepseek, telegram
from utils import history, modes, helpers
from bot.keyboards import get_mode_keyboard

BOT_USERNAME = None
bot_instance = None
# Хранилище ID чатов, где был бот
_chat_ids = set()
CHATS_FILE = "chats.json"  # Файл для сохранения ID чатов


def load_chats():
    """Загружает сохраненные ID чатов из файла"""
    global _chat_ids
    try:
        if os.path.exists(CHATS_FILE):
            with open(CHATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _chat_ids = set(data.get('chat_ids', []))
                settings.logger.info(f"📂 Загружено {len(_chat_ids)} чатов из файла")
        else:
            settings.logger.info("📂 Файл с чатами не найден, будет создан при первом добавлении")
    except Exception as e:
        settings.logger.error(f"❌ Ошибка загрузки чатов: {e}")
        _chat_ids = set()


def save_chats():
    """Сохраняет ID чатов в файл"""
    try:
        with open(CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'chat_ids': list(_chat_ids)}, f, ensure_ascii=False, indent=2)
        settings.logger.debug(f"💾 Сохранено {len(_chat_ids)} чатов в файл")
    except Exception as e:
        settings.logger.error(f"❌ Ошибка сохранения чатов: {e}")


def get_chats_count() -> int:
    """Возвращает количество сохраненных чатов"""
    return len(_chat_ids)


def add_chat(chat_id: int):
    """Добавляет чат в список и сохраняет"""
    global _chat_ids
    if chat_id not in _chat_ids:
        _chat_ids.add(chat_id)
        save_chats()
        settings.logger.info(f"✅ Чат {chat_id} добавлен в список (всего: {len(_chat_ids)})")


def remove_chat(chat_id: int):
    """Удаляет чат из списка и сохраняет"""
    global _chat_ids
    if chat_id in _chat_ids:
        _chat_ids.remove(chat_id)
        save_chats()
        settings.logger.info(f"❌ Чат {chat_id} удален из списка (всего: {len(_chat_ids)})")


def should_respond_in_group(msg: types.Message) -> bool:
    """Проверяет, должен ли бот ответить в группе"""
    settings.logger.debug(f"🔍 Проверка сообщения в группе: '{msg.text}'")

    if msg.text and msg.text.startswith('/'):
        settings.logger.debug(f"✅ Условие 1: это команда {msg.text}")
        return True

    if BOT_USERNAME and msg.text and f"@{BOT_USERNAME}" in msg.text:
        settings.logger.debug(f"✅ Условие 2: есть упоминание @{BOT_USERNAME}")
        return True

    if msg.reply_to_message and msg.reply_to_message.from_user.id == msg.bot.id:
        settings.logger.debug(f"✅ Условие 3: это ответ на сообщение бота")
        return True

    settings.logger.debug(f"❌ Ни одно условие не выполнено, игнорируем")
    return False


def clean_group_message(text: str) -> str:
    """Очищает сообщение от упоминания бота"""
    if not text or not BOT_USERNAME:
        return text
    cleaned = text.replace(f"@{BOT_USERNAME}", "").strip()
    if text != cleaned:
        settings.logger.debug(f"Очистка упоминания: '{text}' -> '{cleaned}'")
    return cleaned


async def notify_all_chats(bot, message: str, emoji: str = "🤖"):
    """Отправляет уведомление во все известные чаты"""
    settings.logger.info(f"{emoji} Отправка уведомления во все чаты: {message}")

    if not _chat_ids:
        settings.logger.info("📭 Нет сохраненных чатов для уведомления")
        return

    settings.logger.info(f"📨 Отправка уведомления в {len(_chat_ids)} чатов")

    success_count = 0
    fail_count = 0
    failed_chats = []

    for chat_id in list(_chat_ids):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"{emoji} {message}",
                parse_mode=None
            )
            settings.logger.info(f"✅ Уведомление отправлено в чат {chat_id}")
            success_count += 1
            await asyncio.sleep(0.2)  # Небольшая задержка чтобы не флудить
        except Exception as e:
            settings.logger.warning(f"❌ Не удалось отправить в чат {chat_id}: {e}")
            fail_count += 1
            failed_chats.append(chat_id)
            # Если бот больше не в чате, удаляем из списка
            error_str = str(e).lower()
            if "bot was kicked" in error_str or "bot is not a member" in error_str or "chat not found" in error_str:
                settings.logger.info(f"🗑️ Удаляем чат {chat_id} из базы (бот больше не в чате)")
                remove_chat(chat_id)

    settings.logger.info(f"📊 Результат: {success_count} отправлено, {fail_count} ошибок")
    if failed_chats:
        settings.logger.debug(f"❌ Неудачные чаты: {failed_chats}")


async def register_handlers(dp, bot, bot_username: str):
    """Регистрирует все обработчики"""
    global BOT_USERNAME, bot_instance
    BOT_USERNAME = bot_username
    bot_instance = bot

    # Загружаем сохраненные чаты ПРИ РЕГИСТРАЦИИ
    load_chats()

    settings.logger.info(f"✅ Регистрация обработчиков для @{BOT_USERNAME}")
    settings.logger.info(f"📋 Всего чатов в базе: {len(_chat_ids)}")

    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        settings.logger.info(f"🚀 /start от {message.from_user.id} (@{message.from_user.username})")
        start_time = time.time()

        # Сохраняем ID чата
        add_chat(message.chat.id)

        welcome = (
            f"👋 Привет! Я бот с {settings.LLM_MODEL}\n\n"
            f"📝 **Как пользоваться:**\n"
            f"• В личке: просто пиши сообщения\n"
            f"• В группе: @{BOT_USERNAME} ваш вопрос\n"
            f"• Добавь 'подробнее' или 'кратко' в вопрос\n\n"
            f"🎭 /mode — выбрать режим ответов\n"
            f"🔄 /reset — очистить историю\n"
            f"📊 /stats — статистика\n"
            f"🧪 /test — тест подключения\n"
            f"🔍 /group_status — статус в группе\n"
            f"📋 /list_chats — список чатов (админ)\n"
            f"❓ /how_to_add — как добавить чат"
        )

        sent = await message.answer(welcome, parse_mode="Markdown")
        elapsed = time.time() - start_time
        settings.logger.info(f"✅ /start обработан за {helpers.format_time(elapsed)}")

    @dp.my_chat_member()
    async def on_chat_member_update(update: types.ChatMemberUpdated):
        """Обработчик событий добавления/удаления бота из чатов"""
        chat = update.chat
        new_status = update.new_chat_member.status
        old_status = update.old_chat_member.status

        settings.logger.info(f"🔔 Изменение статуса в чате {chat.id} ({chat.type}): {old_status} -> {new_status}")

        # Бота добавили в чат
        if new_status in ["member", "administrator"] and old_status in ["left", "kicked"]:
            add_chat(chat.id)
            settings.logger.info(f"✅ Бот добавлен в чат {chat.id}, отправляю приветствие")
            try:
                await bot.send_message(
                    chat_id=chat.id,
                    text=f"👋 Привет! Я бот {BOT_USERNAME}. Я буду помогать вам!",
                    parse_mode=None
                )
            except Exception as e:
                settings.logger.error(f"❌ Не удалось отправить приветствие: {e}")

        # Бота удалили из чата
        elif new_status in ["left", "kicked"] and old_status in ["member", "administrator"]:
            remove_chat(chat.id)

    @dp.message(Command("group_status"))
    async def cmd_group_status(message: types.Message):
        if message.chat.type not in ["group", "supergroup"]:
            await message.answer("❌ Эта команда только для групп!")
            return

        settings.logger.info(f"🔍 Проверка статуса в группе {message.chat.id}")

        try:
            chat = await bot_instance.get_chat(message.chat.id)
            bot_member = await chat.get_member(bot_instance.id)

            status_text = (
                f"📊 **Статус в группе**\n\n"
                f"📌 **Группа:** {chat.title}\n"
                f"🆔 **ID:** `{chat.id}`\n"
                f"🤖 **Статус бота:** {bot_member.status}\n"
                f"📋 **В списке уведомлений:** {'✅' if message.chat.id in _chat_ids else '❌'}\n"
                f"📊 **Всего чатов в базе:** {len(_chat_ids)}\n\n"
            )

            if bot_member.status == 'left':
                status_text += (
                    "❌ **Privacy mode ВКЛЮЧЕН!**\n"
                    "Бот не видит сообщения в группе.\n\n"
                    "**Как исправить:**\n"
                    "1. Открой @BotFather\n"
                    "2. `/mybots` → выбери бота\n"
                    "3. Bot Settings → Group Privacy → **Turn off**\n"
                    "4. Перезапусти бота"
                )
            else:
                status_text += "✅ **Privacy mode выключен.**\nБот видит сообщения в группе."

            await message.answer(status_text, parse_mode="Markdown")

        except Exception as e:
            settings.logger.error(f"❌ Ошибка проверки статуса: {e}")
            await message.answer(f"❌ Ошибка: {e}")

    @dp.message(Command("list_chats"))
    async def cmd_list_chats(message: types.Message):
        """Показывает список всех чатов (только для админа)"""
        if message.from_user.id != settings.ADMIN_ID:
            await message.answer("❌ У вас нет прав")
            return

        if not _chat_ids:
            await message.answer("📭 Нет сохраненных чатов")
            return

        chats_list = "\n".join([f"• `{chat_id}`" for chat_id in _chat_ids])
        await message.answer(
            f"📋 **Список чатов ({len(_chat_ids)}):**\n\n{chats_list}",
            parse_mode="Markdown"
        )

    @dp.message(Command("how_to_add"))
    async def cmd_how_to_add(message: types.Message):
        """Показывает как добавлять чаты в базу"""
        text = (
            "📋 **Как добавить чат в базу уведомлений:**\n\n"
            "✅ **Способы:**\n"
            "• Напиши любое сообщение в личку с ботом\n"
            "• Напиши любое сообщение в группе с ботом\n"
            "• Отправь команду /start\n"
            "• Добавь бота в новую группу\n\n"
            "📊 **Текущий статус:**\n"
            f"• Чатов в базе: {len(_chat_ids)}\n\n"
            "🔍 **Проверка:**\n"
            "• /list_chats - показать все чаты (только админ)"
        )
        await message.answer(text, parse_mode="Markdown")

    @dp.message(Command("mode"))
    async def cmd_mode(message: types.Message):
        settings.logger.info(f"🎭 /mode от {message.from_user.id}")

        key = history.get_mode_key(message)
        current = history.get_user_mode(key)
        current_name = modes.RESPONSE_MODES[current]["name"]

        text = f"🎭 **Текущий режим:** {current_name}\n\n**Выберите:**"
        await message.answer(text, parse_mode="Markdown", reply_markup=get_mode_keyboard())

    @dp.callback_query(lambda c: c.data and c.data.startswith('mode_'))
    async def process_mode(callback: CallbackQuery):
        user_id = callback.from_user.id
        mode_id = callback.data.replace('mode_', '')
        key = history.get_mode_key(callback.message)

        settings.logger.info(f"🎮 Callback mode от {user_id}: {mode_id}")

        if mode_id == "current":
            current = history.get_user_mode(key)
            mode = modes.RESPONSE_MODES[current]
            text = f"🎭 **Текущий режим:** {mode['name']}"
            await callback.message.answer(text, parse_mode="Markdown")
        elif mode_id in modes.RESPONSE_MODES:
            if history.set_user_mode(key, mode_id):
                mode = modes.RESPONSE_MODES[mode_id]
                await callback.message.answer(f"✅ Режим: {mode['name']}")
                settings.logger.info(f"✅ Режим {mode_id} для {key}")
            else:
                settings.logger.error(f"❌ Ошибка установки режима {mode_id}")

        await callback.answer()

    @dp.message(Command("reset"))
    async def cmd_reset(message: types.Message):
        settings.logger.info(f"🔄 /reset от {message.from_user.id}")

        key = history.get_history_key(message)
        if key in history._histories:
            count = len(history._histories[key])
            del history._histories[key]
            await message.answer(f"🧹 История очищена ({count} сообщений)")
            settings.logger.info(f"✅ История {key} очищена, удалено {count} сообщений")
        else:
            await message.answer("📭 История пуста")

    @dp.message(Command("stats"))
    async def cmd_stats(message: types.Message):
        settings.logger.info(f"📊 /stats от {message.from_user.id}")

        key = history.get_history_key(message)
        hist = history.get_history(key)
        mode_key = history.get_mode_key(message)
        current_mode = history.get_user_mode(mode_key)
        mode_name = modes.RESPONSE_MODES[current_mode]["name"]

        stats = (
            f"📊 **Статистика**\n\n"
            f"👤 **ID:** {message.from_user.id}\n"
            f"🎭 **Режим:** {mode_name}\n"
            f"💬 **В истории:** {len(hist)} сообщений\n"
            f"🤖 **Модель:** {settings.LLM_MODEL}"
        )
        await message.answer(stats, parse_mode="Markdown")

    @dp.message(Command("test"))
    async def cmd_test(message: types.Message):
        settings.logger.info(f"🧪 /test от {message.from_user.id}")

        status = await message.answer("🔄 Тест...")
        try:
            messages = [{"role": "user", "content": "Скажи 'ok'"}]
            settings.logger.debug("Отправка тестового запроса в DeepSeek")

            response, gen_time = await deepseek.query_deepseek(messages)

            if response:
                time_str = helpers.format_time(gen_time)
                await status.edit_text(f"✅ OK (время: {time_str})")
                settings.logger.info(f"✅ Тест успешен за {helpers.format_time_detailed(gen_time)}")
            else:
                await status.edit_text("❌ Ошибка: нет ответа от модели")
                settings.logger.error("❌ Тест не удался")
        except Exception as e:
            settings.logger.error(f"❌ Ошибка теста: {e}", exc_info=True)
            await status.edit_text(f"❌ Ошибка: {str(e)[:50]}")

    @dp.message()
    async def handle_message(message: types.Message):
        """Основной обработчик сообщений"""
        user_id = message.from_user.id
        chat_type = message.chat.type
        start_time = time.time()

        # Сохраняем ID чата при любом сообщении
        add_chat(message.chat.id)

        settings.logger.info(f"📨 ПОЛУЧЕНО СООБЩЕНИЕ:")
        settings.logger.info(f"   • От: {user_id} (@{message.from_user.username})")
        settings.logger.info(f"   • Чат: {chat_type} (ID: {message.chat.id})")
        settings.logger.info(f"   • Текст: {message.text}")
        settings.logger.info(f"   • Есть reply: {message.reply_to_message is not None}")

        user_text = (message.text or "").strip()
        if not user_text:
            settings.logger.debug(f"Пустое сообщение от {user_id}")
            return

        if chat_type in ["group", "supergroup"]:
            settings.logger.info(f"🔍 ГРУППОВОЕ СООБЩЕНИЕ:")
            settings.logger.info(f"   • Название группы: {message.chat.title}")

            try:
                bot_member = await message.chat.get_member(bot_instance.id)
                settings.logger.info(f"   • Статус бота: {bot_member.status}")
                settings.logger.info(f"   • Может ли читать: {bot_member.status != 'left'}")
            except Exception as e:
                settings.logger.error(f"   • Ошибка проверки прав: {e}")

            settings.logger.debug(f"Проверка условий для ответа в группе...")

            is_command = user_text.startswith('/')
            has_mention = BOT_USERNAME and f"@{BOT_USERNAME}" in user_text
            is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot_instance.id

            settings.logger.info(f"📋 Условия для ответа:")
            settings.logger.info(f"   • Это команда: {is_command}")
            settings.logger.info(f"   • Есть упоминание @{BOT_USERNAME}: {has_mention}")
            settings.logger.info(f"   • Ответ на бота: {is_reply_to_bot}")

            if not should_respond_in_group(message):
                settings.logger.info(f"⏭️ Сообщение в группе проигнорировано")
                return

            original_text = user_text
            user_text = clean_group_message(user_text)
            settings.logger.debug(f"Текст после очистки: '{user_text}'")

            if not user_text:
                await message.reply("👋 Напишите вопрос после упоминания")
                return

        if history.is_user_processing(user_id):
            settings.logger.warning(f"⚠️ Пользователь {user_id} уже в обработке")
            await message.answer("⏳ Я ещё думаю над предыдущим вопросом...")
            return

        settings.logger.debug("Отправка 'Думаю...'")
        thinking = await message.answer("🤔 Думаю...")
        history.set_user_processing(user_id, True)

        try:
            hist_key = history.get_history_key(message)
            hist = history.get_history(hist_key)

            mode_key = history.get_mode_key(message)
            current_mode = history.get_user_mode(mode_key)

            settings.logger.debug(f"История: {hist_key}, режим: {current_mode}")

            temp_mode = modes.detect_mode_from_text(user_text)
            use_mode = temp_mode if temp_mode else current_mode

            if temp_mode:
                settings.logger.info(f"🔄 Временная смена режима: {current_mode} -> {temp_mode}")

            messages = [{"role": "system", "content": modes.RESPONSE_MODES[use_mode]["system_prompt"]}]

            history_msgs = list(hist)[-settings.HISTORY_MAX_TURNS * 2:]
            settings.logger.debug(f"Добавлено {len(history_msgs)} сообщений из истории")

            for msg in history_msgs:
                messages.append(msg)

            messages.append({"role": "user", "content": user_text})

            settings.logger.debug(f"Всего сообщений для модели: {len(messages)}")

            settings.logger.info("⏳ Отправка запроса в DeepSeek...")
            response, gen_time = await deepseek.query_deepseek(messages, use_mode)

            await thinking.delete()

            if response:
                settings.logger.info(f"✅ Получен ответ, длина: {len(response)} символов")

                history.append_to_history(hist, "user", user_text)
                history.append_to_history(hist, "assistant", response)
                settings.logger.debug(f"История обновлена, теперь {len(hist)} сообщений")

                await telegram.send_response(message, response, start_time)

                total = time.time() - start_time
                settings.logger.info(
                    f"📊 Статистика: пользователь={user_id}, режим={use_mode}, "
                    f"генерация={helpers.format_time_detailed(gen_time)}, "
                    f"всего={helpers.format_time_detailed(total)}, "
                    f"ответ={len(response)} симв."
                )
            else:
                settings.logger.error("❌ Модель не дала ответа")
                await message.answer("😕 Модель не ответила. Попробуйте /test")

        except Exception as e:
            await thinking.delete()
            settings.logger.error(f"❌ Ошибка обработки: {e}", exc_info=True)
            await message.answer(f"❌ Ошибка: {str(e)[:100]}")
        finally:
            history.set_user_processing(user_id, False)
            settings.logger.debug(f"Обработка для {user_id} завершена")