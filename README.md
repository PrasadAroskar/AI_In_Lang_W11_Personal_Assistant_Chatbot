# Personal Assistant Chatbot

A Flask chatbot with a local browser interface, intent recognition, reminders, optional weather and news APIs, feedback collection, and an optional Facebook Messenger webhook. Facebook is not required for the local demo.

## Run the local demo

From the project directory, install the packages and start Flask:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5050](http://127.0.0.1:5050). The app uses port 5050 by default to avoid common macOS port 5000 conflicts. To stop the server, press `Ctrl+C` in its terminal. Restart it after changing Python code.

The browser chat supports greetings, fun facts, weather requests, reminders, reminder listing and deletion, and news requests. If model artifacts have not been trained yet, it uses a small keyword fallback for the local demo. Weather and news requests need API keys. Reminders are saved to `data/reminders.json`; this project stores reminder details but does not send notifications.

## Train or retrain intent recognition

The intent patterns and responses are in `data/intents.json`. After adding or changing examples, train the TensorFlow model with:

```bash
python -m scripts.nlp_engine
```

The model, vectorizer, and label encoder are saved under `models/`. The script saves both `tokenizer.pickle` and `vectorizer.pickle` because the textbook uses both names in different sections. NLTK preprocessing downloads its tokenizer, stopword, and WordNet data when needed. If model artifacts are missing, the local browser demo can still use its keyword fallback.

## Evaluate the model and response time

Run the evaluation example with:

```bash
python -m scripts.evaluate_chatbot
```

It trains a temporary classifier on a stratified training split, prints per-intent precision, recall, and F1 scores, then measures response time for sample prompts. It does not replace the saved model. Each intent needs at least two patterns for the stratified evaluation split to work.

Response clarity and relevance should also be reviewed by people using sample prompts in the browser. The chat page offers thumbs-up/down feedback and an optional comment. Feedback is stored locally in `data/feedback.json` (ignored by Git).

## Optional API keys

Set keys in the same terminal before starting the app. In zsh, for example:

```bash
export OPENWEATHERMAP_API_KEY="your_openweathermap_key"
export NEWS_API_KEY="your_news_api_key"
python app.py
```

Weather uses OpenWeatherMap. News uses NewsAPI for the top US headlines. Without a key, the bot explains which setting is missing.

## Optional Facebook Messenger integration

The Flask app includes a `/webhook` route with Meta webhook verification and message handling. To connect a Facebook Page, configure these environment variables:

```bash
export FACEBOOK_PAGE_ACCESS_TOKEN="your_page_access_token"
export FACEBOOK_VERIFY_TOKEN="a_secret_string_you_choose"
export FACEBOOK_GRAPH_API_VERSION="v27.0"
```

In Meta's developer settings, subscribe the app to the Page's Messenger events and set the callback URL to `https://your-public-host/webhook`, using the same verify token. Meta requires a publicly reachable HTTPS callback; `127.0.0.1` is only available on your computer. Keep tokens private and out of source control. The local browser chat works without these settings.

## HTTP endpoints

- `GET /` serves the browser chat.
- `GET /health` returns a simple service status.
- `POST /chat` accepts JSON with a non-empty `message`; optional fields include `city`, `reminder_text`, and `reminder_time`.
- `POST /feedback` accepts JSON with an integer `rating` from 1 to 5 and an optional `comment`.
- `GET /webhook` verifies a Meta webhook subscription; `POST /webhook` receives Messenger events.

The app logs request duration and input length without logging chat text. The built-in Flask server is intended for local demos; use a WSGI server and appropriate deployment configuration before exposing the app publicly.
