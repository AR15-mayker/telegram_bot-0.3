import sys
import os
import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, ChatTypeFilter # type: ignore
from aiogram.enums import ChatType

# Настройка пути для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Импорты модулей
from database import Database
from moderation import Moderation
from games import ChatGames

# Инициализация бота
async def main():
    bot = Bot(token="YOUR_BOT_TOKEN")  # Замените на реальный токен
    dp = Dispatcher()
    
    # Инициализация модулей
    db = Database()
    await db.init_db()  # Асинхронная инициализация БД
    
    # Инициализация систем
    moderation = Moderation(dp)
    games_system = ChatGames(dp)
    
    # Базовые обработчики команд
    @dp.message(Command("start"))
    async def start_cmd(message: types.Message):
        await message.answer("Добро пожаловать в бота!")
    
    @dp.message(Command("help"))
    async def help_cmd(message: types.Message):
        help_text = (
            "Доступные команды:\n"
            "/start - начать работу\n"
            "/help - помощь\n"
            "/dice - игра в кости\n"
            "/quiz - викторина\n"
            "/events - мероприятия\n"
            "/calendar - календарь событий\n\n"
            "Для модераторов:\n"
            "/warn - выдать предупреждение\n"
            "/reset_warns - сбросить предупреждения"
        )
        await message.answer(help_text)
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
