# Birthday Bot

**Описание:**  
Telegram-бот для поздравлений сотрудников с днём рождения, приветствия новых сотрудников и управления списком сотрудников через HR-панель.

**Технологии:**
- Python 3.11
- Aiogram 3.x
- JSON-хранилище для сотрудников и HR
- Docker & Docker Compose

**Структура проекта:**
birthday_bot/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── src/
├── bot.py # Точка входа бота
├── config.py # Настройки
├── handlers/ # Обработчики команд и callback
├── services/ # Сервисы для работы с данными
├── utils/ # Утилиты (логирование, клиент HTTP и т.д.)
├── photos/ # Фото сотрудников
├── employees.json # Данные сотрудников
├── hr.json # Список HR
├── greetings.json # Шаблоны поздравлений
└── users/ # Дополнительные данные пользователей



**Установка и запуск локально:**
```bash
# Клонировать репозиторий
git clone git@github.com:<username>/birthday_bot.git
cd birthday_bot

# Создать виртуальное окружение и активировать
python3 -m venv .venv
source .venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Запустить бота
python src/bot.py

```
**Docker
```bash
docker-compose build
docker-compose up -d

```


Переменные окружения (config.py):
TELEGRAM_TOKEN — токен Telegram-бота
Другие настройки можно смотреть в config.py

