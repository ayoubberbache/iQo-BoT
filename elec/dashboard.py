"""Terminal dashboard. Options: --llm off|fallback|always   Commands: /goggles on|off|auto, /quit"""
import argparse, textwrap
from engine import IQOEngine

RESET, DIM = "\033[0m", "\033[2m"
COL = {"SOLID GREEN": "\033[92m", "CYAN BLUE": "\033[96m", "SOLID AMBER": "\033[93m", "FLASHING RED": "\033[91;5m"}


class CameraStub:
    """Replace .goggles() with your Roboflow / YOLO PPE detector. None = unknown."""
    state = None
    def goggles(self): return self.state


def show(r):
    c, a = COL[r["led"]], r["arm"]
    print("\n  ┌─ LCD 16x2 ─────┐")
    for line in r["lcd"]:
        print(f"  │{line}│")
    print("  └────────────────┘")
    print(f"  LED    : {c}● {r['led']}{RESET}   [{r['safety']}]   intent: {r['intent']}")
    print(f"  ARM    : {a['zone']}  (pan {a['pan']:+d}°, tilt {a['tilt']:+d}°, reach {a['reach_cm']} cm)")
    print("  TTS    : " + "\n           ".join(textwrap.wrap(r["tts"], 70)))
    if r.get("detail"):
        print("  MORE   : " + "\n           ".join(textwrap.wrap(r["detail"], 70)))
    l = r["latency_ms"]
    extra = f", llm {l['llm']} ms" if "llm" in l else ""
    print(f"  {DIM}LATENCY: {l['total']} ms edge (guardrail {l['guardrail']} ms, neural {l['neural']} ms){extra}  via {r['source']}{RESET}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", choices=["off", "fallback", "always"], default="off")
    ap.add_argument("--artifacts", default=None)
    a = ap.parse_args()
    eng, cam = IQOEngine(a.artifacts, llm=a.llm), CameraStub()
    note = ""
    if eng.brain:
        note = f", llm: {eng.brain.model} ({'online' if eng.brain.available() else 'NOT FOUND - falling back to edge only'})"
    print(f"IQO Bot ready (backend: {eng.be.name}{note}).  /goggles on|off|auto  /quit")
    while True:
        try:
            q = input("Enter the query: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q: continue
        if q == "/quit": break
        if q.startswith("/goggles"):
            cam.state = {"on": True, "off": False}.get(q.split()[-1]); print(f"  camera goggles = {cam.state}"); continue
        show(eng.query(q, cam.goggles()))


if __name__ == "__main__":
    main()
