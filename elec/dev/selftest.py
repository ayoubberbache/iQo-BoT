"""Dev-only: Stage 1 + payload formatting without a trained model."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import guardrail, engine

cases = [("i got an electric shock", "CRITICAL", "POWER_SUPPLY"),
         ("my lipo is swollen", "CRITICAL", "FIRE_EXTINGUISHER"),
         ("why do lipo batteries swell", "WARNING", "FIRE_EXTINGUISHER"),
         ("opening the plugged in power supply to fix it", "CRITICAL", "POWER_SUPPLY"),
         ("soldering without the fume extractor", "WARNING", "FUME_EXTRACTOR")]
for q, sf, zone in cases:
    r = engine.payload(guardrail.check(q), source="t")
    assert r["safety"] == sf and r["arm"]["zone"] == zone, (q, r)
    assert all(len(x) == 16 for x in r["lcd"])
r = engine.payload(guardrail.check("soldering", goggles=False), source="t")
assert r["safety"] == "WARNING" and r["arm"]["zone"] == "GOGGLE_RACK" and r["led"] == "SOLID AMBER"
print("selftest OK")
