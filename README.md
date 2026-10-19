# AIUB Campus Companion

Voice + text campus assistant: faculty room and availability lookup, campus FAQ (RAG),
and a safety layer for distress, harassment and cheating requests.

## Run (no installs, Python 3.9+)
    python app.py
Open http://localhost:8000 in Chrome or Edge (needed for the Mic button).
Tests: `python -m unittest discover tests -v`

## Data
- `data/faculty.csv` - DEMO data: names/rooms/schedules are placeholders. Replace with real AIUB data.
- `data/campus_faq.json` - sample answers marked "SAMPLE"; verify and replace with official AIUB text.

## Files
- `core/safety.py` input classifier + output guard
- `core/faculty.py` fuzzy name match, room, status, next office hour
- `core/knowledge.py` TF-IDF retrieval with "I'm not sure" threshold
- `core/assistant.py` orchestrator   - `app.py` server   - `static/index.html` UI
