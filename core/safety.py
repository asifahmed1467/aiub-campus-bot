"""Safety layer: checks every message BEFORE it reaches the answer engine,
and every answer AFTER it is generated (output guard).

This is a rule-based baseline. Phase 2 of the project replaces `classify`
with a fine-tuned BERT/DistilBERT classifier (see ARCHITECTURE.md).
"""
import re

# Each category: list of regex patterns (English, Bangla script, Banglish)
PATTERNS = {
    "crisis": [
        r"\bsuicid\w*", r"\bkill (my ?self|me)\b", r"\bend (my|it) (life|all)\b",
        r"\bwant to die\b", r"\bself[- ]?harm\b", r"\bcut(ting)? myself\b",
        r"\bmor(t|th)e chai\b", r"\bbachte chai ?na\b", r"\bnijeke shesh\b",
        r"\bmore jabo\b", r"\bjibon(ta)? shesh\b",
        r"আত্মহত্যা", r"মরতে চাই", r"বাঁচতে চাই না", r"নিজেকে শেষ",
    ],
    "harassment": [
        r"\bragg?ing\b", r"\bharass\w*", r"\bbull(y|ied|ying)\b", r"\bstalk\w*",
        r"\bthreat\w*", r"\babuse\w*", r"\bblackmail\w*", r"\bjor kore\b",
        r"হয়রানি", r"র‍্যাগিং", r"হুমকি",
    ],
    "cheating": [
        r"\b(write|do|solve) my (assignment|exam|quiz|lab report|homework)\b",
        r"\bexam (answer|question) leak\w*", r"\bquestion leak\w*",
        r"\bassignment (kore|likhe) dao\b", r"\bexam e (copy|cheat)\b",
        r"\bfake (medical|certificate)\b",
    ],
    "toxic": [r"\bidiot\b", r"\bstupid bot\b", r"\bshut up\b"],
    "stress": [
        r"\bstress(ed)?\b", r"\banxi(ous|ety)\b", r"\bdepress\w*", r"\bburn(ed|t)? ?out\b",
        r"\bcan'?t sleep\b", r"\bpressure\b", r"\btension\b", r"\bmon kharap\b",
        r"\bvoy lagche\b", r"চিন্তা", r"মন খারাপ",
    ],
}

SEVERITY = {"crisis": "high", "harassment": "high", "cheating": "medium",
            "toxic": "low", "stress": "low"}

HELP_CONTACTS = [
    "National Emergency Service (Bangladesh): 999",
    "Kaan Pete Roi emotional support: see kaanpeteroi.org for current numbers",
    "AIUB student counseling office (add the official contact in data/campus_faq.json)",
]

RESPONSES = {
    "crisis": ("I'm really glad you told me. You don't have to go through this alone, "
               "and you deserve support from a real person right now. Please reach out to "
               "someone you trust, or contact one of these: "),
    "harassment": ("That sounds serious, and it is not your fault. You have the right to be safe "
                   "on campus. Please report it to the proctor's office or a faculty member you "
                   "trust. If you're in danger right now, call 999. Other support: "),
    "cheating": ("I can't help with that, because it would break AIUB's academic integrity rules. "
                 "But I'm happy to explain the concept, show a worked example, or quiz you so "
                 "you can solve it yourself."),
    "toxic": "I'm here to help. Let's keep it respectful, and tell me what you need.",
}


def classify(text: str) -> dict:
    """Return {'label', 'severity', 'matches'} for the highest-priority category hit."""
    t = text.lower()
    for label in ["crisis", "harassment", "cheating", "toxic", "stress"]:
        hits = [p for p in PATTERNS[label] if re.search(p, t)]
        if hits:
            return {"label": label, "severity": SEVERITY[label], "matches": len(hits)}
    return {"label": "safe", "severity": "none", "matches": 0}


def blocking_response(result: dict):
    """If the message must NOT go to the normal answer engine, return the safe reply."""
    label = result["label"]
    if label in ("crisis", "harassment"):
        return RESPONSES[label] + " | ".join(HELP_CONTACTS)
    if label in ("cheating", "toxic"):
        return RESPONSES[label]
    return None


BANNED_OUTPUT = [r"\bpassword\b", r"\bphone number\b", r"\bhome address\b", r"\b01[3-9]\d{8}\b"]


def output_guard(answer: str) -> str:
    """Last check before speaking: strip personal data the bot must never reveal."""
    for p in BANNED_OUTPUT:
        if re.search(p, answer, re.I):
            return "Sorry, I can't share personal contact details. I can tell you the faculty member's room and office hours instead."
    return answer
