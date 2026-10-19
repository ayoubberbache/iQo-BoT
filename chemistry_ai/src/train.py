"""
Training Pipeline for IQO Bot Chemistry AI (EdgeChemNet)
Supports multi-task loss, validation metrics, early stopping, and checkpointing.
"""

import os
import json
import time
import argparse
from pathlib import Path
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR

from .model import EdgeChemNet
from .dataset import get_dataloaders


def train_one_epoch(
    model: nn.Module,
    train_loader,
    optimizer,
    scheduler,
    criterion,
    device,
    weights=(1.0, 1.0, 1.0)
):
    model.train()
    total_loss = 0.0
    correct_safety = 0
    correct_arm = 0
    correct_intent = 0
    total_samples = 0

    w_safety, w_arm, w_intent = weights

    for batch in train_loader:
        input_ids = batch["input_ids"].to(device)
        key_padding_mask = batch["key_padding_mask"].to(device)
        safety_labels = batch["safety_labels"].to(device)
        arm_labels = batch["arm_labels"].to(device)
        intent_labels = batch["intent_labels"].to(device)

        batch_size = input_ids.size(0)
        optimizer.zero_grad()

        outputs = model(input_ids, key_padding_mask=key_padding_mask)

        loss_s = criterion(outputs["safety_logits"], safety_labels)
        loss_a = criterion(outputs["arm_logits"], arm_labels)
        loss_i = criterion(outputs["intent_logits"], intent_labels)

        loss = w_safety * loss_s + w_arm * loss_a + w_intent * loss_i
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item() * batch_size
        correct_safety += (outputs["safety_logits"].argmax(dim=-1) == safety_labels).sum().item()
        correct_arm += (outputs["arm_logits"].argmax(dim=-1) == arm_labels).sum().item()
        correct_intent += (outputs["intent_logits"].argmax(dim=-1) == intent_labels).sum().item()
        total_samples += batch_size

    scheduler.step()

    return {
        "loss": total_loss / total_samples,
        "acc_safety": correct_safety / total_samples,
        "acc_arm": correct_arm / total_samples,
        "acc_intent": correct_intent / total_samples
    }


def validate(model: nn.Module, val_loader, criterion, device, weights=(1.0, 1.0, 1.0)):
    model.eval()
    total_loss = 0.0
    correct_safety = 0
    correct_arm = 0
    correct_intent = 0
    total_samples = 0

    w_safety, w_arm, w_intent = weights

    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch["input_ids"].to(device)
            key_padding_mask = batch["key_padding_mask"].to(device)
            safety_labels = batch["safety_labels"].to(device)
            arm_labels = batch["arm_labels"].to(device)
            intent_labels = batch["intent_labels"].to(device)

            batch_size = input_ids.size(0)

            outputs = model(input_ids, key_padding_mask=key_padding_mask)

            loss_s = criterion(outputs["safety_logits"], safety_labels)
            loss_a = criterion(outputs["arm_logits"], arm_labels)
            loss_i = criterion(outputs["intent_logits"], intent_labels)

            loss = w_safety * loss_s + w_arm * loss_a + w_intent * loss_i

            total_loss += loss.item() * batch_size
            correct_safety += (outputs["safety_logits"].argmax(dim=-1) == safety_labels).sum().item()
            correct_arm += (outputs["arm_logits"].argmax(dim=-1) == arm_labels).sum().item()
            correct_intent += (outputs["intent_logits"].argmax(dim=-1) == intent_labels).sum().item()
            total_samples += batch_size

    return {
        "loss": total_loss / total_samples,
        "acc_safety": correct_safety / total_samples,
        "acc_arm": correct_arm / total_samples,
        "acc_intent": correct_intent / total_samples
    }


from torch.utils.data import DataLoader, ConcatDataset
from .model import EdgeChemNet
from .dataset import get_dataloaders, collate_chem_batch
from .online_dataset import OnlineStreamingChemDataset


