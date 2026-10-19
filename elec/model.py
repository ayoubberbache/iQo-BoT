"""EdgeChemNet: ~325k-param char-level Transformer encoder with 4 heads.
Plain nn.Linear everywhere (no nn.MultiheadAttention) so dynamic INT8
quantization and ONNX/C export cover every weight matrix."""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from config import VOCAB_SIZE, MAX_LEN, SAFETY, ARM_CLASSES, INTENTS
from topics import TOPIC_IDS


class Block(nn.Module):
    def __init__(self, d, h, ff, p):
        super().__init__()
        self.h = h
        self.n1, self.n2 = nn.LayerNorm(d), nn.LayerNorm(d)
        self.qkv, self.o = nn.Linear(d, 3 * d), nn.Linear(d, d)
        self.f1, self.f2 = nn.Linear(d, ff), nn.Linear(ff, d)
        self.drop = nn.Dropout(p)

    def forward(self, x, keep):                      # keep: (B,T) bool
        B, T, D = x.shape
        q, k, v = self.qkv(self.n1(x)).view(B, T, 3, self.h, D // self.h).permute(2, 0, 3, 1, 4)
        att = (q @ k.transpose(-1, -2)) / math.sqrt(D // self.h)
        att = att.masked_fill(~keep[:, None, None, :], -1e4).softmax(-1)
        x = x + self.drop(self.o((att @ v).transpose(1, 2).reshape(B, T, D)))
        return x + self.drop(self.f2(F.relu(self.f1(self.n2(x)))))


class EdgeChemNet(nn.Module):
    def __init__(self, d=128, layers=2, heads=4, ff=288, emb=128, p=0.1):
        super().__init__()
        self.tok = nn.Embedding(VOCAB_SIZE, d, padding_idx=0)
        self.pos = nn.Embedding(MAX_LEN, d)
        self.blocks = nn.ModuleList(Block(d, heads, ff, p) for _ in range(layers))
        self.norm = nn.LayerNorm(d)
        self.h_safety = nn.Linear(d, len(SAFETY))
        self.h_arm = nn.Linear(d, len(ARM_CLASSES))
        self.h_intent = nn.Linear(d, len(INTENTS))
        self.h_emb = nn.Linear(d, emb)
        self.protos = nn.Parameter(torch.randn(len(TOPIC_IDS), emb) * 0.1)  # topic prototypes
        self.scale = 16.0

    def forward(self, ids):                           # ids: (B, MAX_LEN) int64, 0 = pad
        keep = ids != 0
        x = self.tok(ids) + self.pos.weight[: ids.shape[1]]
        for b in self.blocks:
            x = b(x, keep)
        m = keep.unsqueeze(-1).to(x.dtype)
        pooled = self.norm((x * m).sum(1) / m.sum(1).clamp(min=1.0))
        emb = F.normalize(self.h_emb(pooled), dim=-1)
        topic = self.scale * emb @ F.normalize(self.protos, dim=-1).t()
        return self.h_safety(pooled), self.h_arm(pooled), self.h_intent(pooled), emb, topic


def n_params(m):
    return sum(p.numel() for p in m.parameters())


if __name__ == "__main__":
    print(n_params(EdgeChemNet()), "parameters")
