import re
from aiogram import types
from datetime import timedelta
from collections import defaultdict

class Moderation:
    def __init__(self):
        self.banned_patterns = [
            r"\b(плохое|слово|мат\w*)\b",  # Базовые запрещенные слова
            r"\b[а-я]*ху[а-я]*\b",        # Вариации мата
            r"\b[а-я]*бля[а-я]*\b",
            r"\b[а-я]*пизд[а-я]*\b",
            r"(?i)\b(дурак|идиот)\b"      # Case-insensitive
        ]
        self.warnings = defaultdict(int)   # Система предупреждений

    async def check_message(self, message: types.Message):
        """Проверка сообщения на запрещенные слова"""
        if not message.text:
            return

        text = message.text.lower()
        for pattern in self.banned_patterns:
            if re.search(pattern, text):
                await self.process_violation(message)
                break

    async def process_violation(self, message: types.Message):
        """Обработка нарушения"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # 1. Удаляем сообщение
        try:
            await message.delete()
        except:
            pass
        
        # 2. Увеличиваем счетчик предупреждений
        self.warnings[user_id] += 1
        warnings_count = self.warnings[user_id]
        
        # 3. Отправляем предупреждение
        warning_msg = await message.answer(
            f"⚠️ {message.from_user.full_name}, нарушение правил чата!\n"
            f"Предупреждение {warnings_count}/3"
        )
        
        # 4. При 3+ предупреждениях бан
        if warnings_count >= 3:
            await message.chat.ban(
                user_id=user_id,
                until_date=timedelta(hours=24)
            )
            await warning_msg.edit_text(
                f"⛔ Пользователь {message.from_user.full_name} забанен на 24 часа "
                f"за 3 нарушения правил"
            )
            self.warnings[user_id] = 0  # Сброс счетчика

    async def warn_user(self, message: types.Message):
        """Ручное предупреждение (команда /warn)"""
        if not message.reply_to_message:
            return await message.reply("Ответьте на сообщение пользователя!")
        
        user_id = message.reply_to_message.from_user.id
        self.warnings[user_id] += 1
        count = self.warnings[user_id]
        
        await message.reply(
            f"Пользователь {message.reply_to_message.from_user.full_name} "
            f"получил предупреждение ({count}/3)"
        )
        
        if count >= 3:
            await message.chat.ban(
                user_id=user_id,
                until_date=timedelta(hours=24)
            )
            await message.reply("Пользователь забанен на 24 часа!")
            self.warnings[user_id] = 0

    async def reset_warns(self, message: types.Message):
        """Сброс предупреждений (команда /reset_warns)"""
        if not message.reply_to_message:
            return await message.reply("Ответьте на сообщение пользователя!")
        
        user_id = message.reply_to_message.from_user.id
        self.warnings[user_id] = 0
        await message.reply("Предупреждения сброшены!")
