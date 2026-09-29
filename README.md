# ai201-project4-provenance-guard



\# Provenance Guard



\*\*Author:\*\* Layla Hadley



\## Architecture \& Design Decisions



\### Detection Signals

Provenance Guard uses a multi-signal detection pipeline to classify text as human or AI-generated:

1\. \*\*LLM Semantic Classification (`openai/gpt-oss-120b`):\*\* This signal evaluates the semantic and stylistic coherence of the text holistically.

2\. \*\*Stylometric Heuristics (Python):\*\* This structural signal calculates the mathematical variance in sentence length. 



\*Reasoning:\* Combining a semantic signal with a structural signal provides a much more robust defense than either alone. An AI might mimic human semantics, but its structural variance is often much tighter. If deploying this for a real production platform, I would add a third signal analyzing n-gram perplexity against known AI-generated datasets to catch sophisticated prompt-engineered text.



\### Confidence Scoring

The system uses a 50/50 weighted average of the LLM score and the Stylometric score to generate a final, calibrated confidence percentage. 



\*Examples showing meaningful variation:\*

\* \*\*High-Confidence AI Submission:\*\* "Artificial intelligence represents a transformative paradigm shift in modern society..." 

&#x20; \* `llm\_score`: 0.95 | `stylo\_score`: 0.90 

&#x20; \* \*\*Final Confidence: 0.93\*\*

\* \*\*Low-Confidence (Likely Human) Submission:\*\* "ok so i finally tried that new ramen place downtown and honestly? underwhelming..." 

&#x20; \* `llm\_score`: 0.15 | `stylo\_score`: 0.10 

&#x20; \* \*\*Final Confidence: 0.13\*\*



\## Transparency Labels

Based on the confidence score thresholds, the system surfaces one of three exact transparency labels to the user:

\* \*\*High-confidence AI (0.75 - 1.00):\*\* "Content labeled as AI-generated (High Confidence)."

\* \*\*Uncertain (0.36 - 0.74):\*\* "Attribution uncertain. Content displays mixed or inconclusive signals."

\* \*\*High-confidence human (0.00 - 0.35):\*\* "Content labeled as Human-authored (High Confidence)."



\## Rate Limiting \& Audit Log

\* \*\*Rate Limits:\*\* `10 per minute; 100 per day`. 

\* \*Reasoning:\* These numbers are defensible because a human creator submitting original writing will rarely post more than 10 times in a single minute, whereas a malicious script attempting to flood the attribution endpoint would trigger this limit almost immediately.

\* \*\*Audit Log Sample:\*\*

```json

\[

&#x20; {

&#x20;   "content\_id": "4e5269a7-4a5f-4571-8f10-3025e36926ad",

&#x20;   "creator\_id": "test-user",

&#x20;   "timestamp": "2026-09-29T16:00:00.000Z",

&#x20;   "attribution": "Likely Human",

&#x20;   "confidence": 0.13,

&#x20;   "llm\_score": 0.15,

&#x20;   "stylo\_score": 0.10,

&#x20;   "status": "under\_review",

&#x20;   "appeal\_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical."

&#x20; }

]



\## Known limitations:

The system predictably struggled with highly structured, repetitive human writing (maybe like a children's poem or lyrical song). Because the stylometric heuristic relies on sentence length variance to identify human writing, a poem with uniformly short lines will score very close to 1.0 (highly uniform/AI-like) on the structural signal. This forces the combined confidence score higher, likely resulting in a false "Uncertain" or "Likely AI" classification.



\## Spec reflection

&#x09;- how the spec helped: Writing the exact endpoints and JSON payloads in the spec first made it incredibly easy to prompt the AI tool to 	generate the Flask code, because the API contracts were rigidly defined upfront

&#x09;- where it diverged from final submission: I originally specified using meta-llama/llama-4-scout-17b-16e-instruct for the LLM signal, but 	that model was decommissioned on the Groq platform. I had to pivot the implementation to use openai/gpt-oss-120b to get a working 	response. Furthermore, my testing diverged from using standard curl commands to using PowerShell Invoke-RestMethod due to local Windows 	JSON parsing errors.



\## AI Usage

Task: I directed the AI to generate the initial Flask app skeleton, including the /submit route and the SQLite database initialization

&#x09;- result: produced a working app.py script

&#x09;- revision: I overrode the code by manually updating the target model string in the get\_llm\_score function after encountering a 400 Bad 	Request error.

Task: I asked the AI to write the pure Python logic for the Stylometric heuristic (Signal 2) to calculate mathematical sentence length variance.

&#x09;- result: produced a functional get\_stylo\_score algorithm

&#x09;- revision: had to revise the CLI testing approach the AI suggested, manually escaping JSON quotes and translating bash loops into 	Windows PowerShell ForEach-Object loops to successfully test the rate limiter in my environment

