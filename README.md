# Personal Assistant Chatbot

A local browser chatbot built with Flask. Facebook Messenger is optional; the local web app runs independently.

## Run locally

From the project directory, install the dependencies and start the app:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). The browser demo supports greetings, fun facts, reminders, and the weather/news routes. Weather and news requests need API keys; without them, the app explains how to configure them. The app also exposes an optional `/webhook` route for Facebook Messenger.

The demo has a lightweight keyword fallback so it can respond before model artifacts exist. To train the TensorFlow intent classifier using `data/intents.json`, run:

```bash
python -m scripts.nlp_engine
```

After changing intent patterns, rerun that command to retrain the classifier. The generated model and preprocessing files are stored in `models/`; both `tokenizer.pickle` and `vectorizer.pickle` are written to match the different filenames used across the textbook sections.

To generate the textbook's per-intent precision, recall, and F1 report and sample response times, run:

```bash
python -m scripts.evaluate_chatbot
```

The command trains an evaluation model from a stratified holdout split; it does not replace the saved chatbot model. The `/feedback` endpoint accepts a rating and optional comment as JSON.

## Optional API keys

Set `OPENWEATHERMAP_API_KEY` for weather lookups and `NEWS_API_KEY` for headlines. Keep API keys out of source control. For Facebook Messenger, configure `FACEBOOK_PAGE_ACCESS_TOKEN`, `FACEBOOK_VERIFY_TOKEN`, and optionally `FACEBOOK_GRAPH_API_VERSION`, subscribe Meta's webhook to `/webhook`, and provide a publicly reachable HTTPS URL. The local browser demo does not depend on Facebook credentials.

## Feedback and monitoring

The chat page includes thumbs-up/down feedback. Ratings and comments are appended to `data/feedback.json`. The Flask app logs request duration and input length without recording message text. Reminder data is stored in `data/reminders.json`.

The built-in Flask server is for local demos. Use a WSGI server and appropriate deployment configuration before exposing the app publicly.
