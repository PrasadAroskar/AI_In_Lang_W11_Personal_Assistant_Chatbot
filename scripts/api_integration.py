"""External API integrations used by the assistant."""

import os

import requests


WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
NEWS_URL = "https://newsapi.org/v2/top-headlines"


def get_weather(city: str) -> str:
    """Return current weather for a city using OpenWeatherMap."""
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return "Weather lookup isn't configured yet. Set the OPENWEATHERMAP_API_KEY environment variable."
    if not city or not city.strip():
        return "Tell me which city you'd like the weather for."

    try:
        response = requests.get(
            WEATHER_URL,
            params={"q": city.strip(), "appid": api_key, "units": "metric"},
            timeout=10,
        )
        if response.status_code == 404:
            return f"I couldn't find weather for {city.strip()}. Check the city name and try again."
        response.raise_for_status()
        data = response.json()
        temperature = data["main"]["temp"]
        description = data["weather"][0]["description"]
        location = data.get("name", city.strip())
        return f"It's {description} in {location}, with a temperature of {temperature:g}°C."
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return "I couldn't retrieve the weather right now. Please try again shortly."


def handle_api_request(intent: str, entities: dict | None = None) -> str:
    """Dispatch supported API-backed intents."""
    entities = entities or {}
    if intent == "weather":
        return get_weather(str(entities.get("city", "")))
    if intent == "news":
        return get_news()
    return "I don't have an API integration for that request yet."


def get_news() -> str:
    """Return a short list of current US headlines using NewsAPI."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "News lookup isn't configured yet. Set the NEWS_API_KEY environment variable."
    try:
        response = requests.get(
            NEWS_URL,
            params={"country": "us", "apiKey": api_key, "pageSize": 5},
            timeout=10,
        )
        response.raise_for_status()
        articles = response.json().get("articles", [])
        headlines = [
            f"• {article.get('title', 'Untitled')} — {article.get('source', {}).get('name', 'Unknown source')}"
            for article in articles[:5]
        ]
        return "Top headlines:\n" + "\n".join(headlines) if headlines else "No headlines are available right now."
    except (requests.RequestException, ValueError, TypeError):
        return "I couldn't retrieve the news right now. Please try again shortly."
