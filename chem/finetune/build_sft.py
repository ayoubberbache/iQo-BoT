"""Build a chat-format SFT set from this project's own topics + templates (no downloads).
Teaches Llama the exact JSON wording/safety behaviour the bot uses.  python finetune/build_sft.py"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_gen import generate
from topics import T, TOPIC_IDS

here = os.path.dirname(os.path.abspath(__file__))
system = re.search(r'SYSTEM """(.*?)"""', open(os.path.join(here, "..", "llm", "Modelfile")).read(), re.S).group(1)
X, ys, ya, yi, yt = generate(per_topic=150, seed=7)
n = 0
with open(os.path.join(here, "sft.jsonl"), "w") as f:
    for q, t in zip(X, yt):
        d = T[TOPIC_IDS[t]]
        user = (f"Student question: {q}\n\nSafety level decided by the safety system: {d['safety']}. "
                'Never contradict it.\n\nReply as JSON with keys "lcd1" and "lcd2" (UPPERCASE, max 16 characters each), '
                '"speech" (spoken style, max 45 words, no markdown) and "hazard" (true if the situation could injure someone).')
        ans = json.dumps({"lcd1": d["lcd"][0], "lcd2": d["lcd"][1], "speech": d["tts"],
                          "hazard": d["safety"] in ("WARNING", "CRITICAL")})
        f.write(json.dumps({"messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user},
                                         {"role": "assistant", "content": ans}]}) + "\n")
        n += 1
print(f"wrote {n} examples to finetune/sft.jsonl")
