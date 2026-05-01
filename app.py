import os
import json
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Load election data
with open("data.json", "r", encoding="utf-8") as f:
    election_data = json.load(f)

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not set")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")

SYSTEM_PROMPT = """You are 'Election Mitra' - an AI assistant designed to help Indian citizens understand elections. Your role is to explain the Indian election process, voting steps, timelines, and FAQs in simple Hindi and English.

Rules:
1. Always be accurate about Indian election facts (Lok Sabha, Vidhan Sabha, EVM, VVPAT, ECI).
2. Use a friendly, helpful tone in Hinglish (mix of Hindi and English).
3. Keep answers under 150 words unless the user asks for details.
4. If asked about political opinions, candidates, or parties, stay neutral.
5. Guide users step-by-step for processes like voter registration, finding polling booth, and what to bring on voting day.
6. Structure information with bullet points when listing steps.

Current election data available:
- Elections: Lok Sabha 2024 (completed)
- Parties: BJP, INC, AAP
- States: UP, Maharashtra, Delhi
- Candidates: Narendra Modi, Rahul Gandhi, Arvind Kejriwal

Use this data when relevant. If asked something not in this data, answer from your general knowledge about Indian elections."""

# Conversation history store
conversations = {}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "default")

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # Initialize conversation if new session
        if session_id not in conversations:
            conversations[session_id] = []

        # Build message history
        messages = [
            {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]},
            {"role": "model", "parts": [{"text": "Understood. I will follow these instructions as Election Mitra."}]}
        ]

        # Add conversation history (last 10 exchanges)
        for msg in conversations[session_id][-10:]:
            messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "parts": [{"text": user_message}]})

        # Generate response using Gemini
        response = model.generate_content(messages)
        ai_reply = response.text.strip()

        # Store conversation
        conversations[session_id].append({"role": "user", "parts": [{"text": user_message}]})
        conversations[session_id].append({"role": "model", "parts": [{"text": ai_reply}]})

        return jsonify({
            "reply": ai_reply,
            "session_id": session_id
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "I am having trouble processing your request. Please try again."}), 500


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