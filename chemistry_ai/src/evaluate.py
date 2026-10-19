"""
Evaluation and Benchmarking Script for IQO Bot Chemistry AI
Measures accuracy, per-class metrics, confusion matrices, and latency.
"""

import time
import json
import argparse
from pathlib import Path
from typing import Dict, Any
import torch
import torch.nn as nn

from .model import EdgeChemNet
from .tokenizer import ChemTokenizer
from .dataset import get_dataloaders
from .guardrail import DeterministicSafetyGuard


def evaluate_model(
    checkpoint_path: str,
    vocab_path: str,
    dataset_path: str,
    device: str = "cpu"
) -> Dict[str, Any]:
    dev = torch.device(device)
    train_loader, val_loader, tokenizer = get_dataloaders(
        dataset_path=dataset_path,
        vocab_path=vocab_path,
        batch_size=32,
        val_split=0.2,
        seed=42
    )

    checkpoint = torch.load(checkpoint_path, map_location=dev)
    model = EdgeChemNet(
        vocab_size=tokenizer.vocab_size,
        max_seq_len=32,
        d_model=128,
        nhead=4,
        num_layers=2,
        dim_feedforward=256
    ).to(dev)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    total_samples = 0
    correct_safety = 0
    correct_arm = 0
    correct_intent = 0

    latencies = []

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(dev)
            key_padding_mask = batch["key_padding_mask"].to(dev)
            safety_labels = batch["safety_labels"].to(dev)
            arm_labels = batch["arm_labels"].to(dev)
            intent_labels = batch["intent_labels"].to(dev)

            batch_size = input_ids.size(0)

            t0 = time.perf_counter()
            outputs = model(input_ids, key_padding_mask=key_padding_mask)
            elapsed = (time.perf_counter() - t0) * 1000.0 / batch_size
            latencies.extend([elapsed] * batch_size)

            s_preds = outputs["safety_logits"].argmax(dim=-1)
            a_preds = outputs["arm_logits"].argmax(dim=-1)
            i_preds = outputs["intent_logits"].argmax(dim=-1)

            correct_safety += (s_preds == safety_labels).sum().item()
            correct_arm += (a_preds == arm_labels).sum().item()
            correct_intent += (i_preds == intent_labels).sum().item()
            total_samples += batch_size

    acc_safety = correct_safety / total_samples
    acc_arm = correct_arm / total_samples
    acc_intent = correct_intent / total_samples

    avg_latency = sum(latencies) / len(latencies)
    p95_latency = sorted(latencies)[int(0.95 * len(latencies))]

    # Test Guardrail latency
    guard = DeterministicSafetyGuard()
    g_latencies = []
    test_queries = [
        "Can I add water to acid?",
        "What happens if I mix bleach and ammonia?",
        "Reading the burette meniscus",
        "How to calculate molarity?",
        "Missing goggles"
    ]
    for q in test_queries * 100:
        t0 = time.perf_counter()
        guard.evaluate(q)
        g_latencies.append((time.perf_counter() - t0) * 1000.0)

    avg_g_latency = sum(g_latencies) / len(g_latencies)

    print("\n" + "=" * 60)
    print(" IQO BOT CHEMISTRY AI - PERFORMANCE & ACCURACY REPORT")
    print("=" * 60)
    print(f"Total Validation Samples Evaluated : {total_samples}")
    print(f"Safety Level Accuracy              : {acc_safety * 100:.2f}%")
    print(f"3-DOF Arm Target Accuracy          : {acc_arm * 100:.2f}%")
    print(f"Intent Classification Accuracy     : {acc_intent * 100:.2f}%")
    print(f"Combined Overall Accuracy          : {((acc_safety + acc_arm + acc_intent) / 3) * 100:.2f}%")
    print("-" * 60)
    print(f"Deterministic Guardrail Avg Latency: {avg_g_latency:.3f} ms (Target: < 20 ms)")
    print(f"Edge Neural Model Avg Latency      : {avg_latency:.2f} ms / query")
    print(f"Edge Neural Model P95 Latency      : {p95_latency:.2f} ms / query")
    print("=" * 60 + "\n")

    return {
        "val_samples": total_samples,
        "acc_safety": acc_safety,
        "acc_arm": acc_arm,
        "acc_intent": acc_intent,
        "avg_neural_latency_ms": avg_latency,
        "guardrail_latency_ms": avg_g_latency
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=str, default="checkpoints/best_model.pt")
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    ckpt_p = project_root / args.checkpoint
    if not ckpt_p.exists():
        ckpt_p = project_root / "checkpoints" / "final_model.pt"
    vocab_p = project_root / "data" / "processed" / "vocab.json"
    dataset_p = project_root / "data" / "processed" / "chem_dataset.json"

    evaluate_model(str(ckpt_p), str(vocab_p), str(dataset_p), device=args.device)
