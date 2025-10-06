import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import settings
from handlers import admin, menu
from utils.greetings import get_random_greeting
from aiogram.types import FSInputFile
from pathlib import Path
from services.storage_service import StorageService
from services.chat_storage import load_chat_id


logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=settings.TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone="Asia/Almaty")


def setup_routers():
    dp.include_router(admin.router)
    dp.include_router(menu.router)


async def send_daily_birthdays():
    chat_id = load_chat_id()
    if not chat_id:
        return

    BASE_DIR = Path(__file__).parent
    photos_dir = BASE_DIR / "photos"
    storage = StorageService()
    employees_today = storage.get_today_birthdays()

    if not employees_today:
        return

    for emp in employees_today:
        greeting = get_random_greeting(emp["name"])
        text = f"{emp['telegram']} {greeting}"
        photo_path = photos_dir / emp["photo"]

        if photo_path.exists() and photo_path.is_file():
            photo_file = FSInputFile(str(photo_path.resolve()))
            await bot.send_photo(
                chat_id=chat_id,
                photo=photo_file,
                caption=text
            )
        else:
            await bot.send_message(chat_id, greeting)


async def send_monthly_birthdays():
    chat_id = load_chat_id()
    if not chat_id:
        return

    storage = StorageService()
    all_employees = storage.get_all()

    current_month = datetime.now().month
    month_birthdays = [
        emp for emp in all_employees
        if datetime.strptime(emp["birthday"], "%Y-%m-%d").month == current_month
    ]

    if not month_birthdays:
        return await bot.send_message(chat_id, "🎂 В этом месяце нет именинников.")

    text = f"🎉 <b>Именинники в этом месяце:</b>\n\n"

    for emp in month_birthdays:
        text += f"🎂 <b>{emp['name']}</b> — {emp['birthday']} ({emp['telegram']})\n"

    await bot.send_message(chat_id, text)


async def main():

    setup_routers()

    scheduler.add_job(
        send_daily_birthdays,
        "cron",
        hour=settings.HOUR,
        minute=settings.MINUTE
    )

    scheduler.add_job(
        send_monthly_birthdays,
        "cron",
        day=1,
        hour=settings.HOUR,
        minute=settings.MINUTE,
    )

    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
