from aiogram import types
from aiogram.fsm.context import FSMContext
from bot.keyboards import Keyboards

async def handle_calendar(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.message.edit_text(
            "Выберите дату:",
            reply_markup=await Keyboards.calendar()
        )
        await callback.answer()
    except Exception as e:
        await callback.message.answer("Ошибка при открытии календаря")
        await callback.answer()
