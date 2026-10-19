"""Chat entrypoint: deterministic specialist pipeline plus Llama central brain."""
import argparse
import json

from central_brain import CentralBrain
from engine import IQOEngine


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--artifacts", default="/artifacts")
    args = ap.parse_args()
    engine = IQOEngine(args.artifacts)
    brain = CentralBrain(args.artifacts)
    print(f"IQO central brain ready ({brain.model}). Type /quit to exit.")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question == "/quit":
            break
        if not question:
            continue
        decision = engine.query(question)
        print(json.dumps(decision, ensure_ascii=False))
        answer, route, hits = brain.answer(question, decision)
        print(json.dumps({"route": route, "sources": hits}, ensure_ascii=False))
        print(f"IQO: {answer}")


if __name__ == "__main__":
    main()
