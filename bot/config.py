import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
DB_NAME = "events.db"
ITEMS_PER_PAGE = 5
REMINDER_CHECK_INTERVAL = 60

# Префиксы для callback-данных
DELETE_PREFIX = "del_"
CONFIRM_PREFIX = "cfm_"
CANCEL_PREFIX = "cnl_"
PAGE_PREFIX = "page_"
REMIND_PREFIX = "rem_"

# Добавляем настройки модерации
BANNED_WORDS = ["мат1", "мат2", "оскорбление"]  # Список запрещенных слов
ADMINS = [12345678]  # ID администраторов
ANTI_FLOOD_RATE = 3  # Макс. сообщений в секунду