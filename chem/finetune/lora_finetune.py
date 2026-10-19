"""LoRA fine-tune Llama 3.x on finetune/sft.jsonl (needs an NVIDIA GPU, >=16 GB; or --4bit for ~8 GB).
  pip install transformers peft accelerate bitsandbytes
  python finetune/lora_finetune.py --base meta-llama/Llama-3.1-8B-Instruct --out llm/adapter
The base model is gated on Hugging Face (accept Meta's licence, `huggingface-cli login`).
Use the SAME base for Ollama (FROM llama3.1:8b) so the adapter matches."""
import argparse, json, torch
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--data", default="finetune/sft.jsonl")
ap.add_argument("--out", default="llm/adapter")
ap.add_argument("--epochs", type=float, default=2)
ap.add_argument("--max-len", type=int, default=1024)
ap.add_argument("--4bit", dest="q4", action="store_true")
a = ap.parse_args()

tok = AutoTokenizer.from_pretrained(a.base)
tok.pad_token = tok.pad_token or tok.eos_token


class SFT(Dataset):
    def __init__(self):
        self.rows = []
        for line in open(a.data):
            m = json.loads(line)["messages"]
            p = tok(tok.apply_chat_template(m[:-1], tokenize=False, add_generation_prompt=True),
                    add_special_tokens=False).input_ids
            f = tok(tok.apply_chat_template(m, tokenize=False), add_special_tokens=False).input_ids[: a.max_len]
            self.rows.append((f, [-100] * min(len(p), len(f)) + f[len(p):]))
    def __len__(self): return len(self.rows)
    def __getitem__(self, i): return self.rows[i]


def collate(batch):
    L = max(len(x[0]) for x in batch)
    ids = torch.tensor([x[0] + [tok.pad_token_id] * (L - len(x[0])) for x in batch])
    lab = torch.tensor([x[1] + [-100] * (L - len(x[1])) for x in batch])
    return {"input_ids": ids, "labels": lab, "attention_mask": (ids != tok.pad_token_id) | (lab != -100)}


kw = {"torch_dtype": torch.bfloat16, "device_map": "auto"}
if a.q4:
    from transformers import BitsAndBytesConfig
    kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                   bnb_4bit_compute_dtype=torch.bfloat16)
model = AutoModelForCausalLM.from_pretrained(a.base, **kw)
model = prepare_model_for_kbit_training(model) if a.q4 else model
model.enable_input_require_grads()
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]))
model.print_trainable_parameters()
Trainer(model=model, train_dataset=SFT(), data_collator=collate,
        args=TrainingArguments(output_dir="/tmp/lora_run", per_device_train_batch_size=2,
                               gradient_accumulation_steps=8, num_train_epochs=a.epochs, learning_rate=2e-4,
                               lr_scheduler_type="cosine", warmup_ratio=0.03, bf16=True, logging_steps=20,
                               gradient_checkpointing=True, save_strategy="no", report_to="none")).train()
model.save_pretrained(a.out)
tok.save_pretrained(a.out)
print("adapter saved to", a.out)
