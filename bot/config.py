import os
from dotenv import load_dotenv

# Загрузка переменных окружения должна быть в начале
load_dotenv()

# Основные настройки бота
TOKEN = os.getenv("BOT_TOKEN")  # Изменил название переменной для стандартизации
DB_NAME = os.getenv("DB_NAME", "events.db")  # Добавил возможность настройки через .env
ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", 5))  # Добавил приведение типа
REMINDER_CHECK_INTERVAL = int(os.getenv("REMINDER_CHECK_INTERVAL", 60))  # В секундах

# Настройки callback-данных
CALLBACK_PREFIXES = {
    "delete": "del_",
    "confirm": "cfm_",
    "cancel": "cnl_",
    "page": "page_",
    "remind": "rem_"
}

# Должно быть:
BANNED_WORDS = [
    r"\b(плохое|слово|мат\w*)\b",
    r"\b[а-я]*ху[а-я]*\b",
    r"\b[а-я]*бля[а-я]*\b",
    r"\b[а-я]*пизд[а-я]*\b",
    r"(?i)\b(дурак|идиот)\b"
]

ADMINS = list(map(int, os.getenv("ADMINS", "1337142737").split(',')))  # Можно указать несколько через запятую
ANTI_FLOOD_RATE = float(os.getenv("ANTI_FLOOD_RATE", 3.0))  # Сообщений в секунду

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")
