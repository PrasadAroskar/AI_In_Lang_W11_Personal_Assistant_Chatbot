"""Command-line interface and response routing for the chatbot."""

import json
import random
import re
from pathlib import Path

from scripts.api_integration import get_weather
from scripts.nlp_engine import predict_intent
from scripts.task_manager import add_reminder, delete_reminder, view_reminders


INTENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "intents.json"


def _response_for(tag: str) -> str:
    """Choose a configured response for an intent, if one is available."""
    try:
        with INTENTS_PATH.open(encoding="utf-8") as file:
            intents = json.load(file).get("intents", [])
        for intent in intents:
            if intent.get("tag") == tag and intent.get("responses"):
                return random.choice(intent["responses"])
    except (OSError, json.JSONDecodeError):
        pass
    return "I'm not sure how to respond to that yet."


def chatbot_response(user_input: str) -> str:
    """Classify a message and route it to the matching assistant feature."""
    message = user_input.strip()
    if not message:
        return "Please type a message so I can help."

    lowered = message.casefold()
    if lowered in {"show reminders", "list reminders", "view reminders"}:
        return view_reminders()
    if lowered.startswith("delete reminder "):
        return delete_reminder(message[len("delete reminder "):])

    try:
        prediction = predict_intent(message)
        tag = prediction["tag"] if isinstance(prediction, dict) else prediction
    except (FileNotFoundError, ImportError, ModuleNotFoundError):
        return "The intent model isn't ready yet. Install the requirements and run `python -m scripts.nlp_engine` first."

    if tag == "weather":
        city_match = re.search(r"\b(?:in|for)\s+([\w .'-]+?)(?:\?|$)", message, re.IGNORECASE)
        city = city_match.group(1).strip(" .?!") if city_match else ""
        return get_weather(city) if city else "Which city would you like the weather for?"
    if tag == "reminder":
        match = re.search(r"remind me to\s+(.+?)\s+(?:at|on)\s+(.+)$", message, re.IGNORECASE)
        if match:
            return add_reminder(match.group(1), match.group(2))
        return "Tell me what to remind you about and when. You can say, 'Remind me to buy groceries at 6 PM'."
    if tag == "reminders":
        return view_reminders()
    if tag == "delete_reminder":
        match = re.search(r"delete (?:the )?reminder(?: for)?\s+(.+)$", message, re.IGNORECASE)
        return delete_reminder(match.group(1)) if match else "Which reminder should I delete?"
    if tag == "knowledge":
        return "Here's a fun fact: honey can remain edible for a very long time when stored sealed."
    return _response_for(str(tag))


def run() -> None:
    """Run the interactive command-line chatbot."""
    print("Personal Assistant Chatbot — type 'exit' or 'quit' to leave.")
    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAssistant: Goodbye!")
            break
        if message.casefold() in {"exit", "quit"}:
            print("Assistant: Goodbye! Have a great day!")
            break
        print(f"Assistant: {chatbot_response(message)}")


if __name__ == "__main__":
    run()
