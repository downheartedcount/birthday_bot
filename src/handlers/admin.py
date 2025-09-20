import random
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, ChatMemberUpdated, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from services.chat_storage import save_chat_id, load_chat_id
from services.hr_storage import HR_IDS, save_hr
from services.storage_service import StorageService, save_photo
from users.filters import is_hr
from utils.utils import cancel_kb

router = Router()
storage = StorageService()


class AddEmployee(StatesGroup):
    name = State()
    birthday = State()
    telegram = State()
    position = State()
    gender = State()
    photo = State()
    welcome_confirm = State()


class CongratsEmployee(StatesGroup):
    waiting_text = State()

CANCEL_STATES = [
    AddEmployee.name.state,
    AddEmployee.birthday.state,
    AddEmployee.position.state,
    AddEmployee.telegram.state,
    AddEmployee.gender.state,
    AddEmployee.photo.state
]


@router.message(F.chat.type == "private", Command("add_employee"))
async def start_add_employee(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    await state.set_state(AddEmployee.name)
    await message.answer("Введите имя сотрудника:", reply_markup=cancel_kb)


@router.message(F.chat.type == "private",AddEmployee.name, F.text)
async def process_name(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(AddEmployee.birthday)
    await message.answer("Введите дату рождения в формате YYYY-MM-DD:", reply_markup=cancel_kb)


@router.message(F.chat.type == "private",AddEmployee.birthday, F.text)
async def process_birthday(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    from re import match
    text = message.text.strip()
    if not match(r"^\d{4}-\d{2}-\d{2}$", text):
        await message.answer("Неверный формат. Пример: 1995-09-10. Попробуйте ещё раз:")
        return
    await state.update_data(birthday=text)
    await state.set_state(AddEmployee.position)
    await message.answer("Введите должность сотрудника сотрудника", reply_markup=cancel_kb)

@router.message(F.chat.type == "private",AddEmployee.position, F.text)
async def process_position(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    text = message.text.strip()

    await state.update_data(position=text)
    await state.set_state(AddEmployee.telegram)
    await message.answer("Введите Telegram аккаунт сотрудника (например, @username):", reply_markup=cancel_kb)



@router.message(F.chat.type == "private",AddEmployee.telegram, F.text)
async def process_telegram(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    text = message.text.strip()
    if not text.startswith("@"):
        await message.answer("Telegram аккаунт должен начинаться с @. Попробуйте снова:")
        return
    await state.update_data(telegram=text)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Мужчина", callback_data="gender_male"),
                InlineKeyboardButton(text="👩 Женщина", callback_data="gender_female"),
            ]
        ]
    )
    await message.answer("Выберите пол сотрудника:", reply_markup=kb)

@router.callback_query(lambda c: c.data in ["gender_male", "gender_female"])
async def process_gender(query: CallbackQuery, state: FSMContext):
    gender = "male" if query.data == "gender_male" else "female"
    await state.update_data(gender=gender)
    await state.set_state(AddEmployee.photo)
    await query.message.edit_text("Теперь пришлите фотографию сотрудника (как фото, не как файл):")


@router.message(F.chat.type == "private",AddEmployee.photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    safe_name = "_".join(data["name"].split())
    filename = f"{safe_name}.jpg"
    file_id = message.photo[-1].file_id
    await save_photo(message.bot, file_id, filename)

    storage.add_employee(
        name=data["name"],
        birthday=data["birthday"],
        telegram=data["telegram"],
        position=data['position'],
        gender=data['gender'],
        photo_filename=filename
    )
    await state.update_data(photo=filename)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎉 Да", callback_data="welcome_yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data="welcome_no"),
            ]
        ]
    )
    await message.answer(
        f"✅ Сотрудник <b>{data['name']}</b> добавлен!\n"
        "Хотите поздравить его с вступлением в команду?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.set_state(AddEmployee.welcome_confirm)

@router.callback_query(lambda c: c.data in ["welcome_yes", "welcome_no"])
async def process_welcome_callback(query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    BASE_DIR = Path(__file__).parent.parent
    PHOTOS_DIR = BASE_DIR / "photos"
    if current_state != AddEmployee.welcome_confirm.state:
        return

    data = await state.get_data()
    chat_id = load_chat_id()

    await state.clear()

    welcome_templates = [
        "✨ У нас отличная новость! ✨\nСегодня к нам {joined} <b>{name}</b>, {position} 🙌\n\nЖелаем лёгкого старта...",
        "🎉 Команда стала больше и сильнее! 🎉\nСегодня к нам {joined} <b>{name}</b>, {position} ✨\nПусть впереди ждут только победы!",
        "🔥 Отличные новости! 🔥\nК нам {joined} коллега — <b>{name}</b>, {position}. Добро пожаловать!",
        "🎉 Друзья, у нас пополнение! 🎉\nСегодня к нашей команде {joined} <b>{name}</b>, {position}. Добро пожаловать 🚀"
    ]

    if query.data == "welcome_yes":
        gender = data.get("gender", "male")
        joined_word = "присоединился" if gender == "male" else "присоединилась"

        text = random.choice(welcome_templates).format(
            name=data['name'],
            position=data['position'],
            joined=joined_word
        )
        if data.get('telegram'):
            text += f" 💼 {data['telegram']}"

        if data.get("photo"):
            photo_path = PHOTOS_DIR / data["photo"]
            photo_file = FSInputFile(path=str(photo_path))
            if photo_path.exists():
                await query.bot.send_photo(chat_id=chat_id, photo=photo_file, caption=text, parse_mode="HTML")
        else:
            await query.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

        await query.message.edit_text(
            f"✅ Сотрудник <b>{data['name']}</b> добавлен и поздравление отправлено!",
            parse_mode="HTML"
        )
    else:
        await query.message.edit_text(
            f"✅ Сотрудник <b>{data['name']}</b> добавлен.",
            parse_mode="HTML"
        )

@router.message(F.chat.type == "private",AddEmployee.photo)
async def wrong_photo(message: Message):
    await message.answer("Пожалуйста, отправьте именно фото, не документ 📷", reply_markup=cancel_kb)


@router.message(F.chat.type == "private",Command("list_employees"))
async def list_employees(message: Message):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.", reply_markup=cancel_kb)

    employees = storage.get_all()
    if not employees:
        await message.answer("👥 Сотрудников пока нет.")
        return

    text = "👥 <b>Список сотрудников</b>:\n\n"
    for idx, emp in enumerate(employees, start=1):
        if emp.get('position'):
            text += (
                f"{idx}. <b>{emp['name']}</b> - {emp['position']}\n"
                f"🎂 {emp['birthday']}   💼 {emp['telegram']}\n"
                f"🆔 ID: <code>{emp['id']}</code>\n\n"
            )
        else:
            text += (
                f"{idx}. <b>{emp['name']}</b>\n"
                f"🎂 {emp['birthday']}   💼 {emp['telegram']}\n"
                f"🆔 ID: <code>{emp['id']}</code>\n\n"
            )


    await message.answer(text)


class RemoveEmployee(StatesGroup):
    waiting_id = State()


@router.message(F.chat.type == "private",Command("remove_employee"))
async def remove_employee_start(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")

    await state.set_state(RemoveEmployee.waiting_id)
    await message.answer(
        "Введите <b>ID</b> сотрудника, "
        "которого хотите удалить:", reply_markup=cancel_kb
    )


@router.message(F.chat.type == "private",RemoveEmployee.waiting_id)
async def remove_employee_confirm(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    emp_id = message.text.strip()
    removed = storage.remove_employee(emp_id)

    if removed:
        await message.answer(f"🗑 Сотрудник с ID <code>{emp_id}</code> удалён.")
    else:
        await message.answer(f""
                             f"⚠ Сотрудник с ID <code>"
                             f"{emp_id}</code> не найден.",
                             reply_markup=cancel_kb
                             )

    await state.clear()


@router.message(F.chat.type == "private",Command("today_birthdays"))
async def today_birthdays(message: Message):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    employees = storage.get_today_birthdays()
    if not employees:
        await message.answer("🎂 Сегодня именинников нет.")
        return

    text = "🎉 <b>Сегодня День рождения!</b>\n\n"
    for emp in employees:
        text += f"🎂 <b>{emp['name']}</b> — {emp['telegram']}\n"

    await message.answer(text)


@router.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated, bot):
    old_status = event.old_chat_member.status
    new_status = event.new_chat_member.status

    if (old_status in ("left", "kicked")
            and new_status in ("member", "administrator")):
        chat_id = event.chat.id
        save_chat_id(chat_id)
        await bot.send_message(chat_id,
                               "✅ Теперь я буду поздравлять "
                               "именинников в этом чате!"
                               )


class HRStates(StatesGroup):
    waiting_hr_id = State()
    waiting_remove_hr_id = State()



@router.message(F.chat.type == "private", F.text == "➕ Добавить HR")
async def menu_add_hr(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    await state.set_state(HRStates.waiting_hr_id)
    await message.answer("Введите user_id нового HR:", reply_markup=cancel_kb)


@router.message(F.chat.type == "private", HRStates.waiting_hr_id, F.text)
async def process_add_hr(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    text = message.text.strip()
    try:
        new_hr = int(text)
        if new_hr in HR_IDS:
            await message.answer("❌ Этот пользователь уже HR.")
        else:
            HR_IDS.append(new_hr)
            save_hr(HR_IDS)
            await message.answer(f"✅ Пользователь <code>{new_hr}</code> теперь HR.", parse_mode="HTML", reply_markup=ReplyKeyboardRemove())
        await state.clear()
    except ValueError:
        await message.answer("❌ Неверный ID. Попробуйте снова:", reply_markup=cancel_kb)



@router.message(F.chat.type == "private", F.text == "🗑 Удалить HR")
async def menu_remove_hr(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    await state.set_state(HRStates.waiting_remove_hr_id)
    await message.answer("Введите user_id HR, которого хотите удалить:", reply_markup=cancel_kb)


@router.message(F.chat.type == "private", HRStates.waiting_remove_hr_id, F.text)
async def process_remove_hr(message: Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("⛔ Действие отменено.", reply_markup=ReplyKeyboardRemove())
        return
    text = message.text.strip()
    try:
        hr_id = int(text)
        if hr_id not in HR_IDS:
            await message.answer("❌ Этот пользователь не HR.")
        else:
            HR_IDS.remove(hr_id)
            save_hr(HR_IDS)
            await message.answer(
                f"🗑 Пользователь <code>{hr_id}</code> удалён из списка HR.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove()
            )
        await state.clear()
    except ValueError:
        await message.answer("❌ Неверный ID. Попробуйте снова:", reply_markup=cancel_kb)


@router.message(F.chat.type == "private", Command("list_hr"))
async def list_hr(message: Message):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")

    if not HR_IDS:
        return await message.answer("👥 Сейчас нет HR.")

    text = "👥 <b>Текущие HR:</b>\n\n"
    buttons = []

    for hr in HR_IDS:
        text += f"🆔 <a href='tg://user?id={hr}'>{hr}</a>\n"
        buttons.append([InlineKeyboardButton(text=f"Удалить {hr}", callback_data=f"remove_hr:{hr}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(lambda c: c.data and c.data.startswith("remove_hr:"))
async def remove_hr_callback(query: CallbackQuery):
    hr_id = int(query.data.split(":")[1])
    if not is_hr(query.from_user):
        return await query.answer("⛔ У вас нет доступа.", show_alert=True)

    if hr_id in HR_IDS:
        HR_IDS.remove(hr_id)
        save_hr(HR_IDS)
        await query.message.edit_text(
            f"🗑 Пользователь <a href='tg://user?id={hr_id}'>{hr_id}</a> удалён из списка HR.",
            parse_mode="HTML"
        )
        await query.answer("✅ HR удалён")
    else:
        await query.answer("❌ Этот пользователь не HR", show_alert=True)


class SearchEmployee(StatesGroup):
    waiting_query = State()

@router.message(F.chat.type == "private", F.text == "🔍 Найти сотрудника")
async def menu_search_employee(message: Message, state: FSMContext):
    if not is_hr(message):
        return await message.answer("⛔ У вас нет доступа.")
    await state.set_state(SearchEmployee.waiting_query)
    await message.answer("Введите имя или ID сотрудника для поиска:", reply_markup=cancel_kb)


@router.message(F.chat.type == "private", SearchEmployee.waiting_query, F.text)
async def process_search_employee(message: Message, state: FSMContext):
    if message.text.startswith("/") or message.text == "❌ Отмена":
        await state.clear()
        return

    query = message.text.strip()
    employees = storage.get_all()
    results = []

    for emp in employees:
        if query.lower() in emp['name'].lower() or query == str(emp['id']) or query == emp.get("telegram", ""):
            results.append(emp)

    if not results:
        await message.answer("❌ Сотрудник не найден. Попробуйте снова:", reply_markup=cancel_kb)
        return

    for emp in results:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🗑 Удалить", callback_data=f"remove_emp:{emp['id']}"),
                    InlineKeyboardButton(text="🎉 Поздравить", callback_data=f"congrats_emp:{emp['id']}")
                ]
            ]
        )
        caption = f"<b>{emp['name']}</b>\n🎂 {emp['birthday']}   💼 {emp['telegram']}\n🆔 ID: <code>{emp['id']}</code>"

        if emp.get("photo"):
            from aiogram.types import FSInputFile
            from pathlib import Path
            PHOTOS_DIR = Path(__file__).parent.parent / "photos"
            photo_path = PHOTOS_DIR / emp["photo"]
            if photo_path.exists():
                photo_file = FSInputFile(path=str(photo_path))
                await message.answer_photo(photo=photo_file, caption=caption, parse_mode="HTML", reply_markup=kb)
            else:
                await message.answer(caption, parse_mode="HTML", reply_markup=kb)
        else:
            await message.answer(caption, parse_mode="HTML", reply_markup=kb)

    await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith("remove_emp:"))
async def remove_emp_callback(query: CallbackQuery):
    emp_id = query.data.split(":", 1)[1]
    removed = storage.remove_employee(emp_id)

    if removed:
        await query.message.edit_text(
            f"🗑 Сотрудник с ID <code>{emp_id}</code> удалён.", parse_mode="HTML"
        )
        await query.answer("✅ Сотрудник удалён")
    else:
        await query.answer("❌ Сотрудник не найден", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("congrats_emp:"))
async def congrats_employee(query: CallbackQuery, state: FSMContext):
    emp_id = query.data.split(":")[1]
    emp = storage.get_by_id(emp_id)
    if not emp:
        return await query.answer("❌ Сотрудник не найден", show_alert=True)

    await state.update_data(congrats_emp_id=emp_id)
    await state.set_state(CongratsEmployee.waiting_text)
    await query.message.answer(f"Введите текст поздравления для <b>{emp['name']}</b>:", parse_mode="HTML")


@router.message(F.chat.type == "private", CongratsEmployee.waiting_text, F.text)
async def process_congrats_text(message: Message, state: FSMContext):
    data = await state.get_data()
    emp_id = data.get("congrats_emp_id")
    emp = storage.get_by_id(emp_id)
    chat_id = load_chat_id()

    text = message.text.strip()
    final_text = f"{emp['name']}, {text}"
    print(final_text)
    if emp.get("telegram"):
        final_text += f" {emp['telegram']}"

    if emp.get("photo"):
        from aiogram.types import FSInputFile
        from pathlib import Path
        PHOTOS_DIR = Path(__file__).parent.parent / "photos"
        photo_path = PHOTOS_DIR / emp["photo"]
        photo_file = FSInputFile(path=str(photo_path))
        await message.bot.send_photo(chat_id=chat_id, photo=photo_file, caption=final_text)
    else:
        await message.bot.send_message(chat_id=chat_id, text=final_text)

    await message.answer("✅ Поздравление отправлено!")
    await state.clear()

