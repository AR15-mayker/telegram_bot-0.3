import os
import asyncio
import uuid
from typing import Dict, Any, List, Tuple
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger
import sqlite3
from contextlib import closing
import random

# Настройка логгера
logger.add(
    "bot.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    rotation="1 week",
    compression="zip",
    level="DEBUG"
)

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("Не найден токен бота в переменных окружения!")

bot = Bot(TOKEN)
dp = Dispatcher()

# Константы
DELETE_PREFIX = "del_"
CONFIRM_PREFIX = "cfm_"
CANCEL_PREFIX = "cnl_"
PAGE_PREFIX = "page_"
REMIND_PREFIX = "rem_"
ITEMS_PER_PAGE = 5
DB_NAME = "events.db"
REMINDER_CHECK_INTERVAL = 60

class Database:
    """Класс для работы с базой данных"""
    @staticmethod
    def init_db():
        with closing(sqlite3.connect(DB_NAME)) as conn:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        user_id INTEGER,
                        event_id TEXT,
                        date TEXT,
                        text TEXT,
                        remind_time TEXT,
                        PRIMARY KEY (user_id, event_id)
                    )
                """)

    @staticmethod
    async def execute_query(query: str, params: tuple = (), fetch: bool = False) -> Any:
        with closing(sqlite3.connect(DB_NAME)) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            conn.commit()
            return cursor.rowcount

class EventManager:
    """Класс для управления событиями"""
    @staticmethod
    async def get_user_events(user_id: int) -> Dict[str, Dict[str, str]]:
        rows = await Database.execute_query(
            "SELECT event_id, date, text, remind_time FROM events WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        return {row[0]: {"date": row[1], "text": row[2], "remind_time": row[3]} for row in rows}

    @staticmethod
    async def add_event(user_id: int, event_id: str, date: str, text: str = "Мое событие", remind_time: str = None):
        await Database.execute_query(
            "INSERT INTO events (user_id, event_id, date, text, remind_time) VALUES (?, ?, ?, ?, ?)",
            (user_id, event_id, date, text, remind_time)
        )

    @staticmethod
    async def update_event_reminder(user_id: int, event_id: str, remind_time: str) -> bool:
        return await Database.execute_query(
            "UPDATE events SET remind_time = ? WHERE user_id = ? AND event_id = ?",
            (remind_time, user_id, event_id)
        ) > 0

    @staticmethod
    async def delete_event(user_id: int, event_id: str) -> bool:
        return await Database.execute_query(
            "DELETE FROM events WHERE user_id = ? AND event_id = ?",
            (user_id, event_id)
        ) > 0

    @staticmethod
    async def clear_user_events(user_id: int) -> int:
        count = (await Database.execute_query(
            "SELECT COUNT(*) FROM events WHERE user_id = ?",
            (user_id,),
            fetch=True
        ))[0][0]
        await Database.execute_query(
            "DELETE FROM events WHERE user_id = ?",
            (user_id,)
        )
        return count

    @staticmethod
    async def event_exists(user_id: int, date: str) -> bool:
        return (await Database.execute_query(
            "SELECT 1 FROM events WHERE user_id = ? AND date = ? LIMIT 1",
            (user_id, date),
            fetch=True
        )) is not None

    @staticmethod
    async def get_events_for_reminder() -> List[Tuple[int, str, str]]:
        now = datetime.now().strftime("%d.%m.%Y %H:%M")
        return await Database.execute_query(
            "SELECT user_id, date, text FROM events WHERE remind_time = ?",
            (now,),
            fetch=True
        )

class KeyboardManager:
    """Класс для управления клавиатурами"""
    @staticmethod
    async def get_events_keyboard(user_id: int, page: int) -> InlineKeyboardMarkup:
        events = await EventManager.get_user_events(user_id)
        events_list = list(events.items())
        total_pages = (len(events_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page_events = events_list[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
        
        keyboard = []
        
        for event_id, event_data in page_events:
            row = [
                InlineKeyboardButton(
                    text=f"❌ {event_data['date']}",
                    callback_data=f"{DELETE_PREFIX}{event_id}"
                )
            ]
            if not event_data['remind_time']:
                row.append(InlineKeyboardButton(
                    text="⏰ Напомнить",
                    callback_data=f"{REMIND_PREFIX}{event_id}"
                ))
            keyboard.append(row)
        
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=f"{PAGE_PREFIX}{page-1}"
                ))
        if page < total_pages - 1:
            pagination_buttons.append(
                InlineKeyboardButton(
                    text="Вперед ➡️",
                    callback_data=f"{PAGE_PREFIX}{page+1}"
                ))
        
        if pagination_buttons:
            keyboard.append(pagination_buttons)
        
        keyboard.append([
            InlineKeyboardButton(
                text="🗑️ Очистить все",
                callback_data="clear_all"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def get_confirmation_keyboard(confirm_data: str, cancel_data: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=confirm_data),
                InlineKeyboardButton(text="❌ Нет", callback_data=cancel_data)
            ]
        ])

    @staticmethod
    def get_back_keyboard(back_data: str = "back_to_events") -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data=back_data)]
        ])

class MessageManager:
    """Класс для управления сообщениями"""
    @staticmethod
    async def get_user_events_text(user_id: int, page: int) -> Tuple[str, int]:
        events = await EventManager.get_user_events(user_id)
        events_list = list(events.items())
        total_pages = (len(events_list) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        page_events = events_list[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
        
        events_text = "📅 Ваши события:\n\n"
        for i, (event_id, event_data) in enumerate(page_events, 1):
            reminder_info = f" (⏰ напомнить в {event_data['remind_time']})" if event_data['remind_time'] else ""
            events_text += f"{i}. {event_data['date']} - {event_data['text']}{reminder_info}\n"
        
        return events_text, total_pages

    @staticmethod
    async def display_events_page(message: types.Message, user_id: int, page: int):
        events_text, total_pages = await MessageManager.get_user_events_text(user_id, page)
        keyboard = await KeyboardManager.get_events_keyboard(user_id, page)
        await message.answer(
            f"{events_text}\nСтраница {page+1}/{total_pages}",
            reply_markup=keyboard
        )

    @staticmethod
    async def april_fools_joke(message: types.Message):
        jokes = [
            "⚠️ Внимание! Обнаружена критическая ошибка в системе календаря!",
            "🔧 Технические работы... Попробуйте позже... Гораздо позже...",
            "📅 Календарь временно отключен из-за вторжения хомяков в серверную",
            "💥 Ошибка 418: Я - чайник (и это не шутка!)",
            "🔄 Перезагружаюсь... 5%... 20%... 95%... Ой, снова 5%...",
            "🤖 Я решил уйти в отпуск. Возвращаюсь никогда.",
            "📆 Все ваши даты были случайно отправлены в прошлое. Извините!",
            "💾 Ошибка загрузки модуля юмора. Серьезное сообщение: сегодня 1 апреля! 😄"
        ]
        await message.answer(random.choice(jokes))

async def remind_checker():
    """Проверяет и отправляет напоминания"""
    while True:
        try:
            events = await EventManager.get_events_for_reminder()
            for user_id, date, text in events:
                await bot.send_message(
                    user_id,
                    f"⏰ Напоминание!\n{date} - {text}"
                )
        except Exception as e:
            logger.error(f"Ошибка в remind_checker: {e}")
        await asyncio.sleep(REMINDER_CHECK_INTERVAL)

def is_april_fools_day() -> bool:
    today = datetime.now()
    return today.month == 4 and today.day == 1

async def check_april_fools(message: types.Message) -> bool:
    if is_april_fools_day() and random.random() < 0.5:
        await MessageManager.april_fools_joke(message)
        return True
    return False

# Обработчики команд
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    if await check_april_fools(message):
        return
    
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        "📅 Улучшенный бот-календарь с напоминаниями\n\n"
        "Доступные команды:\n"
        "/calendar - добавить дату\n"
        "/myevents - мои события\n"
        "/today - сегодняшняя дата\n"
        "/clearevents - очистить все события",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(Command("today"))
async def today_cmd(message: types.Message):
    if is_april_fools_day() and random.random() < 0.5:
        await message.answer("📆 Сегодня: 32 марта 2023 года 🤪")
        return
    
    await message.answer(f"📆 Сегодня: {datetime.now().strftime('%d.%m.%Y')}")

@dp.message(Command("calendar"))
async def calendar_cmd(message: types.Message):
    if is_april_fools_day() and random.random() < 0.5:
        await message.answer("📅 Календарь временно недоступен. Попробуйте вчера!")
        return
    
    logger.info(f"User {message.from_user.id} opened calendar")
    await message.answer(
        "Выберите дату для добавления:",
        reply_markup=await SimpleCalendar().start_calendar()
    )

@dp.message(Command("myevents"))
async def show_events(message: types.Message):
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested their events")
    
    if not await EventManager.get_user_events(user_id):
        await message.answer("📭 У вас нет сохраненных событий.")
        return
    
    await MessageManager.display_events_page(message, user_id, 0)

@dp.message(Command("clearevents"))
async def clear_events_cmd(message: types.Message):
    if is_april_fools_day() and random.random() < 0.5:
        await message.answer("❌ Ошибка: не могу очистить события, они все убежали!")
        return
    
    user_id = message.from_user.id
    if await EventManager.get_user_events(user_id):
        await message.answer(
            "Вы уверены, что хотите удалить ВСЕ события?",
            reply_markup=KeyboardManager.get_confirmation_keyboard(
                "confirm_clear_all", "cancel_clear_all"
            )
        )
    else:
        await message.answer("У вас нет событий для удаления.")

# Обработчики callback-запросов
@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: SimpleCalendarCallback):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if not selected:
        return
    
    if is_april_fools_day() and random.random() < 0.3:
        await callback_query.message.answer("📅 Ой! Выбранная дата потерялась в временной петле!")
        return
    
    user_id = callback_query.from_user.id
    date_str = date.strftime('%d.%m.%Y')
    
    if await EventManager.event_exists(user_id, date_str):
        logger.warning(f"User {user_id} tried to add existing date {date_str}")
        await callback_query.message.answer(f"⚠️ Дата {date_str} уже есть в вашем календаре!")
    else:
        event_id = str(uuid.uuid4())
        await EventManager.add_event(user_id, event_id, date_str)
        logger.success(f"User {user_id} added new date: {date_str} (ID: {event_id})")
        await callback_query.message.answer(
            f"✅ Добавлена дата: {date_str}\n"
            f"Используйте /myevents для просмотра всех событий",
            reply_markup=ReplyKeyboardRemove()
        )

@dp.callback_query(F.data.startswith(DELETE_PREFIX))
async def delete_event_handler(callback_query: types.CallbackQuery):
    event_id = callback_query.data[len(DELETE_PREFIX):]
    user_id = callback_query.from_user.id
    events = await EventManager.get_user_events(user_id)
    
    if event_id not in events:
        await callback_query.answer("Событие не найдено!")
        return
    
    await callback_query.message.edit_text(
        f"Вы точно хотите удалить событие на {events[event_id]['date']}?",
        reply_markup=KeyboardManager.get_confirmation_keyboard(
            f"{CONFIRM_PREFIX}{event_id}", f"{CANCEL_PREFIX}{event_id}"
        )
    )

@dp.callback_query(F.data.startswith((CONFIRM_PREFIX, CANCEL_PREFIX)))
async def handle_confirmation(callback_query: types.CallbackQuery):
    prefix = CONFIRM_PREFIX if callback_query.data.startswith(CONFIRM_PREFIX) else CANCEL_PREFIX
    event_id = callback_query.data[len(prefix):]
    user_id = callback_query.from_user.id
    events = await EventManager.get_user_events(user_id)
    
    if event_id not in events:
        await callback_query.answer("Событие не найдено!")
        return
    
    event_date = events[event_id]['date']
    
    if prefix == CONFIRM_PREFIX:
        if await EventManager.delete_event(user_id, event_id):
            logger.success(f"User {user_id} deleted event {event_id} ({event_date})")
            await callback_query.message.edit_text(
                f"🗑️ Событие на {event_date} удалено!",
                reply_markup=KeyboardManager.get_back_keyboard()
            )
    else:
        await callback_query.message.edit_text(
            f"❌ Удаление события на {event_date} отменено",
            reply_markup=KeyboardManager.get_back_keyboard()
        )

@dp.callback_query(F.data.startswith(REMIND_PREFIX))
async def set_reminder_handler(callback_query: types.CallbackQuery):
    event_id = callback_query.data[len(REMIND_PREFIX):]
    user_id = callback_query.from_user.id
    events = await EventManager.get_user_events(user_id)
    
    if event_id not in events:
        await callback_query.answer("Событие не найдено!")
        return
    
    await callback_query.message.answer(
        f"⏰ Установите время напоминания для {events[event_id]['date']} (в формате ЧЧ:ММ):"
    )
    dp["remind_event_id"] = event_id

@dp.message(lambda message: message.text and "remind_event_id" in dp)
async def process_reminder_time(message: types.Message):
    try:
        time_str = message.text.replace(" ", "")
        if ":" not in time_str:
            raise ValueError
        
        hours, minutes = map(int, time_str.split(":"))
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError
        
        user_id = message.from_user.id
        event_id = dp["remind_event_id"]
        events = await EventManager.get_user_events(user_id)
        
        if event_id not in events:
            await message.answer("Событие не найдено")
            return
        
        event_date = events[event_id]['date']
        remind_time = f"{event_date} {hours:02d}:{minutes:02d}"
        
        if await EventManager.update_event_reminder(user_id, event_id, remind_time):
            await message.answer(
                f"⏰ Напоминание установлено на {hours:02d}:{minutes:02d} для даты {event_date}",
                reply_markup=ReplyKeyboardRemove()
            )
            logger.info(f"User {user_id} set reminder for {event_id} at {remind_time}")
        else:
            await message.answer("Ошибка при установке напоминания")
    except:
        await message.answer("Неправильный формат времени. Используйте ЧЧ:ММ")
    finally:
        dp.pop("remind_event_id", None)

@dp.callback_query(F.data == "confirm_clear_all")
async def confirm_clear_all_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    count = await EventManager.clear_user_events(user_id)
    
    if count > 0:
        logger.success(f"User {user_id} cleared all events ({count} removed)")
        text = f"🗑️ Удалено {count} событий!"
    else:
        text = "У вас не было событий для удаления"
    
    await callback_query.message.edit_text(
        text,
        reply_markup=KeyboardManager.get_back_keyboard("back_to_menu")
    )

@dp.callback_query(F.data == "cancel_clear_all")
async def cancel_clear_all_handler(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "❌ Удаление всех событий отменено",
        reply_markup=KeyboardManager.get_back_keyboard()
    )

@dp.callback_query(F.data.startswith(PAGE_PREFIX))
async def handle_pagination(callback_query: types.CallbackQuery):
    page = int(callback_query.data[len(PAGE_PREFIX):])
    await MessageManager.display_events_page(callback_query.message, callback_query.from_user.id, page)

@dp.callback_query(F.data == "back_to_events")
async def back_to_events_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if await EventManager.get_user_events(user_id):
        await MessageManager.display_events_page(callback_query.message, user_id, 0)
    else:
        await callback_query.message.edit_text("📭 У вас нет сохраненных событий.")

@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback_query: types.CallbackQuery):
    await start_cmd(callback_query.message)

# Запуск бота
async def on_startup():
    Database.init_db()
    logger.info("Bot started")
    asyncio.create_task(remind_checker())

async def on_shutdown():
    logger.warning("Bot shutting down")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Polling error: {e}")
    finally:
        logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")