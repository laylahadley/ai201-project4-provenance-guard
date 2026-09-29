import os
import uuid
import sqlite3
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def init_db():
    conn = sqlite3.connect('provenance.db')
    c = conn.cursor()
    # Added stylo_score column
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log
                 (content_id TEXT, creator_id TEXT, timestamp TEXT,
                  attribution TEXT, confidence REAL, llm_score REAL, stylo_score REAL, status TEXT)''')
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
def submit():
    data = request.json or {}
    text = data.get('text', '')
    creator_id = data.get('creator_id', 'anonymous')

    content_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Process Both Signals
    llm_score = get_llm_score(text)
    stylo_score = get_stylo_score(text)

    # Confidence Scoring Logic (50/50 weighted average)
    confidence = round((llm_score + stylo_score) / 2.0, 2)

    # Threshold Logic
    attribution = "Likely AI" if confidence > 0.74 else "Uncertain" if confidence > 0.35 else "Likely Human"
    label = "Placeholder Label" # Placeholder until M5

    # Write to Audit Log
    conn = sqlite3.connect('provenance.db')
    c = conn.cursor()
    c.execute("INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (content_id, creator_id, timestamp, attribution, confidence, llm_score, stylo_score, "classified"))
    conn.commit()
    conn.close()

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
        "llm_score": llm_score,
        "stylo_score": stylo_score,
        "label": label
    })

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