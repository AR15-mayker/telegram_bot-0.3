from aiogram import F, types
from aiogram.filters import Command
from bot.keyboards import Keyboards

async def start_cmd(message: types.Message):
    """Обработчик команды /start"""
    await message.answer(
        "Привет! Я бот для управления событиями.\n\n"
        "Доступные команды:\n"
        "/calendar - добавить дату\n"
        "/events - просмотреть события",
        reply_markup=Keyboards.main()
    )

async def calendar_cmd(message: types.Message):
    """Обработчик команды /calendar"""
    await message.answer(
        "Выберите дату:",
        reply_markup=await Keyboards.calendar()
    )

async def events_cmd(message: types.Message):
    """Обработчик команды /events"""
    user_id = message.from_user.id
    await message.answer(
        "Ваши события:",
        reply_markup=await Keyboards.events(user_id)
    )
