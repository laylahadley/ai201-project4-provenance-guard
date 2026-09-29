# Provenance Guard: Planning & Specification

## 1. Detection Signals
* **Signal 1: LLM-Based Classification (Groq).** Measures semantic coherence and stylistic predictability. The output is a float between 0.0 (definitively human) and 1.0 (definitively AI).
* **Signal 2: Stylometric Heuristics (Python).** Measures structural variance (sentence length and type-token ratio). The output is normalized to a float between 0.0 (high variance/human) and 1.0 (uniform/AI).
* **Combination:** The final confidence score is a weighted average of both signals (50% weight each). 

## 2. Uncertainty Representation
A confidence score of 0.6 means the system detects some artificial traits (e.g., uniform sentence length) but retains enough semantic nuance that it cannot definitively confirm AI origin. 
* **0.00 – 0.35:** Likely Human
* **0.36 – 0.74:** Uncertain
* **0.75 – 1.00:** Likely AI

## 3. Transparency Label Design
* **High-confidence AI (0.75-1.00):** "Content labeled as AI-generated (High Confidence)."
* **High-confidence human (0.00-0.35):** "Content labeled as Human-authored (High Confidence)."
* **Uncertain (0.36-0.74):** "Attribution uncertain. Content displays mixed or inconclusive signals."

## 4. Appeals Workflow
* **Who submits:** The content creator.
* **Information provided:** `submission_id` and a text `reasoning` explaining their drafting process.
* **System action:** Updates the database status of the submission to "under review" and appends the appeal data to the audit log.
* **Reviewer view:** A human reviewer opening the queue sees the original text, the individual signal scores, the final confidence score, and the creator's reasoning side-by-side.

## 5. Anticipated Edge Cases
1. **The Repetitive Poem:** A highly structured, repetitive children's poem with simple vocabulary will score very high for uniformity on the stylometric heuristic, potentially resulting in a false "Likely AI" classification.
2. **The Slang-Edited AI Text:** A user might generate an essay with an AI, then manually inject random slang words and highly varied punctuation. This artificial burstiness breaks the stylometric heuristic, causing a false "Likely Human" score.

## Architecture
When a submission arrives at `POST /submit`, it is processed in parallel by an LLM signal and a stylometric signal, which generate a combined confidence score, assign a transparency label, log the decision to SQLite, and return the result. If a creator contests the label via `POST /appeal`, the system updates the log status to "under review" without overwriting the original decision.

```mermaid
graph TD
    %% Submission Flow
    A[Client] -->|Raw Text| B(POST /submit)
    B --> C{Rate Limiter}
    C -->|Allowed| D[Signal 1: Groq LLM]
    C -->|Allowed| E[Signal 2: Stylometrics]
    D -->|Semantic Score| F[Confidence Scoring]
    E -->|Structural Score| F
    F -->|Combined Score| G[Transparency Labeler]
    G -->|Label Text| H[(SQLite Audit Log)]
    H -->|Status 200| A
    
    %% Appeal Flow
    I[Creator] -->|Submission ID + Reason| J(POST /appeal)
    J --> K[Status Update: Under Review]
    K -->|Log Append| H
    H -->|Status 200| I

## AI Tool Plan
M3 (Submission endpoint + first signal)
	- Provide to AI: Sections 1 (detection signals) and architecture diagram.
	- Ask for: Flask app skeleton with rate limiting, and the implementation of the Groq LLM first signal function.
	- Verify: Test the standalone function with a clear AI input and clear human input directly in a Python script before wiring it 	into the Flask endpoint.
M4 (Second signal + confidence scoring)
	- Provide to AI: Sections 1 (Detection signals), 2 (Uncertainty representation), and Architecture diagram.
	- Ask for: Pure Python stylometric heuristic function (Signal 2) and the logic to calculate the weighted average of both signals.
	- Verify: Run a batch of 5 mixed inputs and check that the combined scores vary meaningfully and do not clump entirely at 0.0 or 	1.0.
M5 (production layer)
	- Provide to AI: Sections 3 (Transparency label design), 4 (Appeals workflow), and Architecture diagram.
	- Ask for: Logic to map the combined score to the three exact label text variants, plus the SQLite audit logging and the POST 	/appeal endpoint.
	- Verify: Trigger submissions that hit all three score thresholds to confirm label exactness, then submit an appeal and query the 	database to ensure the "under review" status applied correctly.