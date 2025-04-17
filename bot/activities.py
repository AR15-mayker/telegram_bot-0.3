from aiogram import types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random

class Activities:
    def __init__(self, dp):
        dp.message.register(self.start_activities, Command("activities"))
        dp.callback_query.register(self.handle_activity, F.data.startswith("activity_"))
        
        self.quiz_questions = {
            "Какая столица Франции?": ["Лондон", "Париж", "Берлин", 1],
            "2+2*2": ["6", "8", "4", 0]
        }
        self.active_games = {}

    async def start_activities(self, message: types.Message):
        """Меню активностей"""
        builder = InlineKeyboardBuilder()
        builder.add(
            types.InlineKeyboardButton(
                text="Викторина",
                callback_data="activity_quiz"
            ),
            types.InlineKeyboardButton(
                text="Крокодил",
                callback_data="activity_crocodile"
            ),
            types.InlineKeyboardButton(
                text="Правда/Ложь",
                callback_data="activity_truth"
            )
        )
        await message.answer(
            "🎲 Выберите активность:",
            reply_markup=builder.as_markup()
        )

    async def handle_activity(self, callback: types.CallbackQuery):
        """Обработчик выбора активности"""
        activity_type = callback.data.split("_")[1]
        
        if activity_type == "quiz":
            await self.start_quiz(callback.message.chat.id)
        elif activity_type == "crocodile":
            await self.start_crocodile(callback.message.chat.id)
        
        await callback.answer()

    async def start_quiz(self, chat_id: int):
        """Запуск викторины"""
        question, answers = random.choice(list(self.quiz_questions.items()))
        correct_idx = answers[-1]
        
        await self.bot.send_poll(
            chat_id=chat_id,
            question=question,
            options=answers[:-1],
            type="quiz",
            correct_option_id=correct_idx,
            is_anonymous=False
        )

    async def start_crocodile(self, chat_id: int):
        """Игра в Крокодила"""
        words = ["Телефон", "Самолет", "Программист", "Библиотека"]
        word = random.choice(words)
        
        self.active_games[chat_id] = {
            "word": word,
            "guessed": False
        }
        
        await self.bot.send_message(
            chat_id,
            f"🎭 Игра 'Крокодил' началась!\n"
            f"Подсказка: слово из {len(word)} букв\n"
            f"Первая буква: {word[0]}"
        )
