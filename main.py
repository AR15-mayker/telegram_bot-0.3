import os
import asyncio
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime
from dotenv import load_dotenv
from loguru import logger

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

bot = Bot(TOKEN)
dp = Dispatcher()

# Улучшенное хранилище для событий
user_events = {}  # Формат: {user_id: {event_id: {"date": date_str, "text": event_text}}}

# Константы для callback-данных
DELETE_PREFIX = "del_"
CONFIRM_PREFIX = "cfm_"
CANCEL_PREFIX = "cnl_"
PAGE_PREFIX = "page_"
ITEMS_PER_PAGE = 5

# Обработчик команды /start
@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer(
        "📅 Улучшенный бот-календарь\n\n"
        "Доступные команды:\n"
        "/calendar - добавить дату\n"
        "/myevents - мои события\n"
        "/today - сегодняшняя дата\n"
        "/clearevents - очистить все события",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчик команды /today
@dp.message(Command("today"))
async def today_cmd(message: types.Message):
    today = datetime.now().strftime("%d.%m.%Y")
    logger.debug(f"User {message.from_user.id} requested today's date")
    await message.answer(f"📆 Сегодня: {today}")

# Обработчик команды /calendar
@dp.message(Command("calendar"))
async def calendar_cmd(message: types.Message):
    logger.info(f"User {message.from_user.id} opened calendar")
    await message.answer(
        "Выберите дату для добавления:",
        reply_markup=await SimpleCalendar().start_calendar()
    )

# Обработчик команды /myevents
@dp.message(Command("myevents"))
async def show_events(message: types.Message, page: int = 0):
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested their events (page {page})")
    
    if user_id not in user_events or not user_events[user_id]:
        await message.answer("📭 У вас нет сохраненных событий.")
        return
    
    events = list(user_events[user_id].items())
    total_pages = (len(events) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    # Получаем события для текущей страницы
    page_events = events[page*ITEMS_PER_PAGE:(page+1)*ITEMS_PER_PAGE]
    
    events_text = "📅 Ваши события:\n\n"
    for i, (event_id, event_data) in enumerate(page_events, 1):
        events_text += f"{i}. {event_data['date']} - {event_data['text']}\n"
    
    # Создаем клавиатуру с пагинацией
    keyboard = []
    
    # Кнопки удаления для каждого события
    for event_id, event_data in page_events:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ Удалить {event_data['date']}",
                callback_data=f"{DELETE_PREFIX}{event_id}"
            )
        ])
    
    # Кнопки пагинации
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"{PAGE_PREFIX}{page-1}"
            )
        )
    if page < total_pages - 1:
        pagination_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"{PAGE_PREFIX}{page+1}"
            )
        )
    
    if pagination_buttons:
        keyboard.append(pagination_buttons)
    
    keyboard.append([
        InlineKeyboardButton(
            text="🗑️ Очистить все",
            callback_data="clear_all"
        )
    ])
    
    await message.answer(
        f"{events_text}\nСтраница {page+1}/{total_pages}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

# Обработчик команды /clearevents
@dp.message(Command("clearevents"))
async def clear_events_cmd(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_events and user_events[user_id]:
        await message.answer(
            "Вы уверены, что хотите удалить ВСЕ события?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Да", callback_data="confirm_clear_all"),
                    InlineKeyboardButton(text="❌ Нет", callback_data="cancel_clear_all")
                ]
            ])
        )
    else:
        await message.answer("У вас нет событий для удаления.")

# Обработчик выбора даты в календаре
@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: SimpleCalendarCallback):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        user_id = callback_query.from_user.id
        date_str = date.strftime('%d.%m.%Y')
        event_id = str(uuid.uuid4())
        
        if user_id not in user_events:
            user_events[user_id] = {}
        
        # Проверяем, есть ли уже событие на эту дату
        existing_event = next((e for e in user_events[user_id].values() if e['date'] == date_str), None)
        if existing_event:
            logger.warning(f"User {user_id} tried to add existing date {date_str}")
            await callback_query.message.answer(f"⚠️ Дата {date_str} уже есть в вашем календаре!")
        else:
            user_events[user_id][event_id] = {
                "date": date_str,
                "text": "Мое событие"  # Можно заменить на запрос описания
            }
            logger.success(f"User {user_id} added new date: {date_str} (ID: {event_id})")
            await callback_query.message.answer(
                f"✅ Добавлена дата: {date_str}\n"
                f"ID: {event_id}\n"
                f"Используйте /myevents для просмотра всех событий",
                reply_markup=ReplyKeyboardRemove()
            )

