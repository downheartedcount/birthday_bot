import json
from pathlib import Path

HR_FILE = Path(__file__).parent.parent / "hr.json"

def load_hr() -> list[int]:
    if HR_FILE.exists():
        try:
            with open(HR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_hr(hr_list: list[int]):
    with open(HR_FILE, "w", encoding="utf-8") as f:
        json.dump(hr_list, f, indent=2, ensure_ascii=False)

HR_IDS = load_hr()
