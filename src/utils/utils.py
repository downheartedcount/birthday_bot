import datetime
import json
from typing import List, Dict


def format_birthdays_message(birthdays: List[Dict]) -> str:
    if not birthdays:
        return "🎂 Сегодня именинников нет."

    lines = ["🎉 Сегодня празднуют день рождения:"]
    for emp in birthdays:
        lines.append(
            f"\n👤 {emp['name']}\n"
            f"🎂 {emp['birthday']}\n"
            f"💼 {emp['position']}"
        )
    return "\n".join(lines)


def get_today_birthdays() -> List[Dict]:
    today = datetime.date.today()
    with open("../employees.json", "r", encoding="utf-8") as f:
        employees = json.load(f)

    result = []
    for emp in employees:
        bday = datetime.date.fromisoformat(emp["birthday"])
        if bday.day == today.day and bday.month == today.month:
            result.append(emp)

    return result

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
