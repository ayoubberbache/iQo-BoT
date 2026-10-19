"""Small dependency-free local RAG index for chemistry references.
Uses token TF-IDF cosine similarity and returns source labels for citations.
"""
import json
import math
import os
import re
from collections import Counter

TOKEN = re.compile(r"[a-z0-9][a-z0-9+^./%-]*")


def _tokens(text):
    return TOKEN.findall(text.lower())


class LocalRAG:
    def __init__(self, path="/artifacts/rag_index.json"):
        self.path = path
        self.docs = []
        self.df = Counter()
        self._load()

    def add(self, source, text):
        for n, chunk in enumerate(re.split(r"\n\s*\n", text)):
            chunk = chunk.strip()
            if len(chunk) < 30:
                continue
            tokens = _tokens(chunk)
            self.docs.append({"id": f"{source}:{n+1}", "source": source, "text": chunk, "tokens": tokens})
            self.df.update(set(tokens))

    def build_default(self):
        from chemistry_reference import context
        from topics import T
        self.docs = []
        self.df = Counter()
        self.add("chemistry_reference", context())
        for topic, item in T.items():
            self.add(f"topic:{topic}", item["tts"])
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"docs": self.docs}, f, ensure_ascii=False)

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                self.docs = json.load(f)["docs"]
            self.df = Counter()
            for doc in self.docs:
                self.df.update(set(doc["tokens"]))
        except (OSError, KeyError, json.JSONDecodeError):
            self.build_default()

    def search(self, query, limit=4):
        q = Counter(_tokens(query))
        if not q or not self.docs:
            return []
        total = len(self.docs)
        qv = {t: (1 + math.log(c)) * math.log((total + 1) / (self.df[t] + 1)) for t, c in q.items()}
        qnorm = math.sqrt(sum(v * v for v in qv.values())) or 1.0
        ranked = []
        for doc in self.docs:
            counts = Counter(doc["tokens"])
            dv = {t: (1 + math.log(c)) * math.log((total + 1) / (self.df[t] + 1)) for t, c in counts.items() if t in qv}
            dot = sum(qv[t] * dv.get(t, 0.0) for t in qv)
            norm = math.sqrt(sum(v * v for v in dv.values())) or 1.0
            score = dot / (qnorm * norm)
            if score > 0:
                ranked.append((score, doc))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [{"source": d["id"], "score": round(s, 4), "text": d["text"]} for s, d in ranked[:limit]]
