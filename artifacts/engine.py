"""Runtime pipeline: Stage 1 guardrail -> Stage 2 EdgeChemNet -> unified hardware payload."""
import os, time
import numpy as np
import guardrail
from config import encode, lcd, SAFETY, INTENTS, ARM_CLASSES, ARM, LED
from topics import T, TOPIC_IDS, GENERIC

CONF_MIN = 0.55


class Backend:
    """Loads ONNX Runtime if present (fastest/lightest), else TorchScript."""
    def __init__(self, folder="."):
        onnx = os.path.join(folder, "edge_chem_net.onnx")
        ts = os.path.join(folder, "edge_chem_net.pt")
        try:
            import onnxruntime as ort
            so = ort.SessionOptions(); so.intra_op_num_threads = 1
            self.s = ort.InferenceSession(onnx, so)
            self.run = lambda ids: self.s.run(None, {"ids": ids})
            self.name = "onnxruntime"
        except Exception:
            import torch
            self.m = torch.jit.load(ts).eval()
            def run(ids):
                with torch.no_grad():
                    return [o.numpy() for o in self.m(torch.from_numpy(ids))]
            self.run = run; self.name = "torchscript"


def _softmax(x):
    e = np.exp(x - x.max()); return e / e.sum()


def payload(topic=None, heads=None, source="", extra=""):
    if topic:
        d = T[topic]; safety, zone, l1, l2, tts, intent = d["safety"], d["zone"], *d["lcd"], d["tts"], d["intent"]
    else:
        safety, zone, intent = heads
        l1, l2, tts = GENERIC[intent]
    return dict(topic=topic, intent=intent, safety=safety, source=source,
                lcd=[lcd(l1), lcd(l2)], led=LED[safety],
                arm=dict(zone=zone, pan=ARM[zone][0], tilt=ARM[zone][1], reach_cm=ARM[zone][2]),
                tts=(extra + " " + tts).strip())


class IQOEngine:
    def __init__(self, folder="."):
        self.be = Backend(folder)

    def query(self, text, goggles=None):
        t0 = time.perf_counter()
        hit = guardrail.check(text, goggles)
        t1 = time.perf_counter()
        if hit:
            out = payload(hit, source="stage1-guardrail")
            nn_ms = 0.0
        else:
            s, a, i, emb, tp = self.be.run(encode(text))
            p = _softmax(tp[0]); k = int(p.argmax()); t2 = time.perf_counter()
            if p[k] >= CONF_MIN:
                out = payload(TOPIC_IDS[k], source=f"stage2-edgechemnet p={p[k]:.2f}")
            else:                                          # low confidence -> head-only answer
                sf = SAFETY[int(s[0].argmax())]
                out = payload(heads=(sf, ARM_CLASSES[int(a[0].argmax())], INTENTS[int(i[0].argmax())]),
                              source=f"stage2-heads (topic p={p[k]:.2f})")
            nn_ms = (time.perf_counter() - t1) * 1e3
        out["latency_ms"] = dict(guardrail=round((t1 - t0) * 1e3, 4), neural=round(nn_ms, 3),
                                 total=round((time.perf_counter() - t0) * 1e3, 3))
        return out
