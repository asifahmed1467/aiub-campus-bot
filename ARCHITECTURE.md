# Architecture

```mermaid
flowchart TD
  U[Student voice or text] --> UI[Web UI: Mic + chat + live pipeline view]
  UI --> STT[Speech to text: browser now, fine-tuned Whisper later]
  STT --> SAFE{Safety classifier}
  SAFE -- crisis / harassment --> ESC[Crisis response + help contacts]
  SAFE -- cheating / toxic --> POL[Policy reply, teach instead]
  SAFE -- safe / stress --> INT[Intent router]
  INT -- faculty --> FAC[Faculty DB: fuzzy match, room, status, next office hour]
  INT -- campus --> RAG[Knowledge base: TF-IDF now, embeddings + LLM later]
  INT -- greeting --> GRT[Greeting]
  FAC --> OG[Output guard: no personal data]
  RAG --> OG
  GRT --> OG
  ESC --> OG
  POL --> OG
  OG --> TTS[Text to speech: browser now, Parler-TTS later]
  TTS --> UI
  OG --> LOG[Anonymous log: intent + label only] --> DASH[Analytics panel]
```

## Phase 1 (this repo, working today)
Rule-based safety, TF-IDF retrieval, CSV faculty DB, browser STT/TTS.
## Phase 2 (upgrade path, matches the thesis plan)
| Component | Now | Upgrade |
|---|---|---|
| STT | Browser Web Speech API | Whisper fine-tuned on Bangla/Banglish |
| TTS | Browser speechSynthesis | Indic Parler-TTS (pretrained, no fine-tune) |
| Safety | Regex rules (EN/Bangla/Banglish) | Fine-tuned DistilBERT, report precision/recall |
| Retrieval | TF-IDF | Sentence embeddings + ChromaDB |
| Answering | Template | Llama 3 / Qwen + small LoRA, grounded on retrieved text |
## Safety rules
Crisis/harassment never reach the LLM; answers only from verified data; unknown means "I'm not sure";
no phone numbers or addresses; no raw voice or text stored.
