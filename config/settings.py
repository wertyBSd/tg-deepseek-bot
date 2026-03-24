import os
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Определяем пути
ROOT_DIR = Path(__file__).parent.parent  # Корень проекта (где лежит main.py)
ENV_FILE = ROOT_DIR / '.env'
ENV_EXAMPLE_FILE = ROOT_DIR / '.env.example'


def create_default_env():
    """Создает файл .env с значениями по умолчанию"""
    default_content = """# Telegram Bot Configuration
# Получить токен: @BotFather в Telegram
TELEGRAM_TOKEN=your_telegram_bot_token_here

# Your Telegram ID (для админских команд)
# Узнать: @userinfobot в Telegram
ADMIN_ID=your_telegram_id_here

# Модель DeepSeek
LLM_MODEL=deepseek-r1:8b
LLM_BASE_URL=http://localhost:11434/v1

# Системный промпт (как бот будет себя вести)
LLM_SYSTEM_PROMPT=Ты — дружелюбный чат-бот. Отвечай кратко и понятно.

# Параметры модели
MAX_TOKENS=2048
TEMPERATURE=0.7
TOP_P=0.9
TOP_K=40
REPEAT_PENALTY=1.1

# Таймауты (в секундах)
LLM_TIMEOUT_S=300

# История сообщений
HISTORY_MAX_TURNS=6
HISTORY_MAX_CHARS=4000
HISTORY_SCOPE=user  # user - персональная, chat - общая для чата

# Режим отладки (true/false)
DEBUG=true

# ============================================
# ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:
# ============================================
# 1. TELEGRAM_TOKEN: Получите у @BotFather
# 2. ADMIN_ID: Узнайте у @userinfobot (ваш цифровой ID)
# 3. Убедитесь что Ollama запущена: ollama serve
# 4. Загрузите модель: ollama pull deepseek-r1:8b
# ============================================
"""
    try:
        with open(ENV_FILE, 'w', encoding='utf-8') as f:
            f.write(default_content)
        return True
    except Exception as e:
        print(f"❌ Ошибка создания файла .env: {e}")
        return False


def print_setup_instructions():
    """Выводит инструкцию по настройке"""
    instructions = """
╔══════════════════════════════════════════════════════════════╗
║                 🚀 НАСТРОЙКА БОТА 🚀                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   📁 Создан файл .env с настройками по умолчанию            ║
║                                                              ║
║   ⚠️  НЕОБХОДИМО ЗАПОЛНИТЬ:                                  ║
║   ───────────────────────────────────────────────────────   ║
║   1. TELEGRAM_TOKEN - токен бота (получить у @BotFather)    ║
║   2. ADMIN_ID - ваш Telegram ID (узнать у @userinfobot)     ║
║                                                              ║
║   📋 КАК ПОЛУЧИТЬ:                                           ║
║   ───────────────────────────────────────────────────────   ║
║   • Откройте Telegram                                        ║
║   • Найдите @BotFather → создайте бота → получите токен     ║
║   • Найдите @userinfobot → отправьте /start → узнайте ID    ║
║                                                              ║
║   🔧 ДОПОЛНИТЕЛЬНО:                                          ║
║   ───────────────────────────────────────────────────────   ║
║   • Убедитесь что Ollama запущена: ollama serve             ║
║   • Загрузите модель: ollama pull deepseek-r1:8b            ║
║                                                              ║
║   📝 После заполнения перезапустите бота                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(instructions)


# Проверяем наличие файла .env
if not ENV_FILE.exists():
    print("\n" + "!" * 60)
    print("❌ Файл .env не найден!")
    print("!" * 60 + "\n")

    if create_default_env():
        print_setup_instructions()
    else:
        print("❌ Не удалось создать файл .env")

    sys.exit(1)

# Загружаем .env
load_dotenv(ENV_FILE)

# НАСТРОЙКА ЛОГИРОВАНИЯ
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

log_level = logging.DEBUG if DEBUG else logging.INFO

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("deepseek-bot")

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()

# Проверяем обязательные поля
missing_vars = []

if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "your_telegram_bot_token_here":
    missing_vars.append("TELEGRAM_TOKEN")
if not ADMIN_ID or ADMIN_ID == "your_telegram_id_here":
    missing_vars.append("ADMIN_ID")

if missing_vars:
    logger.error("=" * 60)
    logger.error("❌ ОШИБКА КОНФИГУРАЦИИ")
    logger.error("=" * 60)
    logger.error(f"Не заполнены обязательные поля: {', '.join(missing_vars)}")
    logger.error("\n📝 Инструкция:")
    logger.error("1. Откройте файл .env")
    logger.error("2. Заполните пропущенные значения:")
    for var in missing_vars:
        if var == "TELEGRAM_TOKEN":
            logger.error(f"   • {var} - получите у @BotFather")
        elif var == "ADMIN_ID":
            logger.error(f"   • {var} - узнайте у @userinfobot")
    logger.error("\n3. Перезапустите бота")
    logger.error("=" * 60)
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    logger.error("❌ ADMIN_ID должен быть числом (ваш Telegram ID)")
    logger.error("📝 Узнайте свой ID у @userinfobot")
    sys.exit(1)

# Модель
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:8b").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1").strip().rstrip("/")

# Системный промпт
DEFAULT_SYSTEM_PROMPT = os.getenv("LLM_SYSTEM_PROMPT", "Ты — дружелюбный чат-бот. Отвечай кратко и понятно.").strip()

# Параметры модели
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
TOP_P = float(os.getenv("TOP_P", "0.9"))
TOP_K = int(os.getenv("TOP_K", "40"))
REPEAT_PENALTY = float(os.getenv("REPEAT_PENALTY", "1.1"))

# Таймауты
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "300"))

# История
HISTORY_MAX_TURNS = int(os.getenv("HISTORY_MAX_TURNS", "6"))
HISTORY_MAX_CHARS = int(os.getenv("HISTORY_MAX_CHARS", "4000"))
HISTORY_SCOPE = os.getenv("HISTORY_SCOPE", "user").strip().lower()

# Проверяем подключение к Ollama при старте (опционально)
if __name__ != "__main__":
    # Это не основной запуск, просто импорт
    pass
else:
    # При прямом запуске проверяем Ollama
    logger.info("🔄 Проверка подключения к Ollama...")
    # Здесь можно добавить проверку, но она будет в main.py