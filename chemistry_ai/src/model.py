"""
EdgeChemNet: Edge-Optimized Multi-Task Neural Network for IQO Bot Chemistry AI
Designed specifically for edge MCU / RPi 4 / embedded chip deployment.
Exportable to ONNX, TorchScript, and INT8 Quantization.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple


class TransformerEncoderBlock(nn.Module):
    """
    Standard Transformer Encoder block optimized for edge export.
    Uses LayerNorm and MultiheadAttention with clean residual connections.
    """
    def __init__(self, d_model: int = 128, nhead: int = 4, dim_feedforward: int = 256, dropout: float = 0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, nhead, dropout=dropout, batch_first=True)
        self.linear1 = nn.Linear(d_model, dim_feedforward)
        self.dropout = nn.Dropout(dropout)
        self.linear2 = nn.Linear(dim_feedforward, d_model)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, key_padding_mask: torch.Tensor = None) -> torch.Tensor:
        attn_out, _ = self.self_attn(x, x, x, key_padding_mask=key_padding_mask)
        x = self.norm1(x + self.dropout1(attn_out))
        ff_out = self.linear2(self.dropout(F.relu(self.linear1(x))))
        x = self.norm2(x + self.dropout2(ff_out))
        return x


class EdgeChemNet(nn.Module):
    """
    Multi-task laboratory assistant neural network.
    Predicts:
      1. Safety Risk Level (4 classes)
      2. 3-DOF Pointer Arm Target (8 classes)
      3. Intent Classification (8 classes)
      4. Dense Representation Vector (for response retrieval / verification)
    """
    def __init__(
        self,
        vocab_size: int = 512,
        max_seq_len: int = 32,
        d_model: int = 128,
        nhead: int = 4,
        num_layers: int = 2,
        dim_feedforward: int = 256,
        num_safety_classes: int = 4,
        num_arm_classes: int = 8,
        num_intent_classes: int = 8,
        dropout: float = 0.1
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.d_model = d_model

        # Token and positional embeddings
        self.token_embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        self.pos_embedding = nn.Embedding(max_seq_len, d_model)
        self.emb_dropout = nn.Dropout(dropout)

        # Transformer encoder stack
        self.layers = nn.ModuleList([
            TransformerEncoderBlock(d_model, nhead, dim_feedforward, dropout)
            for _ in range(num_layers)
        ])

        self.final_norm = nn.LayerNorm(d_model)

        # Multi-task classification heads
        self.safety_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_safety_classes)
        )

        self.arm_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_arm_classes)
        )

        self.intent_head = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, num_intent_classes)
        )

        self.proj_head = nn.Linear(d_model, 64)

    def forward(
        self,
        input_ids: torch.Tensor,
        key_padding_mask: torch.Tensor = None
    ) -> Dict[str, torch.Tensor]:
        """
        Args:
            input_ids: Tensor of token IDs with shape [batch_size, seq_len]
            key_padding_mask: Optional bool tensor [batch_size, seq_len] where True indicates padding
        Returns:
            Dictionary with 'safety_logits', 'arm_logits', 'intent_logits', 'embeddings'
        """
        batch_size, seq_len = input_ids.shape
        device = input_ids.device

        # Create positional indices [0, 1, ..., seq_len-1]
        positions = torch.arange(seq_len, device=device).unsqueeze(0).expand(batch_size, seq_len)

        x = self.token_embedding(input_ids) + self.pos_embedding(positions)
        x = self.emb_dropout(x)

        for layer in self.layers:
            x = layer(x, key_padding_mask=key_padding_mask)

        x = self.final_norm(x)

        # Mask-aware average pooling across sequence dimension
        if key_padding_mask is not None:
            # key_padding_mask is True for padding tokens
            mask = (~key_padding_mask).unsqueeze(-1).float()
            pooled = (x * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
        else:
            pooled = x.mean(dim=1)

        safety_logits = self.safety_head(pooled)
        arm_logits = self.arm_head(pooled)
        intent_logits = self.intent_head(pooled)
        embeddings = F.normalize(self.proj_head(pooled), p=2, dim=-1)

        return {
            "safety_logits": safety_logits,
            "arm_logits": arm_logits,
            "intent_logits": intent_logits,
            "embeddings": embeddings
        }

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
