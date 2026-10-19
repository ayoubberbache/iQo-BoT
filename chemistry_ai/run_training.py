"""
Main Training & Edge Export Entrypoint for IQO Bot Chemistry AI
Coordinates training, validation, benchmarking, and chip-ready model export.
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR.parent))

import torch
from chemistry_ai.src.train import train_edge_chem_net
from chemistry_ai.src.evaluate import evaluate_model
from chemistry_ai.src.export_to_chip import export_model_to_all_formats


def main():
    parser = argparse.ArgumentParser(description="IQO Bot Chemistry AI Training & Export Engine")
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size for training")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu", help="Compute device")
    parser.add_argument("--skip-export", action="store_true", help="Skip exporting to chip formats")
    parser.add_argument("--no-online-stream", action="store_true", help="Disable streaming from trusted online APIs (PubChem)")
    args = parser.parse_args()

    project_dir = SCRIPT_DIR
    dataset_path = project_dir / "data" / "processed" / "chem_dataset.json"
    vocab_path = project_dir / "data" / "processed" / "vocab.json"
    checkpoint_dir = project_dir / "checkpoints"
    export_dir = project_dir / "exports"

    print("=" * 75)
    print(" IQO BOT - EMBEDDED CHEMISTRY AI TRAINING & EXPORT RUNNER")
    print("=" * 75)
    print(f"Device: {args.device} | Epochs: {args.epochs} | Batch Size: {args.batch_size}")
    print(f"Online Trusted Streaming: {'Enabled (NIH PubChem in-memory)' if not args.no_online_stream else 'Disabled'}")
    print(f"Dataset: {dataset_path}")
    print(f"Checkpoints: {checkpoint_dir}")
    print(f"Exports: {export_dir}")
    print("=" * 75)

    # 1. Train Model
    model, history = train_edge_chem_net(
        dataset_path=str(dataset_path),
        vocab_path=str(vocab_path),
        checkpoint_dir=str(checkpoint_dir),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
        use_online_stream=not args.no_online_stream
    )

    # 2. Evaluate Model
    best_ckpt = checkpoint_dir / "best_model.pt"
    if not best_ckpt.exists():
        best_ckpt = checkpoint_dir / "final_model.pt"

    eval_results = evaluate_model(
        checkpoint_path=str(best_ckpt),
        vocab_path=str(vocab_path),
        dataset_path=str(dataset_path),
        device=args.device
    )

    # 3. Export to Chip Formats
    if not args.skip_export:
        print("\n" + "=" * 75)
        print(" EXPORTING MODEL FOR EDGE CHIP DEPLOYMENT (RPi 4 / ESP32-S3 / NPU)")
        print("=" * 75)
        export_model_to_all_formats(
            checkpoint_path=str(best_ckpt),
            vocab_path=str(vocab_path),
            output_dir=str(export_dir)
        )

    print("\n" + "=" * 75)
    print(" SUCCESS: Training, evaluation, and edge export completed 100%!")
    print("=" * 75)


if __name__ == "__main__":
    main()
