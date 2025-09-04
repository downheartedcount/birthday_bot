import json
import os
from pathlib import Path

from config import settings


BASE_DIR = Path(__file__).parent.parent
CHAT_FILE = BASE_DIR / settings.CHAT_FILE


def save_chat_id(chat_id: int):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump({"chat_id": chat_id}, f)


def load_chat_id() -> int | None:
    if not os.path.exists(CHAT_FILE):
        return None
    with open(CHAT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("chat_id")
