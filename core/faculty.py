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
DAY_START, DAY_END = "08:00", "17:30"
STOP = {"sir", "madam", "mam", "maam", "er", "ki", "room", "number", "no", "kothay",
        "where", "is", "the", "what", "of", "ta", "teacher", "faculty", "now", "free",
        "available", "kokhon", "when", "next", "will", "be", "ache", "achen", "office",
        "hour", "hours", "dr", "prof", "mr", "ms", "and", "his", "her", "uni", "ekhon",
        "can", "i", "meet", "tell", "me", "about", "please", "koi", "ar", "ke"}


def norm(w):
    """Phonetic-ish normalisation so Banglish/STT spellings match (najeeb ~ nazib)."""
    w = w.lower().replace("ee", "i").replace("z", "j").replace("ph", "f").replace("w", "v")
    return re.sub(r"(.)\1+", r"\1", w)


MIN_TOKEN = 3  # ignore 1-2 letter fragments like "Md" or "Al"


def _words(s):
    return [w for w in re.findall(r"[a-zA-Z]+", s.lower()) if len(w) >= MIN_TOKEN and w not in STOP]


def base_designation(d):
    """'Assistant Professor (on Leave)' -> 'Assistant Professor'"""
    return re.sub(r"\s*\(.*?\)", "", d).strip()


def _t(s):
    return datetime.strptime(s, "%H:%M").time()


class FacultyDB:
    def __init__(self, path: Path):
        self.faculty = {}
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                f = self.faculty.setdefault(r["faculty_id"], {
                    "id": r["faculty_id"], "name": r["name"],
                    "aliases": [a.strip() for a in r["aliases"].split("|") if a.strip()],
                    "designation": r["designation"], "department": r["department"],
                    "building": r["building"], "room_no": r["room_no"],
                    "source": r.get("source", ""), "schedule": []})
                if r.get("day") and r.get("start") and r.get("end"):  # rows with no timetable are fine
                    f["schedule"].append({"day": r["day"], "start": r["start"], "end": r["end"],
                                          "type": r["type"], "note": r.get("note", "")})
        for f in self.faculty.values():
            f["schedule"].sort(key=lambda s: (DAYS.index(s["day"]), s["start"]))

    # ---------- name matching ----------
    def rank(self, text: str):
        """[(score, faculty)] best first. Score = sum of per-word matches, so a full name
        beats a shared first/last name."""
        words = _words(text)
        out = []
        for f in self.faculty.values():
            toks = {w for n in [f["name"]] + f["aliases"] for w in _words(n)}
            total = 0.0
            for w in words:
                best = max((difflib.SequenceMatcher(None, norm(w), norm(t)).ratio() for t in toks), default=0.0)
                if best >= 0.75:
                    total += best
            if total > 0:
                out.append((total, f))
        out.sort(key=lambda x: -x[0])
        return out

    def find(self, text: str):
        """Return (faculty, match score 0-1) or (None, 0)."""
        r = self.rank(text)
        if not r:
            return None, 0.0
        return r[0][1], r[0][0] / len(_words(text))

    # ---------- availability ----------
    def status(self, f, now: datetime = None) -> dict:
        now = now or datetime.now(DHAKA)
        if "leave" in f["designation"].lower():
            return {"state": "leave", "label": "Currently on leave", "until": None}
        if not f["schedule"]:
            return {"state": "unknown", "label": "Timetable not available yet", "until": None}
        day, t = DAYS[now.weekday()], now.time()
        for s in f["schedule"]:
            if s["day"] == day and _t(s["start"]) <= t < _t(s["end"]):
                if s["type"] == "office_hour":
                    return {"state": "available", "label": f"In office hour until {s['end']}",
                            "until": s["end"]}
                if s["type"] == "admin":
                    return {"state": "admin", "label": f"In admin hour until {s['end']}", "until": s["end"]}
                return {"state": "busy", "label": f"In class until {s['end']}", "until": s["end"]}
        if day in WORKDAYS and _t(DAY_START) <= t < _t(DAY_END):
            return {"state": "free", "label": "No class scheduled right now", "until": None}
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
        ranked = self.rank(text)
        if not ranked:
            return {"found": False, "text": "I couldn't find that faculty member. Could you say the full name?"}
        top = [f for sc, f in ranked if abs(sc - ranked[0][0]) < 1e-9]
        if len(top) > 1:
            who = "; ".join(f"{f['name']} (room {f['room_no']})" for f in top[:4])
            return {"found": False, "ambiguous": True,
                    "text": f"I found more than one match: {who}. Which one do you mean?"}
        f, score = self.find(text)
        st = self.status(f, now)
        reply = (f"{f['name']} ({base_designation(f['designation'])}, {f['department']}) sits in room "
                 f"{f['room_no']}, building {f['building']}.")
        if st["state"] == "unknown":
            reply += " Their timetable isn't available yet."
        elif st["state"] == "leave":
            reply += " They are currently on leave."
        else:
            reply += f" {st['label']}."
            nxt = self.next_office_hour(f, now)
            if st["state"] != "available":
                reply += (f" Next office hour: {nxt['when']} {nxt['start']} to {nxt['end']}."
                          if nxt else " No office hours are listed.")
        return {"found": True, "text": reply, "faculty": self.public(f, now), "match": round(score, 2)}

    def public(self, f, now: datetime = None) -> dict:
        d = {k: v for k, v in f.items()}
        d["status"] = self.status(f, now)
        d["next_office_hour"] = self.next_office_hour(f, now)
        return d

    def all(self, now: datetime = None):
        return [self.public(f, now) for f in self.faculty.values()]
