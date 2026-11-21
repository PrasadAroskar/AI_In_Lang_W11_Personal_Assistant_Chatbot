"""Local Flask web application for the personal assistant chatbot."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, render_template_string, request

from scripts.chatbot_interface import chatbot_response


app = Flask(__name__)
app.logger.setLevel(logging.INFO)
FEEDBACK_PATH = Path(__file__).resolve().parent / "data" / "feedback.json"

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Personal Assistant</title>
  <style>
    :root{font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#172033;background:#f2f5fa}
    *{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px}
    .shell{width:min(760px,100%);height:min(820px,calc(100vh - 48px));min-height:540px;background:#fff;border:1px solid #e2e8f0;border-radius:22px;box-shadow:0 24px 70px #25385818;display:flex;flex-direction:column;overflow:hidden}
    header{padding:22px 26px;background:linear-gradient(120deg,#263b80,#5575d8);color:#fff;display:flex;align-items:center;gap:14px}
    .avatar{width:44px;height:44px;border-radius:15px;background:#ffffff24;display:grid;place-items:center;font-size:22px}h1{font-size:18px;margin:0 0 4px}header p{margin:0;color:#dbe4ff;font-size:13px}
    #messages{padding:22px;overflow-y:auto;flex:1;background:linear-gradient(#f9fbff,#f5f7fc)}.message{max-width:82%;padding:12px 15px;border-radius:17px;margin:0 0 13px;white-space:pre-wrap;line-height:1.45;font-size:14px;overflow-wrap:anywhere}
    .assistant{background:#fff;border:1px solid #e5eaf2;border-bottom-left-radius:5px}.user{background:#4565c7;color:white;margin-left:auto;border-bottom-right-radius:5px}
    .feedback{font-size:11px;color:#748099;margin:-7px 0 14px 8px}.feedback button{border:0;background:transparent;color:#596b9a;cursor:pointer;padding:4px 7px}
    .suggestions{display:flex;gap:8px;flex-wrap:wrap;padding:0 22px 12px}.suggestions button{border:1px solid #dce3f0;background:#fff;color:#40527f;border-radius:18px;padding:8px 12px;cursor:pointer;font-size:12px}
    form{display:flex;gap:10px;padding:16px 20px 20px;border-top:1px solid #edf0f5}.entry{flex:1;border:1px solid #dce3ed;border-radius:14px;padding:13px 15px;font:inherit;outline:none}.entry:focus{border-color:#7189dc;box-shadow:0 0 0 3px #7189dc20}
    .send{border:0;border-radius:14px;background:#4565c7;color:#fff;padding:0 19px;font-weight:600;cursor:pointer}.send:disabled{opacity:.55;cursor:wait}.status{font-size:11px;color:#8a94a8;text-align:center;padding:0 0 12px}
    @media(max-width:540px){body{padding:0}.shell{height:100vh;min-height:0;border-radius:0}.message{max-width:90%}header{padding:18px}}
  </style>
</head>
<body><main class="shell">
  <header><div class="avatar">✦</div><div><h1>Personal Assistant</h1><p>Local demo · ready to help</p></div></header>
  <section id="messages" aria-live="polite"><div class="message assistant">Hi! I can help with reminders, weather, headlines, and fun facts. What would you like to do?</div></section>
  <div class="suggestions"><button data-message="Show my reminders">My reminders</button><button data-message="What's the weather in Boston?">Weather</button><button data-message="Tell me a fun fact">Fun fact</button></div>
  <form id="chat-form"><input id="message" class="entry" autocomplete="off" placeholder="Write a message…" aria-label="Message"><button class="send" type="submit">Send</button></form>
  <div class="status">This demo runs locally on your computer.</div>
</main>
<script>
const messages=document.querySelector('#messages'), form=document.querySelector('#chat-form'), input=document.querySelector('#message'), send=document.querySelector('.send');
function addMessage(text,who){const el=document.createElement('div');el.className='message '+who;el.textContent=text;messages.appendChild(el);messages.scrollTop=messages.scrollHeight;return el}
async function sendMessage(text){if(!text.trim())return;addMessage(text,'user');input.value='';send.disabled=true;try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});const data=await r.json();const answer=data.response||data.error||'Something went wrong.';const bubble=addMessage(answer,'assistant');if(r.ok){const fb=document.createElement('div');fb.className='feedback';fb.textContent='Was this helpful? ';for(const rating of [5,1]){const b=document.createElement('button');b.textContent=rating===5?'👍':'👎';b.title=rating===5?'Helpful':'Not helpful';b.onclick=async()=>{await fetch('/feedback',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rating,comment:''})});fb.textContent='Thanks for your feedback.'};fb.appendChild(b)}bubble.after(fb)}}catch(e){addMessage('Could not connect to the local chatbot. Please check that the server is running.','assistant')}finally{send.disabled=false;input.focus()}}
form.addEventListener('submit',e=>{e.preventDefault();sendMessage(input.value)});document.querySelectorAll('[data-message]').forEach(b=>b.addEventListener('click',()=>sendMessage(b.dataset.message)));
</script></body></html>"""


@app.get("/")
def home():
    """Serve the browser-based local chat demo."""
    return render_template_string(PAGE)


@app.get("/health")
def health():
    """Health route for local checks and deployment probes."""
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
    started = time.perf_counter()
    try:
        response = chatbot_response(message, context=context)
    except Exception:
        app.logger.exception("Chat request failed")
        return jsonify({"error": "The chatbot could not process this request."}), 500
    app.logger.info("Chat request completed (input_chars=%d, duration_ms=%.1f)", len(message), (time.perf_counter() - started) * 1000)
    return jsonify({"response": response})


@app.post("/feedback")
def feedback():
    """Persist a simple 1–5 rating and optional comment for later review."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    rating = payload.get("rating")
    if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
        return jsonify({"error": "'rating' must be an integer from 1 to 5."}), 400
    comment = payload.get("comment", "")
    if not isinstance(comment, str) or len(comment) > 2000:
        return jsonify({"error": "'comment' must be text up to 2000 characters."}), 400

    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with FEEDBACK_PATH.open(encoding="utf-8") as file:
            entries = json.load(file)
        if not isinstance(entries, list):
            entries = []
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []
    entries.append({
        "rating": rating,
        "comment": comment.strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    with FEEDBACK_PATH.open("w", encoding="utf-8") as file:
        json.dump(entries, file, indent=2, ensure_ascii=False)
    return jsonify({"message": "Thanks for your feedback!"}), 201


if __name__ == "__main__":
    # Run locally; use a WSGI server for a public production deployment.
    app.run(host="127.0.0.1", port=5000, debug=False)
