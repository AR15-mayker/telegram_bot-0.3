from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from bot.config import *
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class Keyboards:
    @staticmethod
    def main():
        # Реализация клавиатуры
        pass

class Keyboards:
    @staticmethod
    def main():
        """Главное меню"""
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📅 Календарь")],
                [KeyboardButton(text="📝 Мои события")],
                [KeyboardButton(text="⏰ Напоминания")]
            ],
            resize_keyboard=True
        )

    @staticmethod
    async def events(user_id: int, page: int = 0):
        # Логика формирования клавиатуры событий
        return InlineKeyboardMarkup(inline_keyboard=[])

    @staticmethod
    def confirm(confirm_data: str, cancel_data: str):
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=confirm_data),
                InlineKeyboardButton(text="❌ Нет", callback_data=cancel_data)
            ]
        ])

    @staticmethod
    def back():
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
        ])
    

@staticmethod
async def calendar():
    """Клавиатура календаря"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Выбрать дату", callback_data="open_calendar")]
    ])