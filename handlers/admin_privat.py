from typing import List, Dict
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram import F, Bot
from loguru import logger
from database import Database

class AdminPrivileges:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.admin_ids = self._load_admin_ids()
        
    def _load_admin_ids(self) -> List[int]:
        """Загружает ID администраторов из базы данных"""
        try:
            rows = Database.execute_query(
                "SELECT user_id FROM admins",
                fetch=True
            )
            return [row[0] for row in rows] if rows else []
        except Exception as e:
            logger.error(f"Error loading admin IDs: {e}")
            return []

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        return user_id in self.admin_ids

    async def get_all_users(self) -> List[Dict]:
        """Получает список всех пользователей (только для админов)"""
        if not self.admin_ids:
            return []
            
        try:
            rows = Database.execute_query(
                "SELECT user_id, username, first_name, last_name FROM users",
                fetch=True
            )
            return [{
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'last_name': row[3]
            } for row in rows]
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            return []

    async def get_user_stats(self, user_id: int) -> Dict:
        """Получает статистику пользователя (только для админов)"""
        try:
            event_count = Database.execute_query(
                "SELECT COUNT(*) FROM events WHERE user_id = ?",
                (user_id,),
                fetch=True
            )[0][0]
            
            last_event = Database.execute_query(
                "SELECT date, text FROM events WHERE user_id = ? ORDER BY date DESC LIMIT 1",
                (user_id,),
                fetch=True
            )
            
            return {
                'event_count': event_count,
                'last_event': last_event[0] if last_event else None
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}

    async def broadcast_message(self, message: Message) -> bool:
        """Отправляет сообщение всем пользователям (только для админов)"""
        if not self.is_admin(message.from_user.id):
            return False
            
        try:
            users = await self.get_all_users()
            for user in users:
                try:
                    await self.bot.send_message(
                        user['user_id'],
                        f"📢 Администратор сообщает:\n{message.text}"
                    )
                except Exception as e:
                    logger.warning(f"Can't send to user {user['user_id']}: {e}")
            return True
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            return False

    async def add_admin(self, message: Message) -> bool:
        """Добавляет нового администратора"""
        if not self.is_admin(message.from_user.id):
            return False
            
        try:
            target_id = int(message.text.split()[1])
            Database.execute_query(
                "INSERT OR IGNORE INTO admins (user_id) VALUES (?)",
                (target_id,)
            )
            self.admin_ids = self._load_admin_ids()  # Обновляем кэш
            return True
        except (IndexError, ValueError) as e:
            logger.error(f"Invalid admin add command: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding admin: {e}")
            return False

# Регистрация обработчиков команд для администратора
def register_admin_handlers(dp: Dispatcher, admin_priv: AdminPrivileges):
    # Команда для получения статистики
    @dp.message(Command("stats"))
    async def admin_stats(message: Message):
        if not admin_priv.is_admin(message.from_user.id):
            return
            
        stats = await admin_priv.get_user_stats(message.from_user.id)
        await message.answer(
            f"📊 Ваша статистика:\n"
            f"Событий: {stats['event_count']}\n"
            f"Последнее: {stats['last_event'][0] if stats['last_event'] else 'нет'}"
        )

    # Команда для трансляции сообщения
    @dp.message(Command("broadcast"))
    async def broadcast_cmd(message: Message):
        if not admin_priv.is_admin(message.from_user.id):
            return
            
        if len(message.text.split()) < 2:
            await message.answer("Используйте: /broadcast текст сообщения")
            return
            
        if await admin_priv.broadcast_message(message):
            await message.answer("✅ Сообщение отправлено всем пользователям")
        else:
            await message.answer("❌ Ошибка при отправке сообщения")

    # Команда для добавления администратора
    @dp.message(Command("addadmin"))
    async def add_admin_cmd(message: Message):
        if not admin_priv.is_admin(message.from_user.id):
            return
            
        if len(message.text.split()) < 2:
            await message.answer("Используйте: /addadmin user_id")
            return
            
        if await admin_priv.add_admin(message):
            await message.answer("✅ Новый администратор добавлен")
        else:
            await message.answer("❌ Ошибка при добавлении администратора")
