import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import Database 

import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command

# Относительные импорты
from .database import Database
from .moderation import Moderation
from .games import ChatGames
from .handlers import start_cmd, calendar_cmd, events_cmd
from .callbacks import handle_calendar

async def main():
    bot = Bot("YOUR_BOT_TOKEN")  # Замените на реальный токен
    dp = Dispatcher()

    # Инициализация модулей
    Database.init_db()
    moderation = Moderation()
    games = ChatGames(dp)

    # Регистрация обработчиков
    dp.message.register(start_cmd, Command("start"))
    dp.message.register(calendar_cmd, Command("calendar"))
    dp.message.register(events_cmd, Command("events"))
    dp.callback_query.register(handle_calendar, F.data == "open_calendar")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
