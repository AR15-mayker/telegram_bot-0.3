import aiosqlite
from bot.config import DB_NAME

class Database:
    @staticmethod
    async def init_db():
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    user_id INTEGER,
                    event_id TEXT,
                    date TEXT,
                    text TEXT,
                    remind_time TEXT,
                    PRIMARY KEY (user_id, event_id)
                )
            """)
            await db.commit()

    @staticmethod
    async def execute(query: str, params: tuple = (), fetch: bool = False):
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(query, params)
            if fetch:
                result = await cursor.fetchall()
                await cursor.close()
                return result
            await db.commit()
            rowcount = cursor.rowcount
            await cursor.close()
            return rowcount
