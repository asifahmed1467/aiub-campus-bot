"""Orchestrator: safety check -> intent routing -> answer engine -> output guard."""
import json
import re
import time
from collections import Counter, deque
from pathlib import Path

from .faculty import FacultyDB
from .knowledge import Knowledge
from .safety import blocking_response, classify, output_guard

DATA = Path(__file__).resolve().parent.parent / "data"

FACULTY_WORDS = r"\b(sir|madam|mam|maam|room|office hour|available|free|kothay|faculty|teacher|kokhon)\b"
GREET = r"^(hi|hello|hey|salam|assalamu alaikum|kemon acho|hola)\b"


class Assistant:
    def __init__(self):
        self.faculty = FacultyDB(DATA / "faculty.csv")
        self.kb = Knowledge(DATA / "campus_faq.json")
        self.stats = Counter()
        self.log = deque(maxlen=50)  # anonymized: label + intent only, never raw text

    def _intent(self, text):
        t = text.lower()
        if re.search(GREET, t):
            return "greeting"
        f, _ = self.faculty.find(text)
        if f and (re.search(FACULTY_WORDS, t) or len(t.split()) <= 4):
            return "faculty"
        return "campus_faq"

    def handle(self, text: str, now=None) -> dict:
        t0 = time.perf_counter()
        text = (text or "").strip()[:500]
        if not text:
            return {"reply": "I didn't catch that. Please try again.", "intent": "empty"}

        safety = classify(text)
        pipeline = [{"step": "Speech to text", "detail": "browser / Whisper"},
                    {"step": "Safety classifier", "detail": safety["label"]}]
        blocked = blocking_response(safety)

        if blocked:
            intent, reply, extra = "safety_escalation", blocked, {}
            pipeline.append({"step": "Crisis / policy response", "detail": safety["label"]})
        else:
            intent = self._intent(text)
            pipeline.append({"step": "Intent router", "detail": intent})
            extra = {}
            if intent == "greeting":
                reply = ("Hi! I'm your AIUB Campus Companion. Ask me things like "
                         "\"Nyme Ahmed madam er room number ki?\" or \"How is CGPA calculated?\"")
            elif intent == "faculty":
                r = self.faculty.answer(text, now)
                reply = r["text"]
                extra = {"faculty": r.get("faculty"), "match": r.get("match")}
                pipeline.append({"step": "Faculty database", "detail": f"match {r.get('match', 0)}"})
            else:
                r = self.kb.answer(text)
                reply = r["text"]
                extra = {"source": r.get("source"), "confidence": r.get("confidence")}
                pipeline.append({"step": "Knowledge base (RAG)", "detail": f"confidence {r.get('confidence')}"})
            if safety["label"] == "stress":
                reply += (" It sounds like you're under some pressure. Take a short break, breathe slowly, "
                          "and talk to someone you trust. AIUB counseling is there for you too.")

        reply = output_guard(reply)
        pipeline += [{"step": "Output guard", "detail": "passed"},
                     {"step": "Text to speech", "detail": "browser / Parler-TTS"}]

        self.stats[intent] += 1
        self.stats["safety_" + safety["label"]] += 1
        self.log.appendleft({"time": time.strftime("%H:%M:%S"), "intent": intent,
                             "safety": safety["label"], "severity": safety["severity"]})
        return {"reply": reply, "intent": intent, "safety": safety, "pipeline": pipeline,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1), **extra}

    def dashboard(self):
        return {"stats": dict(self.stats), "log": list(self.log)}
