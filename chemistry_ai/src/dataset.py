"""
PyTorch Dataset and DataLoader for IQO Bot Chemistry AI
Prepares tokenized sequences and multi-task ground truth labels.
"""

import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import torch
from torch.utils.data import Dataset, DataLoader, random_split

from .tokenizer import ChemTokenizer


class ChemDataset(Dataset):
    """
    Multi-task dataset for Chemistry AI.
    Yields input token tensors along with safety, arm target, and intent targets.
    """
    def __init__(self, data: List[Dict], tokenizer: ChemTokenizer, max_length: int = 32):
        self.data = data
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        item = self.data[idx]
        query = item["query"]

        token_ids = self.tokenizer.encode(query, add_special_tokens=True)
        input_ids = torch.tensor(token_ids, dtype=torch.long)
        key_padding_mask = (input_ids == self.tokenizer.pad_id)

        safety_label = torch.tensor(item["safety_level"], dtype=torch.long)
        arm_label = torch.tensor(item["arm_target"], dtype=torch.long)
        intent_label = torch.tensor(item["intent"], dtype=torch.long)

        return {
            "input_ids": input_ids,
            "key_padding_mask": key_padding_mask,
            "safety_label": safety_label,
            "arm_label": arm_label,
            "intent_label": intent_label,
            "query": query,
            "speech_response": item.get("speech_response", ""),
            "lcd_display": item.get("lcd_display", ""),
            "led_color": item.get("led_color", "GREEN")
        }


def collate_chem_batch(batch: List[Dict]) -> Dict[str, torch.Tensor]:
    """
    Custom collator stacking tensors while preserving text annotations.
    """
    input_ids = torch.stack([item["input_ids"] for item in batch], dim=0)
    key_padding_mask = torch.stack([item["key_padding_mask"] for item in batch], dim=0)
    safety_labels = torch.stack([item["safety_label"] for item in batch], dim=0)
    arm_labels = torch.stack([item["arm_label"] for item in batch], dim=0)
    intent_labels = torch.stack([item["intent_label"] for item in batch], dim=0)

    queries = [item["query"] for item in batch]
    speech_responses = [item["speech_response"] for item in batch]
    lcd_displays = [item["lcd_display"] for item in batch]
    led_colors = [item["led_color"] for item in batch]

    return {
        "input_ids": input_ids,
        "key_padding_mask": key_padding_mask,
        "safety_labels": safety_labels,
        "arm_labels": arm_labels,
        "intent_labels": intent_labels,
        "queries": queries,
        "speech_responses": speech_responses,
        "lcd_displays": lcd_displays,
        "led_colors": led_colors
    }


def get_dataloaders(
    dataset_path: str,
    vocab_path: str,
    batch_size: int = 32,
    val_split: float = 0.2,
    seed: int = 42,
    max_length: int = 32
) -> Tuple[DataLoader, DataLoader, ChemTokenizer]:
    """
    Loads dataset, creates train/val splits and returns PyTorch DataLoaders.
    """
    with open(dataset_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    tokenizer = ChemTokenizer.load_vocab(vocab_path, max_length=max_length)
    full_dataset = ChemDataset(raw_data, tokenizer=tokenizer, max_length=max_length)

    total_len = len(full_dataset)
    val_len = int(total_len * val_split)
    train_len = total_len - val_len

    generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds = random_split(full_dataset, [train_len, val_len], generator=generator)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_chem_batch,
        drop_last=False
    )

    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_chem_batch,
        drop_last=False
    )

    return train_loader, val_loader, tokenizer
