# AIUB Campus Bot - notes for Claude Code

Read README.md and ARCHITECTURE.md first. Task list to work through: CLAUDE_CODE_PROMPT.md.

## Run and test
- `python app.py` then open http://localhost:8000 (Chrome/Edge for the Mic button)
- `python -m unittest discover tests -v` - run after every change

## Rules
- Core app is pure standard-library Python. Add a dependency only when a task needs it and list it in requirements.txt.
- Make small, targeted edits. Do not rewrite working files.
- Never invent faculty data or campus rules. Answers come only from data/faculty.csv and data/campus_faq.json.
- data/faculty.csv rows with source=demo are placeholders, replace with real data when provided.
- Crisis/harassment messages must never be sent to an LLM. Never expose phone numbers or addresses.
- Do not store raw voice or user text. The log keeps only intent and safety label.
- Keep commit messages short and plain, in the style of a student developer. No AI attribution lines.
