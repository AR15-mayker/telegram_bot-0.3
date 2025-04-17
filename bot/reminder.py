import asyncio
from bot.config import REMINDER_CHECK_INTERVAL
from bot.database import Database

async def check_reminders():
    while True:
        # Проверка напоминаний
        await asyncio.sleep(REMINDER_CHECK_INTERVAL)
