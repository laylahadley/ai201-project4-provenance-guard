import os
from groq import Groq
from dotenv import load_dotenv

# Load your API key from the .env file
load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_llm_score(text):
    prompt = f"Analyze this text. Is it AI-generated or human-written? Return ONLY a single float between 0.0 (definitively human) and 1.0 (definitively AI). Text: {text}"

    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b", 
    )
    return response.choices[0].message.content.strip()

print("Testing Groq Signal...")
print("Score:", get_llm_score("The sun dipped below the horizon, painting the sky."))
