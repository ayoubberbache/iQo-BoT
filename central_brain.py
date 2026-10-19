"""Central brain: RAG retrieval, specialist routing, then Llama communication."""
import json
import os
import urllib.error
import urllib.request

from chemistry_reference import context
from rag_engine import LocalRAG


class CentralBrain:
    def __init__(self, artifacts="/artifacts"):
        self.url = os.getenv("LLAMA_URL", "http://model-runner.docker.internal/engines/v1/chat/completions")
        self.model = os.getenv("LLAMA_MODEL", "llama3.2")
        self.timeout = float(os.getenv("LLAMA_TIMEOUT", "90"))
        self.rag = LocalRAG(os.path.join(artifacts, "rag_index.json"))

    def _route(self, question, decision):
        q = question.lower()
        emergency = decision.get("safety") == "CRITICAL"
        calculation = any(x in q for x in ("calculate", "equation", "molarity", "moles", "ph", "poh", "dilution", "titration"))
        return {"specialist_first": emergency or calculation, "use_llama": True,
                "reason": "guardrail/classifier priority" if emergency else "calculation or explanation"}

    def answer(self, question, decision):
        route = self._route(question, decision)
        hits = self.rag.search(question, limit=4)
        retrieved = "\n\n".join(f"[{h['source']}] {h['text']}" for h in hits) or context()
        system = f"""You are IQO Bot's central chemistry brain and communication layer.
Routing: {json.dumps(route)}
The specialist decision is authoritative for safety. Never downgrade CRITICAL or WARNING.
Use the retrieved context below, cite its bracketed source labels, and say when evidence is insufficient.
For calculations show equation, values, units, result, and a sanity check.
Do not claim complete chemistry knowledge. For emergencies or unknown substances, use the decision and direct the user to the SDS and trained personnel.

SPECIALIST DECISION:
{json.dumps(decision, ensure_ascii=False)}

RETRIEVED CONTEXT:
{retrieved}"""
        body = json.dumps({"model": self.model, "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question}],
            "temperature": 0.1, "max_tokens": 600}).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode())
            return data["choices"][0]["message"]["content"].strip(), route, hits
        except (OSError, KeyError, IndexError, json.JSONDecodeError) as exc:
            return f"Central brain unavailable ({type(exc).__name__}). Specialist response: {decision['tts']}", route, hits
