from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import F
from loguru import logger
from database import Database

class UserPrivileges:
    def __init__(self):
        self.user_limits = {
            'max_events': 50,  # Максимальное количество событий
            'max_reminders': 20  # Максимальное количество напоминаний
        }

    async def get_user_limits(self, user_id: int) -> Dict:
        """Возвращает лимиты пользователя и текущее использование"""
        try:
            event_count = Database.execute_query(
                "SELECT COUNT(*) FROM events WHERE user_id = ?",
                (user_id,),
                fetch=True
            )[0][0]
            
            reminder_count = Database.execute_query(
                "SELECT COUNT(*) FROM events WHERE user_id = ? AND remind_time IS NOT NULL",
                (user_id,),
                fetch=True
            )[0][0]
            
            return {
                'events': {
                    'current': event_count,
                    'max': self.user_limits['max_events']
                },
                'reminders': {
                    'current': reminder_count,
                    'max': self.user_limits['max_reminders']
                }
            }
        except Exception as e:
            logger.error(f"Error getting user limits: {e}")
            return {}

    async def can_add_event(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь добавить новое событие"""
        limits = await self.get_user_limits(user_id)
        return limits.get('events', {}).get('current', 0) < limits.get('events', {}).get('max', 0)

    async def can_add_reminder(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь добавить новое напоминание"""
        limits = await self.get_user_limits(user_id)
        return limits.get('reminders', {}).get('current', 0) < limits.get('reminders', {}).get('max', 0)

# Регистрация обработчиков команд для пользователя
def register_user_handlers(dp: Dispatcher, user_priv: UserPrivileges):
    # Команда для просмотра лимитов
    @dp.message(Command("limits"))
    async def view_limits(message: Message):
        limits = await user_priv.get_user_limits(message.from_user.id)
        await message.answer(
            f"📊 Ваши лимиты:\n"
            f"Событий: {limits['events']['current']}/{limits['events']['max']}\n"
            f"Напоминаний: {limits['reminders']['current']}/{limits['reminders']['max']}"
        )

    # Проверка лимитов перед добавлением события
    @dp.callback_query(SimpleCalendarCallback.filter())
    async def check_limits_before_add(callback_query: CallbackQuery, callback_data: SimpleCalendarCallback):
        if not await user_priv.can_add_event(callback_query.from_user.id):
            await callback_query.answer(
                "❌ Вы достигли лимита событий! Удалите некоторые, чтобы добавить новые.",
                show_alert=True
            )
            return
        await process_simple_calendar(callback_query, callback_data)  # Оригинальный обработчик

    # Проверка лимитов перед добавлением напоминания
    @dp.callback_query(F.data.startswith(REMIND_PREFIX))
    async def check_reminder_limits(callback_query: CallbackQuery):
        if not await user_priv.can_add_reminder(callback_query.from_user.id):
            await callback_query.answer(
                "❌ Вы достигли лимита напоминаний! Удалите некоторые, чтобы добавить новые.",
                show_alert=True
            )
            return
        await set_reminder_handler(callback_query)  # Оригинальный обработчик
