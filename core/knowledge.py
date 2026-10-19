"""Mini RAG: TF-IDF retrieval over campus FAQ documents (pure Python).

Answers ONLY from data/campus_faq.json. Below the confidence threshold the bot
says "I'm not sure" instead of guessing (hallucination control).
Phase 2: swap for sentence-embeddings + ChromaDB + a LoRA fine-tuned LLM.
"""
import json
import math
import re
from collections import Counter
from pathlib import Path

STOP = {"the", "a", "an", "is", "are", "what", "how", "do", "i", "to", "of", "in", "for",
        "my", "and", "can", "ki", "kivabe", "kothay", "er", "e", "ta", "where", "when"}


def tok(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


class Knowledge:
    def __init__(self, path: Path, threshold: float = 0.18):
        self.docs = json.loads(Path(path).read_text(encoding="utf-8"))
        self.threshold = threshold
        texts = [tok(d["question"] + " " + " ".join(d.get("keywords", [])) + " " + d["answer"])
                 for d in self.docs]
        n = len(texts)
        df = Counter(w for t in texts for w in set(t))
        self.idf = {w: math.log((n + 1) / (c + 1)) + 1 for w, c in df.items()}
        self.vecs = [self._vec(t) for t in texts]

    def _vec(self, tokens):
        tf = Counter(tokens)
        v = {w: c * self.idf.get(w, 0) for w, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        return {w: x / norm for w, x in v.items()}

    def search(self, query, k=3):
        q = self._vec(tok(query))
        scored = [(sum(q.get(w, 0) * x for w, x in v.items()), i) for i, v in enumerate(self.vecs)]
        scored.sort(reverse=True)
        return [(round(s, 3), self.docs[i]) for s, i in scored[:k]]

    def answer(self, query):
        hits = self.search(query)
        if not hits or hits[0][0] < self.threshold:
            return {"found": False, "confidence": hits[0][0] if hits else 0,
                    "text": "I'm not sure about that. Please check the AIUB website or ask the relevant office."}
        score, doc = hits[0]
        return {"found": True, "confidence": score, "text": doc["answer"],
                "source": doc.get("source", "campus_faq.json"), "topic": doc["question"]}
