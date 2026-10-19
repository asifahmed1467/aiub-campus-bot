# Prompt for Claude Code (paste this, with the project folder open)

You are my co-developer. Project: AIUB Campus Companion in this folder (read README.md and ARCHITECTURE.md first).
It already runs with `python app.py` and all tests pass. Constraints: I have limited time and tokens, so make
small, targeted edits, do not rewrite working files, and run the tests after each change.

Do these tasks in order, stopping after each to run `python -m unittest discover tests`:
1. Replace the DEMO rows in data/faculty.csv with the real data I will paste (keep the same columns). Keep source="real".
2. Replace the SAMPLE answers in data/campus_faq.json with the official AIUB text I provide.
3. Add 15 more safety test phrases (English, Bangla script, Banglish) to tests/test_all.py and fix any misses in core/safety.py.
4. Add a /api/stt endpoint that accepts a WAV upload and transcribes it with faster-whisper (model "small"); keep the browser Mic as fallback.
5. Add TTS using ai4bharat/indic-parler-tts for Bangla replies, falling back to the browser voice if the model is not installed.
6. Add scripts/eval_safety.py that reads data/safety_eval.csv (text,label) and prints precision, recall and F1 per label.
7. Polish static/index.html: keep the dark theme, add a Bangla/English UI toggle.
Rules: never invent faculty data or campus rules; answers come only from data files; crisis messages never go to a model;
never expose phone numbers; do not store raw voice or text. Keep it dependency-light and explain each change in 2 lines.
