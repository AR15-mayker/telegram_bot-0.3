from aiogram import types, Dispatcher
from aiogram.filters import Command, ChatTypeFilter
from aiogram.enums import ChatType
import random
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ChatGames:
    def __init__(self, dp: Dispatcher):
        self.quizzes: List[Dict] = [
            {
                "question": "Сколько будет 2+2*2?",
                "options": ["6", "8", "4"],
                "answer": 0,
                "explanation": "Правильный ответ: 6 (сначала умножение!)"
            },
            # ... другие викторины
        ]
        self.register_handlers(dp)

    def register_handlers(self, dp: Dispatcher):
        dp.message.register(
            self.dice_game,
            Command("dice"),
            ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP, ChatType.PRIVATE])
        )
        dp.message.register(
            self.quiz_game,
            Command("quiz"),
            ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP, ChatType.PRIVATE])
        )
        dp.message.register(
            self.quiz_list,
            Command("quizzes"),
            ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP, ChatType.PRIVATE])
        )

    async def _check_bot_permissions(self, message: types.Message) -> bool:
        if message.chat.type == ChatType.PRIVATE:
            return True
            
        bot_member = await message.chat.get_member(message.bot.id)
        return bot_member.can_send_polls

    async def dice_game(self, message: types.Message):
        try:
            dice = await message.answer_dice(emoji="🎲")
            logger.info(f"Dice game by {message.from_user.id} in chat {message.chat.id}")
        except Exception as e:
            logger.error(f"Dice error: {e}")
            await message.answer("⚠️ Не удалось отправить dice")

    async def quiz_game(self, message: types.Message):
        if not await self._check_bot_permissions(message):
            await message.answer("❌ Мне нужны права на отправку опросов!")
            return

        try:
            quiz = random.choice(self.quizzes)
            await message.answer_poll(
                question=quiz["question"],
                options=quiz["options"],
                correct_option_id=quiz["answer"],
                type="quiz",
                is_anonymous=False,
                explanation=quiz["explanation"],
                open_period=30
            )
        except Exception as e:
            logger.error(f"Quiz error: {e}")
            await message.answer(f"⚠️ Ошибка: {e}")

    async def quiz_list(self, message: types.Message):
        try:
            text = "📚 Доступные викторины:\n\n" + "\n".join(
                f"{i}. {q['question']}" for i, q in enumerate(self.quizzes, 1)
            )
            await message.answer(text)
        except Exception as e:
            logger.error(f"Quiz list error: {e}")
            await message.answer("⚠️ Ошибка при показе списка")
