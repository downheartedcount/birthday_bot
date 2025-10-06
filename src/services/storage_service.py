import datetime
import uuid
from pathlib import Path
import json
from aiogram import Bot

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "employees.json"
PHOTOS_DIR = BASE_DIR / "photos"


class StorageService:
    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        PHOTOS_DIR.mkdir(exist_ok=True)

    def load(self):
        if not DATA_FILE.exists():
            return []
        try:
            with DATA_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    def save(self, employees):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(employees, f, ensure_ascii=False, indent=2)

    def add_employee(self, name, birthday, position, telegram, gender, photo_filename):
        employees = self.load()
        employees.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "birthday": birthday,
            "position": position,
            "telegram": telegram,
            "gender": gender,
            "photo": str(photo_filename)
        })
        self.save(employees)

    def get_all(self):
        return self.load()

    def get_today_birthdays(self):
        today = datetime.date.today()
        employees = self.load()
        result = []
        for emp in employees:
            bday = datetime.date.fromisoformat(emp["birthday"])
            if bday.day == today.day and bday.month == today.month:
                result.append(emp)
        return result

    def remove_employee(self, emp_id: str) -> bool:
        employees = self.load()
        new_employees = [e for e in employees if e["id"] != emp_id]

        if len(new_employees) == len(employees):
            return False

        self.save(new_employees)
        return True

    def update_employee(self, emp_id: str, **kwargs):
        for emp in self.get_all():
            if emp["id"] == emp_id:
                for key, value in kwargs.items():
                    if key in emp:
                        emp[key] = value
                return True
        return False

    def get_by_id(self, emp_id: str):
        """
        Находит сотрудника по его UUID.
        Возвращает словарь с данными сотрудника или None.
        """
        for emp in self.get_all():
            if str(emp.get("id")) == emp_id:
                return emp
        return None

    def get_birthdays_in_month(self, month: int):
        employees = self.get_all()
        result = []
        for emp in employees:
            try:
                emp_month = int(emp["birthday"].split("-")[1])
                if emp_month == month:
                    result.append(emp)
            except Exception:
                continue
        return result

async def save_photo(bot: Bot, file_id: str, filename: str):
    file = await bot.get_file(file_id)
    dst = PHOTOS_DIR / filename
    await bot.download(file, destination=dst)
    return dst
