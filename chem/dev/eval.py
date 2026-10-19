"""Dev-only. Stage 1 always; Stage 2 + engine if ./artifacts exists.  python dev/eval.py [artifacts_dir]"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import guardrail
from cases import STAGE1, STAGE2

bad = 0
for q, exp in STAGE1:
    got = guardrail.check(q)
    if got != exp:
        bad += 1; print(f"STAGE1 MISS  {q!r} -> {got} (expected {exp})")
print(f"stage1: {len(STAGE1)-bad}/{len(STAGE1)} ok")

art = sys.argv[1] if len(sys.argv) > 1 else "artifacts"
if any(f.endswith(".onnx") for f in os.listdir(art)) if os.path.isdir(art) else False:
    from engine import IQOEngine
    eng = IQOEngine(art)
    miss = 0
    for q, topic in STAGE2:
        r = eng.query(q)
        if r["topic"] != topic:
            miss += 1; print(f"STAGE2 MISS  {q!r} -> {r['topic']} (expected {topic}) [{r['source']}]")
    print(f"stage2: {len(STAGE2)-miss}/{len(STAGE2)} ok  (hand-written paraphrases NOT in the training templates)")
else:
    print("no artifacts found: skipping stage 2 (train first)")
