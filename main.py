import asyncio
import logging

from config import MAIN_BOT_TOKEN, ADMINS, DB_CONFIG
from aiogram import Bot, Dispatcher
from core.handlers.basic import router
from core.database.database import Database
from core.middlewares.middlewares import DbMiddleware

bot = Bot(token=MAIN_BOT_TOKEN)
dp = Dispatcher()
db = Database(DB_CONFIG)

connection = None
logging.basicConfig(level=logging.INFO)


async def on_startup_bot(bot: Bot):
    """Уведомление админа о старте бота"""
    text = "Бот запущен"
    await bot.send_message(chat_id=ADMINS[0], text=text)
    db.connect()


async def on_shutdown_bot(bot: Bot):
    """Уведомление об остановке бота"""
    text = "Бот остановлен"
    await bot.send_message(chat_id=ADMINS[0], text=text)
    db.close()


async def start():
    # Регистрируем мидлварь для передачи объекта db в обработчики
    dp.message.middleware(DbMiddleware(db))
    dp.callback_query.middleware(DbMiddleware(db))

    dp.include_router(router)
    dp.startup.register(on_startup_bot)
    dp.shutdown.register(on_shutdown_bot)

    try:
        await dp.start_polling(bot)
    finally:
        db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(start())
