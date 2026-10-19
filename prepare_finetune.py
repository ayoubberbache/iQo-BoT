"""Prepare JSONL instruction data for later LoRA/SFT fine-tuning.
This does not alter Llama weights; it creates a reviewable training set.
"""
import argparse
import json
from pathlib import Path

from chemistry_reference import context
from topics import T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="/artifacts/llama_sft.jsonl")
    args = ap.parse_args()
    rows = []
    system = "You are IQO Bot. Follow deterministic safety decisions, cite retrieved context, show units in calculations, and defer emergencies to trained personnel."
    for topic, item in T.items():
        rows.append({"messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Explain the chemistry and safety guidance for {topic}."},
            {"role": "assistant", "content": item["tts"]},
        ]})
    rows.append({"messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": "What equations should I use for chemistry calculations?"},
        {"role": "assistant", "content": context()},
    ]})
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} review examples to {path}")


if __name__ == "__main__":
    main()