# Обработчик удаления конкретного события
@dp.callback_query(F.data.startswith(DELETE_PREFIX))
async def delete_event_handler(callback_query: types.CallbackQuery):
    event_id = callback_query.data[len(DELETE_PREFIX):]
    user_id = callback_query.from_user.id
    
    if user_id in user_events and event_id in user_events[user_id]:
        event_date = user_events[user_id][event_id]['date']
        await callback_query.message.edit_text(
            f"Вы точно хотите удалить событие на {event_date}?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Да, удалить",
                        callback_data=f"{CONFIRM_PREFIX}{event_id}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Нет, отмена",
                        callback_data=f"{CANCEL_PREFIX}{event_id}"
                    )
                ]
            ])
        )
    else:
        await callback_query.answer("Событие не найдено!")

# Обработчик подтверждения удаления
@dp.callback_query(F.data.startswith(CONFIRM_PREFIX))
async def confirm_delete_handler(callback_query: types.CallbackQuery):
    event_id = callback_query.data[len(CONFIRM_PREFIX):]
    user_id = callback_query.from_user.id
    
    if user_id in user_events and event_id in user_events[user_id]:
        event_date = user_events[user_id][event_id]['date']
        del user_events[user_id][event_id]
        logger.success(f"User {user_id} deleted event {event_id} ({event_date})")
        
        # Возвращаемся к списку событий
        await callback_query.message.edit_text(
            f"🗑️ Событие на {event_date} удалено!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку событий", callback_data="back_to_events")]
            ])
        )
    else:
        await callback_query.answer("Событие не найдено!")

# Обработчик отмены удаления
@dp.callback_query(F.data.startswith(CANCEL_PREFIX))
async def cancel_delete_handler(callback_query: types.CallbackQuery):
    event_id = callback_query.data[len(CANCEL_PREFIX):]
    user_id = callback_query.from_user.id
    
    if user_id in user_events and event_id in user_events[user_id]:
        event_date = user_events[user_id][event_id]['date']
        await callback_query.message.edit_text(
            f"❌ Удаление события на {event_date} отменено",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К списку событий", callback_data="back_to_events")]
            ])
        )

# Обработчик очистки всех событий
@dp.callback_query(F.data == "confirm_clear_all")
async def confirm_clear_all_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_events:
        count = len(user_events[user_id])
        user_events[user_id].clear()
        logger.success(f"User {user_id} cleared all events ({count} removed)")
        await callback_query.message.edit_text(
            f"🗑️ Удалено {count} событий!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 В меню", callback_data="back_to_menu")]
            ])
        )

@dp.callback_query(F.data == "cancel_clear_all")
async def cancel_clear_all_handler(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text(
        "❌ Удаление всех событий отменено",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К списку событий", callback_data="back_to_events")]
        ])
    )

# Обработчик пагинации
@dp.callback_query(F.data.startswith(PAGE_PREFIX))
async def handle_pagination(callback_query: types.CallbackQuery):
    page = int(callback_query.data[len(PAGE_PREFIX):])
    await show_events(callback_query.message, page)

# Обработчик возврата к списку событий
@dp.callback_query(F.data == "back_to_events")
async def back_to_events_handler(callback_query: types.CallbackQuery):
    await show_events(callback_query.message)

# Обработчик возврата в меню
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu_handler(callback_query: types.CallbackQuery):
    await start_cmd(callback_query.message)

# Обработчик ошибок
async def on_startup():
    logger.info("Bot started")

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
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
