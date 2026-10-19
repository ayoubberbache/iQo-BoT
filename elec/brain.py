"""Llama brain via Ollama's HTTP API. Supplies WORDING only (LCD lines + spoken text + hazard flag).
Env: OLLAMA_HOST (default http://localhost:11434), IQO_LLM_MODEL (e.g. iqo-chem / iqo-elec)."""
import json, os, time, urllib.error, urllib.request
import rag
import domain_policy

SCHEMA = {
    "type": "object",
    "properties": {
        "lcd1": {"type": "string"}, "lcd2": {"type": "string"},
        "speech": {"type": "string"}, "hazard": {"type": "boolean"},
    },
    "required": ["lcd1", "lcd2", "speech", "hazard"],
}


def _host():
    h = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    return h if h.startswith("http") else "http://" + h


class Brain:
    def __init__(self, model=None, host=None, timeout=60):
        self.model = model or os.getenv("IQO_LLM_MODEL", "iqo-brain")
        self.host = (host or _host()).rstrip("/")
        self.timeout = timeout
        self.kb = rag.load()

    def _post(self, path, body):
        req = urllib.request.Request(self.host + path, json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return json.loads(r.read().decode())

    def available(self):
        try:
            with urllib.request.urlopen(self.host + "/api/tags", timeout=3) as r:
                names = [m["name"] for m in json.loads(r.read().decode()).get("models", [])]
            return any(n.split(":")[0] == self.model.split(":")[0] for n in names)
        except Exception:
            return False

    def ask(self, query, safety, known=None):
        if not domain_policy.is_in_domain(query):
            return {"lcd1": "ELEC ONLY", "lcd2": "TRUSTED DATA", "speech": domain_policy.refusal(), "hazard": False, "ms": 0}
        notes = self.kb.search(query, k=3)
        parts = [f"Student question: {query}",
                 f"Safety level decided by the safety system: {safety}. Never contradict it."]
        if notes:
            parts.append("Verified notes:\n" + "\n".join("- " + n for n in notes))
        if known:
            parts.append(f"The robot already said: {known}\nAdd one or two new helpful sentences.")
        parts.append('Reply as JSON with keys "lcd1" and "lcd2" (UPPERCASE, max 16 characters each), '
                     '"speech" (spoken style, max 45 words, no markdown) and "hazard" '
                     '(true if the situation could injure someone).')
        body = {"model": self.model, "stream": False, "keep_alive": "30m",
                "messages": [{"role": "user", "content": "\n\n".join(parts)}],
                "options": {"temperature": 0.2, "num_predict": 200}}
        t0 = time.perf_counter()
        try:
            try:
                r = self._post("/api/chat", {**body, "format": SCHEMA})
            except urllib.error.HTTPError:                       # older Ollama: plain JSON mode
                r = self._post("/api/chat", {**body, "format": "json"})
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            return None
        ms = round((time.perf_counter() - t0) * 1e3)
        raw = r.get("message", {}).get("content", "")
        try:
            d = json.loads(raw)
            speech = " ".join(str(d.get("speech", "")).split()[:60])
            if not speech:
                raise ValueError
            return dict(lcd1=str(d.get("lcd1", "AI ANSWER"))[:16], lcd2=str(d.get("lcd2", ""))[:16],
                        speech=speech, hazard=bool(d.get("hazard", False)), ms=ms)
        except (ValueError, TypeError):
            return dict(lcd1="AI ANSWER", lcd2="ASK INSTRUCTOR", hazard=False, ms=ms,
                        speech=" ".join(raw.split()[:60]) or "I am not sure. Please ask your instructor.")
