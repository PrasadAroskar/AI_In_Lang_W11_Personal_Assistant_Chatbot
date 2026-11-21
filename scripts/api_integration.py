"""External API integrations used by the assistant."""

import os

import requests


WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


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
    return "I don't have an API integration for that request yet."
