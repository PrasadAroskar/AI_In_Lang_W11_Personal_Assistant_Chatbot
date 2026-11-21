"""Optional Facebook Messenger webhook integration."""

import hmac
import os

import requests
from flask import Blueprint, current_app, request

from scripts.chatbot_interface import chatbot_response


facebook_bp = Blueprint("facebook", __name__)


def send_message(recipient_id: str, message_text: str) -> bool:
    """Send a reply through Meta's Messenger Send API."""
    page_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    if not page_token:
        current_app.logger.error("Facebook webhook received a message without a page access token")
        return False
    version = os.getenv("FACEBOOK_GRAPH_API_VERSION", "v27.0")
    url = f"https://graph.facebook.com/{version}/me/messages"
    try:
        response = requests.post(
            url,
            params={"access_token": page_token},
            json={"recipient": {"id": recipient_id}, "message": {"text": message_text}},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException:
        current_app.logger.exception("Could not send Facebook Messenger reply")
        return False


@facebook_bp.get("/webhook")
def webhook_verification():
    """Handle Meta webhook subscription verification."""
    mode = request.args.get("hub.mode", "")
    token = request.args.get("hub.verify_token", "")
    challenge = request.args.get("hub.challenge", "")
    expected = os.getenv("FACEBOOK_VERIFY_TOKEN", "")
    if mode == "subscribe" and expected and hmac.compare_digest(token, expected):
        return challenge, 200
    return "Verification failed", 403


@facebook_bp.post("/webhook")
def webhook():
    """Receive text messages from subscribed Facebook Pages and reply."""
    data = request.get_json(silent=True) or {}
    if data.get("object") != "page":
        return "Not Found", 404
    for entry in data.get("entry", []):
        for event in entry.get("messaging", []):
            message = event.get("message", {})
            sender_id = event.get("sender", {}).get("id")
            text = message.get("text")
            # Ignore delivery notifications, postbacks, and messages sent by this page.
            if sender_id and isinstance(text, str) and not message.get("is_echo"):
                send_message(sender_id, chatbot_response(text))
    return "OK", 200
