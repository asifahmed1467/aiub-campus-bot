"""Faculty lookup: fuzzy name matching + room number + live/next availability.

Data comes ONLY from data/faculty.csv (never invented by a model).
"""
import csv
import difflib
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

DHAKA = timezone(timedelta(hours=6))
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WORKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
DAY_START, DAY_END = "09:00", "17:30"
STOP = {"sir", "madam", "mam", "maam", "er", "ki", "room", "number", "no", "kothay",
        "where", "is", "the", "what", "of", "ta", "teacher", "faculty", "now", "free",
        "available", "kokhon", "when", "next", "will", "be", "ache", "achen", "office",
        "hour", "hours", "dr", "prof", "mr", "ms", "and", "his", "her", "uni", "ekhon",
        "can", "i", "meet", "tell", "me", "about", "please", "koi", "ar", "ke"}


def norm(w):
    """Phonetic-ish normalisation so Banglish/STT spellings match (najeeb ~ nazib)."""
    w = w.lower().replace("ee", "i").replace("z", "j").replace("ph", "f").replace("w", "v")
    return re.sub(r"(.)\1+", r"\1", w)


def _t(s):
    return datetime.strptime(s, "%H:%M").time()


class FacultyDB:
    def __init__(self, path: Path):
        self.faculty = {}
        with open(path, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                f = self.faculty.setdefault(r["faculty_id"], {
                    "id": r["faculty_id"], "name": r["name"],
                    "aliases": [a.strip() for a in r["aliases"].split("|") if a.strip()],
                    "designation": r["designation"], "department": r["department"],
                    "building": r["building"], "room_no": r["room_no"],
                    "source": r.get("source", ""), "schedule": []})
                f["schedule"].append({"day": r["day"], "start": r["start"],
                                      "end": r["end"], "type": r["type"]})
        for f in self.faculty.values():
            f["schedule"].sort(key=lambda s: (DAYS.index(s["day"]), s["start"]))

    # ---------- name matching ----------
    def find(self, text: str):
        """Return (faculty, score) best matching any name/alias token in the text."""
        words = [w for w in re.findall(r"[a-zA-Z]+", text.lower()) if w not in STOP]
        if not words:
            return None, 0.0
        best, best_score = None, 0.0
        for f in self.faculty.values():
            names = [f["name"]] + f["aliases"]
            tokens = {w.lower() for n in names for w in re.findall(r"[a-zA-Z]+", n)} - STOP
            for w in words:
                for tok in tokens:
                    s = difflib.SequenceMatcher(None, norm(w), norm(tok)).ratio()
                    if s > best_score:
                        best, best_score = f, s
        return (best, best_score) if best_score >= 0.75 else (None, best_score)

    # ---------- availability ----------
    def status(self, f, now: datetime = None) -> dict:
        now = now or datetime.now(DHAKA)
        day, t = DAYS[now.weekday()], now.time()
        for s in f["schedule"]:
            if s["day"] == day and _t(s["start"]) <= t < _t(s["end"]):
                if s["type"] == "office_hour":
                    return {"state": "available", "label": f"In office hour until {s['end']}",
                            "until": s["end"]}
                return {"state": "busy", "label": f"In class until {s['end']}", "until": s["end"]}
        if day in WORKDAYS and _t(DAY_START) <= t < _t(DAY_END):
            return {"state": "free", "label": "Not in class right now (may be in office)", "until": None}
        return {"state": "off", "label": "Outside university hours", "until": None}

    def next_office_hour(self, f, now: datetime = None):
        now = now or datetime.now(DHAKA)
        for add in range(0, 8):
            d = now + timedelta(days=add)
            day = DAYS[d.weekday()]
            for s in f["schedule"]:
                if s["day"] == day and s["type"] == "office_hour":
                    if add > 0 or _t(s["start"]) > now.time():
                        when = "today" if add == 0 else ("tomorrow" if add == 1 else day)
                        return {"day": day, "when": when, "start": s["start"], "end": s["end"]}
        return None

    def answer(self, text: str, now: datetime = None) -> dict:
        f, score = self.find(text)
        if not f:
            return {"found": False, "text": "I couldn't find that faculty member. Could you say the full name?"}
        st = self.status(f, now)
        nxt = self.next_office_hour(f, now)
        reply = (f"{f['name']} ({f['designation']}, {f['department']}) sits in room "
                 f"{f['room_no']}, building {f['building']}. {st['label']}.")
        if st["state"] != "available" and nxt:
            reply += f" Next office hour: {nxt['when']} {nxt['start']} to {nxt['end']}."
        return {"found": True, "text": reply, "faculty": self.public(f, now), "match": round(score, 2)}

    def public(self, f, now: datetime = None) -> dict:
        d = {k: v for k, v in f.items()}
        d["status"] = self.status(f, now)
        d["next_office_hour"] = self.next_office_hour(f, now)
        return d

    def all(self, now: datetime = None):
        return [self.public(f, now) for f in self.faculty.values()]
