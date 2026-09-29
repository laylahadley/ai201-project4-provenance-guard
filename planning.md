\# Provenance Guard: Architecture \& Planning



\## 1. Architecture Narrative

When a user submits text, it hits the `POST /submit` endpoint and passes through a rate limiter. The text is then routed in parallel to our Multi-Signal Detection Pipeline, consisting of a Groq LLM semantic analyzer and a Python stylometric heuristic engine. Both signals return a raw score, which the Confidence Scoring module aggregates into a final confidence percentage. Based on predefined thresholds, the system selects one of three Transparency Labels (High-Confidence AI, High-Confidence Human, Uncertain). This entire decision, including the signals used and the final label, is written to the SQLite Audit Log. Finally, the endpoint returns the structured JSON response containing the result, score, and label to the user.



\## 2. Detection Signals

\*\*Signal 1: LLM-Based Classification (Groq)\*\*

\* \*\*What it measures:\*\* Semantic and stylistic coherence. 

\* \*\*Why it differs:\*\* AI models tend to produce highly predictable, formulaic structures, whereas human writing often contains unique idiomatic phrasing and narrative nuance.

\* \*\*Blind spot:\*\* Highly edited, corporate-style human writing can easily be flagged as AI, and sophisticated AI prompting can mimic human quirks.



\*\*Signal 2: Stylometric Heuristics (Python)\*\*

\* \*\*What it measures:\*\* Sentence length variance and type-token ratio (vocabulary diversity).

\* \*\*Why it differs:\*\* AI text statistically favors uniform sentence lengths and predictable vocabulary distribution. Human writing is structurally bursty (mixing very short and very long sentences).

\* \*\*Blind spot:\*\* Extremely short submissions (e.g., a single sentence or tweet) do not contain enough data to establish statistical variance, rendering the heuristic useless.



\## 3. False Positive Scenario \& Appeals

\*\*Scenario:\*\* A human writer submits a highly structured, academic essay. The stylometric signal sees uniform sentence length, and the LLM sees formulaic phrasing. 

\* \*\*Confidence Score:\*\* The system calculates a 0.55 score (leaning AI, but low confidence). 

\* \*\*Transparency Label:\*\* Because it falls in the middle threshold, the system assigns the "Uncertain" label rather than firmly accusing the user of using AI.

\* \*\*Appeal:\*\* The creator uses the `POST /appeal` endpoint, submitting their drafting history as reasoning. The system updates the database status to "under review" and logs the appeal alongside the original audit entry.



\## 4. API Surface

\* `POST /submit`

&#x20; \* \*\*Accepts:\*\* JSON `{"text": "string"}`

&#x20; \* \*\*Returns:\*\* JSON `{"attribution": "string", "confidence\_score": float, "transparency\_label": "string"}`

\* `POST /appeal`

&#x20; \* \*\*Accepts:\*\* JSON `{"submission\_id": "string", "reasoning": "string"}`

&#x20; \* \*\*Returns:\*\* JSON `{"status": "under review", "message": "string"}`

\* `GET /log`

&#x20; \* \*\*Accepts:\*\* None

&#x20; \* \*\*Returns:\*\* JSON array of recent audit log entries.



\## 5. Architecture Diagram



```mermaid

graph TD

&#x20;   %% Submission Flow

&#x20;   A\[Client] -->|Raw Text| B(POST /submit)

&#x20;   B --> C{Rate Limiter}

&#x20;   C -->|Allowed| D\[Signal 1: Groq LLM]

&#x20;   C -->|Allowed| E\[Signal 2: Stylometrics]

&#x20;   D -->|Semantic Score| F\[Confidence Scoring]

&#x20;   E -->|Structural Score| F

&#x20;   F -->|Combined Score| G\[Transparency Labeler]

&#x20;   G -->|Label Text| H\[(SQLite Audit Log)]

&#x20;   H -->|Status 200| A

&#x20;   

&#x20;   %% Appeal Flow

&#x20;   I\[Creator] -->|Submission ID + Reason| J(POST /appeal)

&#x20;   J --> K\[Status Update: Under Review]

&#x20;   K -->|Log Append| H

&#x20;   H -->|Status 200| I



