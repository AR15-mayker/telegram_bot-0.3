import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from loguru import logger
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
CHANNEL_ID = os.getenv("CHANNEL_ID")

class HolidaySender:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        
    async def fetch_holidays(self):
        """Получение праздников с calend.ru"""
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://www.calend.ru/day/{today}/"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Парсим основные праздники
                    main_holidays = []
                    for item in soup.select('.itemsNet .title'):
                        holiday = item.get_text(strip=True)
                        if holiday and len(holiday) > 3:
                            main_holidays.append(holiday)
                    
                    # Парсим профессиональные праздники
                    prof_holidays = []
                    for item in soup.select('.professional .title'):
                        holiday = item.get_text(strip=True)
                        if holiday:
                            prof_holidays.append(holiday)
                    
                    return {
                        "date": datetime.now().strftime("%d.%m.%Y"),
                        "main": main_holidays[:5],  # Берем первые 5 основных
                        "professional": prof_holidays[:3]  # И 3 профессиональных
                    }
        except Exception as e:
            logger.error(f"Ошибка парсинга: {e}")
            return None

    async def send_holidays(self):
        """Отправка праздников в канал"""
        holidays = await self.fetch_holidays()
        if not holidays:
            logger.warning("Не удалось получить праздники")
            return
            
        message = f"🎉 Праздники на {holidays['date']}:\n\n"
        
        if holidays['main']:
            message += "📅 Основные праздники:\n"
            message += "\n".join(f"• {h}" for h in holidays['main']) + "\n\n"
        
        if holidays['professional']:
            message += "👔 Профессиональные:\n"
            message += "\n".join(f"• {h}" for h in holidays['professional'])
        
        try:
            await self.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                disable_web_page_preview=True
            )
            logger.success("Праздники отправлены в канал")
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")

    async def cleanup(self):
        """Закрытие сессии"""
        await self.session.close()


async def scheduled_sender(bot: Bot):
    """Задача для регулярной отправки"""
    sender = HolidaySender(bot)
    try:
        while True:
            now = datetime.now()
            # Отправляем в 9:00 утра
            if now.hour == 9 and now.minute == 0:
                await sender.send_holidays()
            await asyncio.sleep(60)  # Проверяем каждую минуту
    finally:
        await sender.cleanup()


def setup_channel_handlers(dp: Dispatcher, bot: Bot):
    # Запускаем фоновую задачу
    asyncio.create_task(scheduled_sender(bot))
    
    @dp.message(Command('holidays'), F.chat.type == "channel")
    async def manual_send(message: types.Message):
        """Ручная отправка праздников"""
        sender = HolidaySender(bot)
        await sender.send_holidays()
        await sender.cleanup()
        await message.answer("Праздники отправлены!")
