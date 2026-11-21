"""Flask web application for the personal assistant chatbot."""

from flask import Flask, jsonify, request

from scripts.chatbot_interface import chatbot_response


app = Flask(__name__)


@app.get("/")
def health():
    """Basic status route for local checks and deployment health probes."""
    return jsonify({"status": "ok", "service": "personal-assistant-chatbot"})


@app.post("/chat")
def chat():
    """Accept a JSON message and return the assistant's response."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "'message' must be a non-empty string."}), 400

    context = {
        key: payload[key]
        for key in ("city", "reminder_text", "reminder_time")
        if isinstance(payload.get(key), str)
    }
    try:
        response = chatbot_response(message, context=context)
    except Exception:
        app.logger.exception("Chat request failed")
        return jsonify({"error": "The chatbot could not process this request."}), 500

    return jsonify({"response": response})


if __name__ == "__main__":
    # For production, run with a WSGI server (for example, `flask --app app run`).
    app.run(host="127.0.0.1", port=5000, debug=False)
