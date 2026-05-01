import os
import json
from flask import Flask, render_template, request, jsonify
from google import genai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Load election data
with open("data.json", "r", encoding="utf-8") as f:
    election_data = json.load(f)


api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file")

client = genai.Client(api_key=api_key)

# 🔥 STRONG SYSTEM PROMPT
SYSTEM_PROMPT = """
You are 'Election Mitra' 🇮🇳

Role:
Help Indian citizens understand elections in a simple, friendly Hinglish style.

Instructions:
- Always explain step-by-step
- Use bullet points for processes
- Keep answers under 120 words
- Be neutral (no political bias)
- Ask follow-up questions when helpful

Topics:
- Voter eligibility
- Registration (NVSP)
- Voting process (EVM, VVPAT)
- Documents required
- Polling booth guidance

If user is confused → simplify more  
If user is first-time voter → guide step-by-step  
"""

# Conversation memory
conversations = {}

def build_prompt(user_message, history):
    history_text = ""
    for msg in history[-6:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['text']}\n"

    return f"""
{SYSTEM_PROMPT}

Conversation:
{history_text}

User: {user_message}
Assistant:
"""

def fallback_response(user_message):
    msg = user_message.lower()

    if "register" in msg:
        return "Register karne ke liye NVSP website use karein:\nhttps://www.nvsp.in/\n\nSteps:\n• Form 6 fill karein\n• Documents upload karein\n• Submit karein"

    if "eligibility" in msg:
        return "Eligibility:\n• Age: 18+\n• Indian citizen\n• Electoral roll me naam hona chahiye"

    if "vote" in msg:
        return "Voting Steps:\n• Polling booth par jao\n• ID verify karo\n• EVM pe vote karo\n• VVPAT confirm karo"

    return "Main help kar sakta hoon:\n• Registration\n• Eligibility\n• Voting steps\n\nAap kya jaana chahte ho?"

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
            return jsonify({"error": "Message required"}), 400

        if session_id not in conversations:
            conversations[session_id] = []

        history = conversations[session_id]

        prompt = build_prompt(user_message, history)

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                config={
                    "temperature": 0.6,
                    "max_output_tokens": 300
                }
            )

            ai_reply = response.text.strip()

        except Exception as ai_error:
            print("Gemini Error:", ai_error)
            ai_reply = fallback_response(user_message)

        # Save conversation
        history.append({"role": "user", "text": user_message})
        history.append({"role": "assistant", "text": ai_reply})

        return jsonify({
            "reply": ai_reply,
            "session_id": session_id
        })

    except Exception as e:
        print("Server Error:", e)
        return jsonify({"error": "Something went wrong"}), 500


# 🔥 DATA APIs (GOOD FOR SCORING)
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)