import re

def get_stylo_score(text):
    # Split into sentences using basic punctuation
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(sentences) < 2:
        return 0.5 # Not enough data for variance

    # Calculate lengths
    lengths = [len(s.split()) for s in sentences]
    mean_length = sum(lengths) / len(lengths)

    # Calculate variance
    variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)

    # Normalize variance to a 0.0 (high variance/human) to 1.0 (uniform/AI) scale
    # Assumption: Variance > 50 is highly human, Variance < 10 is highly AI
    normalized = 1.0 - min(max(variance / 50.0, 0.0), 1.0)
    return round(normalized, 2)
 
print("Testing Stylometric Signal...")
print("AI-generated:", get_stylo_score("Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment."))
print("Human-written:", get_stylo_score("ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after. my friend got the spicy version and said it was better. probably won't go back unless someone drags me there"))
print("Borderline Formal:", get_stylo_score("The relationship between monetary policy and asset price inflation has been extensively studied in the literature. Central banks face a fundamental tension between their mandate for price stability and the unintended consequences of prolonged low interest rates on equity and real estate valuations."))
print("Borderline Edited:", get_stylo_score("I've been thinking a lot about remote work lately. There are genuine tradeoffs - flexibility and no commute on one side, isolation and blurred work-life boundaries on the other. Studies show productivity varies widely by individual and role type."))