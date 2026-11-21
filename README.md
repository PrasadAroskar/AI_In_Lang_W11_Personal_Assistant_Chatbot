# Personal Assistant Chatbot

A local browser chatbot built with Flask. Facebook Messenger is optional; the local web app runs independently.

## Run locally

From the project directory, install the dependencies and start the app:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The browser demo supports greetings, fun facts, reminders, and the weather/news routes. Weather and news requests need API keys; without them, the app explains how to configure them.

The demo has a lightweight keyword fallback so it can respond before model artifacts exist. To train the TensorFlow intent classifier using `data/intents.json`, run:

```bash
python -m scripts.nlp_engine
```

After changing intent patterns, rerun that command to retrain the classifier. The generated model and preprocessing files are stored in `models/`.

## Optional API keys

Set `OPENWEATHERMAP_API_KEY` for weather lookups and `NEWS_API_KEY` for headlines. Keep API keys out of source control.

## Feedback and monitoring

The chat page includes thumbs-up/down feedback. Ratings are appended to `data/feedback.json`. The Flask app logs request duration and input length without recording message text. Reminder data is stored in `data/reminders.json`.

The built-in Flask server is for local demos. Use a WSGI server and appropriate deployment configuration before exposing the app publicly.
