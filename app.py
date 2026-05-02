import os
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

with open("data.json", "r", encoding="utf-8") as f:
    election_data = json.load(f)

api_key = os.getenv("GEMINI_API_KEY")

# Lazy import to avoid startup crash
def get_gemini_response(user_message, history):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    
    SYSTEM_PROMPT = """You are Election Mitra, an AI assistant helping Indian citizens understand elections. Explain voting process, EVM, VVPAT, voter registration in simple Hinglish. Keep answers under 150 words. Stay neutral."""
    
    messages = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
        {"role": "model", "parts": [{"text": "Understood."}]}
    ]
    for msg in history[-6:]:
        messages.append(msg)
    messages.append({"role": "user", "parts": [{"text": user_message}]})
    
    response = model.generate_content(messages)
    return response.text.strip()

conversations = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health():
    return jsonify({"status": "ok", "api_key_set": bool(api_key)})

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        if session_id not in conversations:
            conversations[session_id] = []

        ai_reply = get_gemini_response(user_message, conversations[session_id])

        conversations[session_id].append({"role": "user", "parts": [{"text": user_message}]})
        conversations[session_id].append({"role": "model", "parts": [{"text": ai_reply}]})

        return jsonify({"reply": ai_reply, "session_id": session_id})

    except Exception as e:
        return jsonify({"error": str(e)[:200]}), 500

@app.route("/api/elections")
def get_elections():
    return jsonify(election_data.get("elections", []))
@app.route("/api/parties")
def get_parties():
    return jsonify(election_data.get("parties", []))
@app.route("/api/candidates")
def get_candidates():
    return jsonify(election_data.get("candidates", []))
@app.route("/api/states")
def get_states():
    return jsonify(election_data.get("states", []))
@app.route("/api/faqs")
def get_faqs():
    return jsonify(election_data.get("faqs", []))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
