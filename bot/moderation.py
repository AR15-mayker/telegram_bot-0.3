import re
from aiogram import types, Dispatcher
from aiogram.filters import Command, ChatTypeFilter
from aiogram.enums import ChatType
from datetime import timedelta
from collections import defaultdict
import logging
from config import BANNED_WORDS  # Импорт из config.py

logger = logging.getLogger(__name__)

class Moderation:
    def __init__(self, dp: Dispatcher):
        self.banned_patterns = BANNED_WORDS
        self.warnings = defaultdict(int)
        
        dp.message.register(
            self.warn_user,
            Command("warn"),
            ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP])
        )
        dp.message.register(
            self.reset_warns,
            Command("reset_warns"),
            ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP])
        )
        dp.message.register(
            self.check_message,
            ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP])
        )

    async def _check_bot_permissions(self, message: types.Message) -> bool:
        if message.chat.type == ChatType.PRIVATE:
            return True
        bot_member = await message.chat.get_member(message.bot.id)
        return bot_member.can_delete_messages and bot_member.can_restrict_members

    async def check_message(self, message: types.Message):
        if not message.text or not await self._check_bot_permissions(message):
            return

        text = message.text.lower()
        for pattern in self.banned_patterns:
            if re.search(pattern, text):
                await self.process_violation(message)
                break

    # ... остальные методы класса ...