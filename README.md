# TG DeepSeek Bot

Краткое описание
---------------
Этот репозиторий содержит Telegram-бота DeepSeek — обёртку вокруг локальной/удалённой LLM (по умолчанию настроено на модель `deepseek-r1:8b` и сервер Ollama). Бот принимает запросы из Telegram, отправляет их в LLM и возвращает ответы.

Кому это нужно
---------------
- Разработчикам, желающим запустить локальную версию чат-бота с использованием LLM
- Тем, кто хочет интегрировать локальные модели (Ollama) с Telegram

Файлы конфигурации
-------------------
- Основные зависимости: [requirements.txt](requirements.txt)
- Конфигурация приложения: [config/settings.py](config/settings.py)

Быстрый старт (Windows)
-----------------------
1. Убедитесь, что установлен Python 3.10+ (рекомендуется 3.11).
2. Клонируйте репозиторий и перейдите в папку проекта.
3. Создайте и активируйте виртуальное окружение:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
```

4. Установите зависимости:

```powershell
pip install -r requirements.txt
```

5. Создайте и заполните файл `.env` в корне проекта (при первом импорте `config/settings.py` файл создаётся автоматически с примерами). Обязательные поля:

```
TELEGRAM_TOKEN=ваш_токен_от_BotFather
ADMIN_ID=ваш_numeric_telegram_id
LLM_MODEL=deepseek-r1:8b
LLM_BASE_URL=http://localhost:11434/v1
```

6. Запустите локальный LLM-сервер (если используете Ollama):

```bash
# Запуск Ollama (пример)
ollama serve
# Загрузка модели (пример)
ollama pull deepseek-r1:8b
```

7. Запустите бота:

```powershell
python main.py
```

Дополнительные компоненты (опционально)
-------------------------------------
- ffmpeg — если требуется обработка аудио. Установить через Chocolatey/winget.
- tesseract — если нужна OCR-поддержка.

Примеры установки (Windows):

```powershell
choco install ffmpeg
choco install tesseract
# или через winget
winget install --id=Gyan.FFmpeg
winget install --id=UB-Mannheim.Tesseract
```

Отладка и советы
-----------------
- Ошибка `ADMIN_ID должен быть числом` — проверьте значение в `.env`.
- Если конфигурация сообщает о пустых переменных — откройте [config/settings.py](config/settings.py) и заполните `.env` согласно подсказкам.
- Проверка доступности LLM: откройте в браузере `LLM_BASE_URL` или выполните HTTP-запрос.

Готово к доработке
-------------------
Если хотите, я могу автоматически:
- добавить шаблонный `.env` (с примерными значениями),
- или создать минимальный `README.md` на другом языке.

Лицензия
--------
Смотрите файл `LICENSE` в корне репозитория.
