"""Tiny dependency-free BM25 retriever over knowledge/*.md|txt (blank-line separated chunks)."""
import glob, math, os, re
from collections import Counter

_TOK = re.compile(r"[a-z0-9]+")
_STOP = set("a an the is are of to in on and or for with what how do i we you it this that can my be at as by".split())


def _tokens(s):
    return [t for t in _TOK.findall(s.lower()) if t not in _STOP]


class KB:
    def __init__(self, chunks):
        self.chunks = chunks
        self.tf = [Counter(_tokens(c)) for c in chunks]
        self.len = [sum(t.values()) for t in self.tf]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 1.0
        df = Counter(w for t in self.tf for w in t)
        n = len(chunks)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def search(self, q, k=3, min_score=1.0):
        qt = _tokens(q)
        scored = []
        for i, tf in enumerate(self.tf):
            s = 0.0
            for w in qt:
                f = tf.get(w, 0)
                if f:
                    s += self.idf[w] * f * 2.5 / (f + 1.5 * (0.25 + 0.75 * self.len[i] / self.avg))
            if s >= min_score:
                scored.append((s, i))
        return [self.chunks[i] for _, i in sorted(scored, reverse=True)[:k]]


def load(folder=None):
    folder = folder or os.getenv("IQO_KNOWLEDGE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "knowledge"))
    chunks = []
    for f in sorted(glob.glob(os.path.join(folder, "*.md")) + glob.glob(os.path.join(folder, "*.txt"))):
        for c in re.split(r"\n\s*\n", open(f, encoding="utf-8", errors="ignore").read()):
            c = " ".join(c.split())
            if len(c.split()) >= 8 and not c.startswith("#"):
                chunks.append(c)
    return KB(chunks)
