"""Dev-only: checks Stage 1 + payload formatting without a trained model."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import guardrail, engine
from config import SAFETY

cases = [("I just mixed bleach and ammonia", "CRITICAL", "FUME_HOOD"),
         ("why is mixing bleach and ammonia dangerous", "WARNING", "FUME_HOOD"),
         ("acid splashed on my eyes", "CRITICAL", "EYEWASH_STATION"),
         ("how do i dilute 98% h2so4", "WARNING", "FUME_HOOD")]
for q, sf, zone in cases:
    r = engine.payload(guardrail.check(q), source="t")
    assert r["safety"] == sf and r["arm"]["zone"] == zone, (q, r)
    assert all(len(x) == 16 for x in r["lcd"])
r = engine.payload(guardrail.check("titrating", goggles=False), source="t")
assert r["safety"] == "WARNING" and r["arm"]["zone"] == "GOGGLE_RACK" and r["led"] == "SOLID AMBER"
print("selftest OK")
