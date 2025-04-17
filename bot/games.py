from aiogram import types, Dispatcher
from aiogram.filters import Command
import random

class ChatGames:
    def __init__(self, dp: Dispatcher):
        dp.message.register(self.dice_game, Command("dice"))
        dp.message.register(self.quiz_game, Command("quiz"))

    async def dice_game(self, message: types.Message):
        await message.answer_dice(emoji="🎲")
        await message.answer("Кто получит больше очков?")

    async def quiz_game(self, message: types.Message):
        question = "Сколько будет 2+2*2?"
        options = ["6", "8", "4"]
        
        await message.answer_poll(
            question=question,
            options=options,
            correct_option_id=0,
            type="quiz"
        )
