import os
import uuid
import sqlite3
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Setup Rate Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://"
)

def init_db():
    conn = sqlite3.connect('provenance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log
                 (content_id TEXT, creator_id TEXT, timestamp TEXT,
                  attribution TEXT, confidence REAL, llm_score REAL, stylo_score REAL, status TEXT, appeal_reasoning TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_llm_score(text):
    try:
        prompt = f"Analyze this text. Is it AI-generated or human-written? Return ONLY a single float between 0.0 (definitively human) and 1.0 (definitively AI). Text: {text}"
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        return float(response.choices[0].message.content.strip())
    except Exception:
        return 0.5 

def get_stylo_score(text):
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(sentences) < 2: return 0.5
    lengths = [len(s.split()) for s in sentences]
    mean_length = sum(lengths) / len(lengths)
    variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
    normalized = 1.0 - min(max(variance / 50.0, 0.0), 1.0)
    return round(normalized, 2)

@app.route('/submit', methods=['POST'])
@limiter.limit("10 per minute;100 per day")
def submit():
    data = request.json or {}
    text = data.get('text', '')
    creator_id = data.get('creator_id', 'anonymous')

    content_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    llm_score = get_llm_score(text)
    stylo_score = get_stylo_score(text)
    confidence = round((llm_score + stylo_score) / 2.0, 2)

    # Threshold and Label Logic
    if confidence > 0.74:
        attribution = "Likely AI"
        label = "Content labeled as AI-generated (High Confidence)."
    elif confidence > 0.35:
        attribution = "Uncertain"
        label = "Attribution uncertain. Content displays mixed or inconclusive signals."
    else:
        attribution = "Likely Human"
        label = "Content labeled as Human-authored (High Confidence)."

    conn = sqlite3.connect('provenance.db')
    c = conn.cursor()
    c.execute("INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
              (content_id, creator_id, timestamp, attribution, confidence, llm_score, stylo_score, "classified", ""))
    conn.commit()
    conn.close()

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "label": label
    })

@app.route('/appeal', methods=['POST'])
def appeal():
    data = request.json or {}
    content_id = data.get('content_id')
    reasoning = data.get('creator_reasoning', '')

    conn = sqlite3.connect('provenance.db')
    c = conn.cursor()
    c.execute("UPDATE audit_log SET status = 'under_review', appeal_reasoning = ? WHERE content_id = ?", 
              (reasoning, content_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "under_review", "message": "Appeal logged successfully."})

@app.route('/log', methods=['GET'])
def get_log():
    conn = sqlite3.connect('provenance.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()

    return jsonify({"entries": [dict(row) for row in rows]})

if __name__ == '__main__':
    app.run(debug=True)