def train_edge_chem_net(
    dataset_path: str,
    vocab_path: str,
    checkpoint_dir: str,
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-3,
    device: str = "cpu",
    use_online_stream: bool = True
):
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    dev = torch.device(device)
    print(f"[Training] Using compute device: {dev}")

    train_loader, val_loader, tokenizer = get_dataloaders(
        dataset_path=dataset_path,
        vocab_path=vocab_path,
        batch_size=batch_size,
        val_split=0.2,
        seed=42
    )

    if use_online_stream:
        print("[Online Trusted Datasets] Streaming live chemical safety data from NIH PubChem in-memory (no bulk disk download)...")
        online_ds = OnlineStreamingChemDataset(tokenizer=tokenizer, max_length=32, max_online_samples=60)
        print(f"[Online Trusted Datasets] Successfully streamed {len(online_ds)} records into memory buffer.")
        train_loader = DataLoader(
            ConcatDataset([train_loader.dataset, online_ds]),
            batch_size=batch_size,
            shuffle=True,
            collate_fn=collate_chem_batch
        )

    print(f"[Dataset] Train batches: {len(train_loader)}, Val batches: {len(val_loader)}")
    print(f"[Vocab] Size: {tokenizer.vocab_size}")

    model = EdgeChemNet(
        vocab_size=tokenizer.vocab_size,
        max_seq_len=32,
        d_model=128,
        nhead=4,
        num_layers=2,
        dim_feedforward=256,
        dropout=0.1
    ).to(dev)

    param_count = model.count_parameters()
    print(f"[Model] Initialized EdgeChemNet with {param_count:,} trainable parameters.")

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    best_val_loss = float("inf")
    best_acc = 0.0
    history = []

    print("-" * 75)
    print(f"{'Epoch':<6}{'Tr Loss':<10}{'Val Loss':<10}{'Safety Acc':<12}{'Arm Acc':<12}{'Intent Acc':<12}{'LR':<10}")
    print("-" * 75)

    for epoch in range(1, epochs + 1):
        t0 = time.time()
        train_metrics = train_one_epoch(model, train_loader, optimizer, scheduler, criterion, dev)
        val_metrics = validate(model, val_loader, criterion, dev)
        elapsed = time.time() - t0

        avg_acc = (val_metrics["acc_safety"] + val_metrics["acc_arm"] + val_metrics["acc_intent"]) / 3.0
        current_lr = scheduler.get_last_lr()[0]

        print(
            f"{epoch:<6}{train_metrics['loss']:<10.4f}{val_metrics['loss']:<10.4f}"
            f"{val_metrics['acc_safety']*100:<11.1f}%{val_metrics['acc_arm']*100:<11.1f}%"
            f"{val_metrics['acc_intent']*100:<11.1f}%{current_lr:<10.6f}"
        )

        history.append({
            "epoch": epoch,
            "train": train_metrics,
            "val": val_metrics,
            "lr": current_lr,
            "time_sec": elapsed
        })

        # Save checkpoint if best combined metric
        if val_metrics["loss"] < best_val_loss or avg_acc > best_acc:
            best_val_loss = min(best_val_loss, val_metrics["loss"])
            best_acc = max(best_acc, avg_acc)
            save_path = checkpoint_dir / "best_model.pt"
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_metrics["loss"],
                "avg_acc": avg_acc,
                "vocab_size": tokenizer.vocab_size,
                "config": {
                    "d_model": 128,
                    "nhead": 4,
                    "num_layers": 2,
                    "dim_feedforward": 256,
                    "max_seq_len": 32
                }
            }, save_path)

    # Save final model & history
    torch.save({
        "epoch": epochs,
        "model_state_dict": model.state_dict(),
        "vocab_size": tokenizer.vocab_size,
        "config": {
            "d_model": 128,
            "nhead": 4,
            "num_layers": 2,
            "dim_feedforward": 256,
            "max_seq_len": 32
        }
    }, checkpoint_dir / "final_model.pt")

    with open(checkpoint_dir / "training_history.json", "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

    print("-" * 75)
    print(f"[Complete] Best validation combined accuracy: {best_acc*100:.2f}%")
    print(f"[Artifacts] Checkpoints saved to: {checkpoint_dir.resolve()}")
    return model, history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EdgeChemNet for IQO Bot")
    parser.add_argument("--epochs", type=int, default=25, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    dataset_p = project_root / "data" / "processed" / "chem_dataset.json"
    vocab_p = project_root / "data" / "processed" / "vocab.json"
    checkpoint_p = project_root / "checkpoints"

    train_edge_chem_net(
        dataset_path=str(dataset_p),
        vocab_path=str(vocab_p),
        checkpoint_dir=str(checkpoint_p),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device
    )
