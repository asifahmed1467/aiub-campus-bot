# AIUB Campus Companion

Voice + text campus assistant: faculty room and availability lookup, campus FAQ (RAG),
and a safety layer for distress, harassment and cheating requests.

## Run (no installs, Python 3.9+)
    python app.py
Open http://localhost:8000 in Chrome or Edge (needed for the Mic button).
Tests: `python -m unittest discover tests -v`

## Data
- `data/faculty.csv` - real faculty rooms; timetables only for some faculty (empty = shown as "unknown", never guessed). Types: class, office_hour, admin. "on leave" in the designation is shown as on leave.
- `data/campus_faq.json` - sample answers marked "SAMPLE"; verify and replace with official AIUB text.

## Files
- `core/safety.py` input classifier + output guard
- `core/faculty.py` fuzzy name match, room, status, next office hour
- `core/knowledge.py` TF-IDF retrieval with "I'm not sure" threshold
- `core/assistant.py` orchestrator   - `app.py` server   - `static/index.html` UI

## Live demo (GitHub Pages)
https://asifahmed1467.github.io/aiub-campus-bot/

The `docs/` folder is a static copy of the app that runs fully in the browser (no server).
It is generated from the same data and rules as the Python app:

    python scripts/build_pages_data.py     # rebuild docs/data.js after editing data/ or core/safety.py

`docs/engine.js` is a JavaScript port of `core/`. If you change the logic in `core/`, update it too.

To publish: repo Settings -> Pages -> Source: "Deploy from a branch" -> Branch: `main`, folder `/docs` -> Save.
