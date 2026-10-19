"""
Edge Chip Exporter for IQO Bot Chemistry AI
Exports EdgeChemNet to ONNX, TorchScript, Dynamic INT8 Quantization, and C/C++ Header.
Prepares the model for edge hardware (Raspberry Pi 4, ESP32-S3, Edge Accelerators).
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import torch
import torch.nn as nn

try:
    import onnx
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

from .model import EdgeChemNet
from .tokenizer import ChemTokenizer


def export_model_to_all_formats(
    checkpoint_path: str,
    vocab_path: str,
    output_dir: str,
    max_seq_len: int = 32,
    d_model: Optional[int] = None,
    nhead: Optional[int] = None,
    num_layers: Optional[int] = None,
    dim_feedforward: Optional[int] = None
) -> Dict[str, str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tokenizer = ChemTokenizer.load_vocab(vocab_path, max_length=max_seq_len)
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    cfg = checkpoint.get("config", {})

    d_model = d_model or cfg.get("d_model", 128)
    nhead = nhead or cfg.get("nhead", 4)
    num_layers = num_layers or cfg.get("num_layers", 2)
    dim_feedforward = dim_feedforward or cfg.get("dim_feedforward", 256)
    max_seq_len = cfg.get("max_seq_len", max_seq_len)

    model = EdgeChemNet(
        vocab_size=tokenizer.vocab_size,
        max_seq_len=max_seq_len,
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers,
        dim_feedforward=dim_feedforward
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    exported_files = {}

    # Dummy input for tracing [batch_size=1, max_seq_len]
    dummy_input = torch.randint(0, tokenizer.vocab_size, (1, max_seq_len), dtype=torch.long)

    # 1. Export to TorchScript (for Raspberry Pi 4 / Embedded Linux / C++ LibTorch)
    ts_path = output_path / "edge_chem_net.pt"
    try:
        traced_model = torch.jit.trace(model, (dummy_input,), strict=False, check_trace=False)
        traced_model.save(str(ts_path))
        exported_files["torchscript"] = str(ts_path)
        print(f"[Export] Saved TorchScript model: {ts_path} ({ts_path.stat().st_size / 1024:.1f} KB)")
    except Exception as e:
        print(f"[Export Warning] TorchScript trace failed: {e}")

    # 2. Export to ONNX (for ONNX Runtime / OpenVINO / TensorRT / Edge TPU)
    onnx_path = output_path / "edge_chem_net.onnx"
    try:
        torch.onnx.export(
            model,
            (dummy_input,),
            str(onnx_path),
            export_params=True,
            opset_version=17,
            dynamo=False,
            do_constant_folding=True,
            input_names=["input_ids"],
            output_names=["safety_logits", "arm_logits", "intent_logits", "embeddings"],
            dynamic_axes={
                "input_ids": {0: "batch_size"},
                "safety_logits": {0: "batch_size"},
                "arm_logits": {0: "batch_size"},
                "intent_logits": {0: "batch_size"},
                "embeddings": {0: "batch_size"}
            }
        )
        if HAS_ONNX:
            model_proto = onnx.load(str(onnx_path))
            onnx.checker.check_model(model_proto)
            print(f"[Export] Verified ONNX model integrity: {onnx_path} ({onnx_path.stat().st_size / 1024:.1f} KB)")
        else:
            print(f"[Export] Saved ONNX model: {onnx_path} ({onnx_path.stat().st_size / 1024:.1f} KB)")
        exported_files["onnx"] = str(onnx_path)
    except Exception as e:
        print(f"[Export Warning] ONNX export failed: {e}")

    # 3. Dynamic INT8 Quantization (4x memory reduction for edge chips)
    quant_path = output_path / "edge_chem_net_quantized.pt"
    try:
        quantized_model = torch.quantization.quantize_dynamic(
            model,
            {nn.Linear},
            dtype=torch.qint8
        )
        torch.save(quantized_model.state_dict(), str(quant_path))
        exported_files["quantized_int8"] = str(quant_path)
        print(f"[Export] Saved INT8 Quantized model: {quant_path} ({quant_path.stat().st_size / 1024:.1f} KB)")
    except Exception as e:
        print(f"[Export Warning] INT8 Quantization failed: {e}")

    # 4. Generate C/C++ Header for Embedded Microcontrollers (ESP32-S3)
    header_path = output_path / "iqo_chem_embedded_config.h"
    with open(header_path, "w", encoding="utf-8") as f:
        f.write("/* IQO Bot Chemistry AI - Embedded Configuration Header */\n")
        f.write("#ifndef IQO_CHEM_EMBEDDED_CONFIG_H\n")
        f.write("#define IQO_CHEM_EMBEDDED_CONFIG_H\n\n")
        f.write(f"#define IQO_CHEM_VOCAB_SIZE {tokenizer.vocab_size}\n")
        f.write(f"#define IQO_CHEM_MAX_SEQ_LEN {max_seq_len}\n")
        f.write(f"#define IQO_CHEM_D_MODEL 128\n")
        f.write(f"#define IQO_CHEM_NUM_SAFETY_CLASSES 4\n")
        f.write(f"#define IQO_CHEM_NUM_ARM_TARGETS 8\n")
        f.write(f"#define IQO_CHEM_NUM_INTENTS 8\n\n")
        f.write("// Safety Levels: 0=SAFE, 1=INFO, 2=WARNING, 3=CRITICAL\n")
        f.write("// Arm Targets: 0=NONE, 1=GOGGLE_RACK, 2=EYEWASH, 3=FUME_HOOD, 4=WASTE, 5=BURETTE, 6=SHELF, 7=BENCH\n\n")
        f.write("#endif // IQO_CHEM_EMBEDDED_CONFIG_H\n")
    exported_files["embedded_header"] = str(header_path)

    # 5. Metadata JSON
    metadata = {
        "model_name": "EdgeChemNet",
        "vocab_size": tokenizer.vocab_size,
        "max_seq_len": max_seq_len,
        "d_model": 128,
        "parameter_count": model.count_parameters(),
        "exported_files": exported_files,
        "class_mappings": {
            "safety": ["SAFE", "INFO", "WARNING", "CRITICAL"],
            "arm_target": ["NONE", "GOGGLE_RACK", "EYEWASH_STATION", "FUME_HOOD", "CHEMICAL_WASTE", "BURETTE_STAND", "REAGENT_SHELF", "BENCH_WORKSTATION"],
            "intent": ["TITRATION_GUIDANCE", "REAGENT_COMPATIBILITY", "SAFETY_EMERGENCY", "PPE_VIOLATION", "CALCULATION_STOICHIOMETRY", "MSDS_INQUIRY", "WASTE_DISPOSAL", "GENERAL_LAB_PROCEDURE"]
        }
    }
    meta_path = output_path / "model_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    exported_files["metadata"] = str(meta_path)

    print(f"[Export Complete] All edge artifacts generated in: {output_path.resolve()}")
    return exported_files


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    ckpt = project_root / "checkpoints" / "best_model.pt"
    if not ckpt.exists():
        ckpt = project_root / "checkpoints" / "final_model.pt"
    vocab = project_root / "data" / "processed" / "vocab.json"
    out_d = project_root / "exports"

    if ckpt.exists():
        export_model_to_all_formats(str(ckpt), str(vocab), str(out_d))
    else:
        print(f"Checkpoint not found at {ckpt}. Please run training first.")
