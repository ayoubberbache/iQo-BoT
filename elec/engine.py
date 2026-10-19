"""Runtime pipeline: Stage 1 guardrail -> Stage 2 EdgeNet -> (optional) Llama language layer.
The LLM only supplies wording. It can ESCALATE safety (never lower it) and is never used for
guardrail hits or CRITICAL results, so life-safety answers stay deterministic and fast."""
import os, time
import domain_policy
import numpy as np
import guardrail
from config import encode, lcd, SAFETY, INTENTS, ARM_CLASSES, ARM, LED, ARTIFACT
from topics import T, TOPIC_IDS, GENERIC

CONF_MIN = 0.55


class Backend:
    """ONNX Runtime if available (fastest/lightest), else TorchScript."""
    def __init__(self, folder="."):
        onnx = os.path.join(folder, ARTIFACT + ".onnx")
        ts = os.path.join(folder, ARTIFACT + ".pt")
        try:
            import onnxruntime as ort
            so = ort.SessionOptions()
            so.intra_op_num_threads = 1
            so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self.s = ort.InferenceSession(onnx, so, providers=["CPUExecutionProvider"])
            self.run = lambda ids: self.s.run(None, {"ids": ids})
            self.name = "onnxruntime"
        except Exception:
            import torch
            self.m = torch.jit.load(ts).eval()
            def run(ids):
                with torch.no_grad():
                    return [o.numpy() for o in self.m(torch.from_numpy(ids))]
            self.run = run
            self.name = "torchscript"


def _softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()


def payload(topic=None, heads=None, source=""):
    if topic:
        d = T[topic]
        safety, zone, (l1, l2), tts, intent = d["safety"], d["zone"], d["lcd"], d["tts"], d["intent"]
    else:
        safety, zone, intent = heads
        l1, l2, tts = GENERIC[intent]
    return dict(topic=topic, intent=intent, safety=safety, source=source,
                lcd=[lcd(l1), lcd(l2)], led=LED[safety],
                arm=dict(zone=zone, pan=ARM[zone][0], tilt=ARM[zone][1], reach_cm=ARM[zone][2]),
                tts=tts)


class IQOEngine:
    def __init__(self, folder=None, llm="off"):
        self.be = Backend(folder or os.getenv("IQO_ARTIFACTS", "."))
        self.llm_mode, self.brain = llm, None
        if llm != "off":
            from brain import Brain
            self.brain = Brain()

    def query(self, text, goggles=None):
        if not domain_policy.is_in_domain(text):
            return {"topic": None, "intent": "OUT_OF_DOMAIN", "safety": "INFO", "source": "domain-policy", "lcd": ["ELECTRONICS ONLY", "TRUSTED DATA   "], "led": LED["INFO"], "arm": {"zone": "REST", "pan": 0, "tilt": 0, "reach_cm": 10}, "tts": domain_policy.refusal(), "latency_ms": {"guardrail": 0.0, "neural": 0.0, "total": 0.0}}
        t0 = time.perf_counter()
        hit = guardrail.check(text, goggles)
        t1 = time.perf_counter()
        low_conf, nn_ms = False, 0.0
        if hit:
            out = payload(hit, source="stage1-guardrail")
        else:
            s, a, i, emb, tp = self.be.run(encode(text))
            p = _softmax(tp[0])
            k = int(p.argmax())
            if p[k] >= CONF_MIN:
                out = payload(TOPIC_IDS[k], source=f"stage2-edgenet p={p[k]:.2f}")
            else:
                low_conf = True
                out = payload(heads=(SAFETY[int(s[0].argmax())], ARM_CLASSES[int(a[0].argmax())],
                                     INTENTS[int(i[0].argmax())]),
                              source=f"stage2-heads (topic p={p[k]:.2f})")
            nn_ms = (time.perf_counter() - t1) * 1e3
        lat = dict(guardrail=round((t1 - t0) * 1e3, 4), neural=round(nn_ms, 3),
                   total=round((time.perf_counter() - t0) * 1e3, 3))

        # ---- optional Llama language layer (skipped for guardrail hits and CRITICAL) ----
        if self.brain and not hit and out["safety"] != "CRITICAL":
            if low_conf:
                r = self.brain.ask(text, out["safety"])
                if r:
                    out["lcd"] = [lcd(r["lcd1"]), lcd(r["lcd2"])]
                    out["tts"] = r["speech"]
                    out["source"] += " + llm"
                    lat["llm"] = r["ms"]
                    if r["hazard"] and SAFETY.index(out["safety"]) < SAFETY.index("WARNING"):
                        out["safety"], out["led"] = "WARNING", LED["WARNING"]     # escalate only
            elif self.llm_mode == "always":
                r = self.brain.ask(text, out["safety"], known=out["tts"])
                if r:
                    out["detail"] = r["speech"]
                    lat["llm"] = r["ms"]
        out["latency_ms"] = lat
        return out
