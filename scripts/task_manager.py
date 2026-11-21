"""Manage reminders stored in the project's JSON data file."""

import json
from pathlib import Path


REMINDERS_FILE = Path(__file__).resolve().parent.parent / "data" / "reminders.json"


def load_reminders() -> list[dict]:
    """Load reminders, accepting both the current object and legacy list format."""
    try:
        with REMINDERS_FILE.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("reminders"), list):
        return data["reminders"]
    return []


def save_reminders(reminders: list[dict]) -> None:
    """Persist reminders in the project's standard JSON format."""
    REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with REMINDERS_FILE.open("w", encoding="utf-8") as file:
        json.dump({"reminders": reminders}, file, indent=2, ensure_ascii=False)


def add_reminder(reminder_text: str, reminder_time: str) -> str:
    """Add a reminder with its text and user-provided time."""
    if not reminder_text.strip() or not reminder_time.strip():
        return "Please provide both what to remember and when."
    reminders = load_reminders()
    reminders.append({"text": reminder_text.strip(), "time": reminder_time.strip()})
    save_reminders(reminders)
    return "Reminder added successfully."


def view_reminders() -> str:
    """Return a readable list of reminders."""
    reminders = load_reminders()
    if not reminders:
        return "You have no reminders."
    lines = [f"{item.get('time', 'Time not set')}: {item.get('text', 'Untitled reminder')}" for item in reminders]
    return "Your reminders:\n" + "\n".join(lines)


def delete_reminder(reminder_text: str) -> str:
    """Delete reminders whose text matches (case-insensitively)."""
    reminders = load_reminders()
    kept = [item for item in reminders if item.get("text", "").casefold() != reminder_text.strip().casefold()]
    removed = len(reminders) - len(kept)
    if removed:
        save_reminders(kept)
        return "Reminder deleted successfully."
    return "I couldn't find a reminder with that description."
