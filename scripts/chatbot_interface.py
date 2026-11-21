"""Command-line interface and response routing for the chatbot."""

import json
import random
import re
from pathlib import Path

from scripts.api_integration import get_news, get_weather
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


def _fallback_intent(message: str) -> str:
    """Provide basic local-demo routing before trained model files exist."""
    text = message.casefold()
    if any(word in text for word in ("weather", "forecast", "temperature", "rain")):
        return "weather"
    if any(word in text for word in ("headline", "news")):
        return "news"
    if "remind" in text or "reminder" in text:
        if any(word in text for word in ("show", "list", "view", "what")):
            return "reminders"
        if any(word in text for word in ("delete", "remove", "cancel")):
            return "delete_reminder"
        return "reminder"
    if any(word in text for word in ("fun fact", "interesting fact", "tell me something")):
        return "knowledge"
    if any(word in text for word in ("bye", "goodbye", "see you", "quit")):
        return "goodbye"
    if any(word in text for word in ("hi", "hello", "hey", "good morning", "good afternoon")):
        return "greeting"
    return "unknown"


def chatbot_response(user_input: str, context: dict | None = None, intent_override: str | None = None) -> str:
    """Classify a message and route it to the matching assistant feature."""
    message = user_input.strip()
    if not message:
        return "Please type a message so I can help."

    lowered = message.casefold()
    if lowered in {"show reminders", "list reminders", "view reminders"}:
        return view_reminders()
    if lowered.startswith("delete reminder "):
        return delete_reminder(message[len("delete reminder "):])

    if intent_override:
        tag = intent_override
    else:
        try:
            # Import lazily so the local web demo can run without TensorFlow/model files.
            from scripts.nlp_engine import predict_intent

            prediction = predict_intent(message)
            tag = prediction["tag"] if isinstance(prediction, dict) else prediction
        except (FileNotFoundError, ImportError, ModuleNotFoundError):
            tag = _fallback_intent(message)

    context = context or {}
    if tag == "weather":
        city_match = re.search(r"\b(?:in|for)\s+([\w .'-]+?)(?:\?|$)", message, re.IGNORECASE)
        if not city_match:
            city_match = re.match(r"\s*(?:weather|forecast)\s+([\w .'-]+?)\s*[?!.,]*$", message, re.IGNORECASE)
        city = str(context.get("city") or (city_match.group(1).strip(" .?!") if city_match else ""))
        return get_weather(city) if city else "Which city would you like the weather for?"
    if tag == "reminder":
        reminder_text = context.get("reminder_text")
        reminder_time = context.get("reminder_time")
        if reminder_text and reminder_time:
            return add_reminder(str(reminder_text), str(reminder_time))
        match = re.search(r"remind me to\s+(.+?)\s+(?:at|on)\s+(.+)$", message, re.IGNORECASE)
        if match:
            return add_reminder(match.group(1), match.group(2))
        return "Tell me what to remind you about and when. You can say, 'Remind me to buy groceries at 6 PM'."
    if tag in {"reminders", "view_reminders"}:
        return view_reminders()
    if tag == "delete_reminder":
        if context.get("reminder_text"):
            return delete_reminder(str(context["reminder_text"]))
        match = re.search(r"delete (?:the )?reminder(?: for)?\s+(.+)$", message, re.IGNORECASE)
        return delete_reminder(match.group(1)) if match else "Which reminder should I delete?"
    if tag == "knowledge":
        return "Here's a fun fact: honey can remain edible for a very long time when stored sealed."
    if tag == "news":
        return get_news()
    if tag == "unknown":
        return "I didn't catch that. Try asking about weather, reminders, news, or a fun fact."
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
