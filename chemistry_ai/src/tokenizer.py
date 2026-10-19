"""
Edge-Compatible Tokenizer for IQO Bot Chemistry AI
Supports fast string tokenization, padding, truncation, and vocabulary serialization.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Union


class ChemTokenizer:
    """
    Lightweight, self-contained tokenizer designed for embedded chips and microcontrollers.
    Zero external dependencies, fast O(N) execution.
    """

    PAD_TOKEN = "<PAD>"
    UNK_TOKEN = "<UNK>"
    SOS_TOKEN = "<SOS>"
    EOS_TOKEN = "<EOS>"

    def __init__(self, vocab: Dict[str, int] = None, max_length: int = 32):
        self.max_length = max_length
        if vocab is not None:
            self.vocab = vocab
        else:
            self.vocab = {
                self.PAD_TOKEN: 0,
                self.UNK_TOKEN: 1,
                self.SOS_TOKEN: 2,
                self.EOS_TOKEN: 3
            }
        self.inv_vocab = {v: k for k, v in self.vocab.items()}

    @property
    def pad_id(self) -> int:
        return self.vocab[self.PAD_TOKEN]

    @property
    def unk_id(self) -> int:
        return self.vocab[self.UNK_TOKEN]

    @property
    def sos_id(self) -> int:
        return self.vocab[self.SOS_TOKEN]

    @property
    def eos_id(self) -> int:
        return self.vocab[self.EOS_TOKEN]

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    @classmethod
    def load_vocab(cls, vocab_path: Union[str, Path], max_length: int = 32) -> "ChemTokenizer":
        with open(vocab_path, "r", encoding="utf-8") as f:
            vocab = json.load(f)
        return cls(vocab=vocab, max_length=max_length)

    @classmethod
    def build_vocab_from_texts(cls, texts: List[str], max_length: int = 32) -> "ChemTokenizer":
        tokenizer = cls(max_length=max_length)
        vocab = {
            cls.PAD_TOKEN: 0,
            cls.UNK_TOKEN: 1,
            cls.SOS_TOKEN: 2,
            cls.EOS_TOKEN: 3
        }
        for t in texts:
            tokens = tokenizer.tokenize(t)
            for tok in tokens:
                if tok not in vocab:
                    vocab[tok] = len(vocab)
        return cls(vocab=vocab, max_length=max_length)

    def save_vocab(self, vocab_path: Union[str, Path]) -> None:
        with open(vocab_path, "w", encoding="utf-8") as f:
            json.dump(self.vocab, f, indent=2, ensure_ascii=False)

    def clean_text(self, text: str) -> str:
        text = text.lower().strip()
        # Keep chemical formulas and words intact, normalize punctuation
        text = re.sub(r"[?,!;:\"'()\[\]{}]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def tokenize(self, text: str) -> List[str]:
        cleaned = self.clean_text(text)
        return cleaned.split() if cleaned else []

    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        tokens = self.tokenize(text)
        token_ids = []
        if add_special_tokens:
            token_ids.append(self.sos_id)

        for t in tokens:
            token_ids.append(self.vocab.get(t, self.unk_id))

        if add_special_tokens:
            token_ids.append(self.eos_id)

        # Truncate or Pad to max_length
        if len(token_ids) > self.max_length:
            token_ids = token_ids[:self.max_length]
            if add_special_tokens:
                token_ids[-1] = self.eos_id
        else:
            token_ids = token_ids + [self.pad_id] * (self.max_length - len(token_ids))

        return token_ids

    def decode(self, token_ids: List[int], skip_special_tokens: bool = True) -> str:
        words = []
        for tid in token_ids:
            word = self.inv_vocab.get(tid, self.UNK_TOKEN)
            if skip_special_tokens and word in (self.PAD_TOKEN, self.SOS_TOKEN, self.EOS_TOKEN):
                continue
            words.append(word)
        return " ".join(words)
