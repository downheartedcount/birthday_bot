from pathlib import Path
import json
import random

BASE_DIR = Path(__file__).parent.parent  # -> src/
GREETINGS_FILE = BASE_DIR / 'greetings.json'


def load_greetings() -> list[str]:
    if GREETINGS_FILE.exists():
        try:
            with open(GREETINGS_FILE, "r", encoding="utf-8") as f:  # <-- важно
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []


def get_random_greeting(name: str) -> str:
    greetings = load_greetings()
    if not greetings:
        return f"С днём рождения, {name}!"
    template = random.choice(greetings)
    return template.replace("{name}", name)
