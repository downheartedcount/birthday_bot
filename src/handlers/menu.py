from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message

from handlers.admin import list_employees, today_birthdays, menu_add_hr, menu_remove_hr, menu_search_employee, \
    start_add_employee
from services.hr_storage import HR_IDS
from users.filters import is_hr

router = Router()
# --- Главное меню HR ---
def hr_main_kb():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить HR")],
            [KeyboardButton(text="🗑 Удалить HR")],
            [KeyboardButton(text="➕ Добавить сотрудника")],
            [KeyboardButton(text="🔍 Найти сотрудника")],
            [KeyboardButton(text="📋 Список сотрудников")],
            [KeyboardButton(text="👥 Список HR")],
            [KeyboardButton(text="🎂 Сегодняшние дни рождения")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )
    return kb

# --- Хендлер вызова меню HR ---
@router.message(F.chat.type == "private", Command('menu'))
async def hr_menu(message: Message):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    await message.answer("Выберите действие:", reply_markup=hr_main_kb())


# --- Кнопки меню ---
@router.message(F.chat.type == "private", F.text == "📋 Список сотрудников")
async def menu_list_employees(message: Message):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    await list_employees(message)


@router.message(F.chat.type == "private", F.text == "🎂 Сегодняшние дни рождения")
async def menu_today_birthdays(message: Message):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    await today_birthdays(message)


@router.message(F.chat.type == "private", F.text == "➕ Добавить HR")
async def menu_add_hr_button(message: Message, state: FSMContext):
    await menu_add_hr(message, state)


@router.message(F.chat.type == "private", F.text == "🗑 Удалить HR")
async def menu_remove_hr_button(message: Message, state: FSMContext):
    await menu_remove_hr(message, state)


@router.message(F.text == "🔍 Найти сотрудника")
async def menu_search_employee_button(message: Message, state: FSMContext):
    await menu_search_employee(message, state)


@router.message(F.text == "👥 Список HR")
async def list_hr_menu(message: Message):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")

    if not HR_IDS:
        await message.answer("👥 Сейчас нет HR.")
        return

    text = "👥 <b>Текущие HR:</b>\n\n"
    for hr in HR_IDS:
        text += f"🆔 <a href='tg://user?id={hr}'>{hr}</a>\n"

    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "➕ Добавить сотрудника")
async def menu_add_employee(message: Message, state):
    await start_add_employee(message, state)
