import os
import uuid
import sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Setup Audit Log Database
def init_db():
    conn = sqlite3.connect('provenance.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log
                 (content_id TEXT, creator_id TEXT, timestamp TEXT,
                  attribution TEXT, confidence REAL, llm_score REAL, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_llm_score(text):
    try:
        prompt = f"Analyze this text. Is it AI-generated or human-written? Return ONLY a single float between 0.0 (definitively human) and 1.0 (definitively AI). Text: {text}"
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
        )
        return float(response.choices[0].message.content.strip())
    except Exception:
        return 0.5 # Fallback score on error

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    text = data.get('text', '')
    creator_id = data.get('creator_id', 'anonymous')

    # Generate IDs and timestamp
    content_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Process Signal
    llm_score = get_llm_score(text)

    # Milestone 3 Placeholders
    attribution = "Likely AI" if llm_score > 0.74 else "Uncertain" if llm_score > 0.35 else "Likely Human"
    confidence = llm_score # Placeholder until M4
    label = "Placeholder Label" # Placeholder until M5

    # Write structured entry to Audit Log
    conn = sqlite3.connect('provenance.db')
    c = conn.cursor()
    c.execute("INSERT INTO audit_log VALUES (?, ?, ?, ?, ?, ?, ?)",
              (content_id, creator_id, timestamp, attribution, confidence, llm_score, "classified"))
    conn.commit()
    conn.close()

    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": confidence,
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