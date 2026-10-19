"""
Full Multimodal Inference Pipeline for IQO Bot Chemistry AI
Integrates Deterministic Zero-Tolerance Guardrail and EdgeChemNet Neural Model.
"""

import time
import torch
from pathlib import Path
from typing import Dict, Any, Optional

from .guardrail import DeterministicSafetyGuard
from .model import EdgeChemNet
from .tokenizer import ChemTokenizer

SAFETY_LABELS = {0: "SAFE", 1: "INFO", 2: "WARNING", 3: "CRITICAL"}
ARM_LABELS = {
    0: "NONE",
    1: "GOGGLE_RACK",
    2: "EYEWASH_STATION",
    3: "FUME_HOOD",
    4: "CHEMICAL_WASTE",
    5: "BURETTE_STAND",
    6: "REAGENT_SHELF",
    7: "BENCH_WORKSTATION"
}
INTENT_LABELS = {
    0: "TITRATION_GUIDANCE",
    1: "REAGENT_COMPATIBILITY",
    2: "SAFETY_EMERGENCY",
    3: "PPE_VIOLATION",
    4: "CALCULATION_STOICHIOMETRY",
    5: "MSDS_INQUIRY",
    6: "WASTE_DISPOSAL",
    7: "GENERAL_LAB_PROCEDURE"
}


class ChemistryAIPipeline:
    """
    Unified Chemistry Assistant Pipeline.
    Evaluates safety via deterministic guardrail first, then runs neural model inference.
    """
    def __init__(
        self,
        model: Optional[EdgeChemNet] = None,
        tokenizer: Optional[ChemTokenizer] = None,
        device: str = "cpu"
    ):
        self.device = torch.device(device)
        self.guardrail = DeterministicSafetyGuard()
        self.model = model
        if self.model is not None:
            self.model.to(self.device)
            self.model.eval()
        self.tokenizer = tokenizer

    @classmethod
    def load_from_checkpoint(
        cls,
        checkpoint_path: str,
        vocab_path: str,
        device: str = "cpu"
    ) -> "ChemistryAIPipeline":
        tokenizer = ChemTokenizer.load_vocab(vocab_path)
        checkpoint = torch.load(checkpoint_path, map_location=device)

        model = EdgeChemNet(
            vocab_size=tokenizer.vocab_size,
            max_seq_len=32,
            d_model=128,
            nhead=4,
            num_layers=2,
            dim_feedforward=256
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        return cls(model=model, tokenizer=tokenizer, device=device)

    def process(
        self,
        query: str,
        visual_missing_goggles: bool = False
    ) -> Dict[str, Any]:
        """
        Executes end-to-end evaluation for student query and vision telemetry.
        """
        t0 = time.perf_counter()

        # Step 1: Sub-20ms Deterministic Guardrail Check
        guard_result = self.guardrail.evaluate(query, visual_missing_goggles=visual_missing_goggles)
        if guard_result is not None:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            guard_intent = guard_result.get("intent", 2 if guard_result["safety_level"] == 3 else 3)
            return {
                "query": query,
                "safety_level": guard_result["safety_level"],
                "safety_label": SAFETY_LABELS[guard_result["safety_level"]],
                "arm_target": guard_result["arm_target"],
                "arm_label": ARM_LABELS[guard_result["arm_target"]],
                "intent": guard_intent,
                "intent_label": INTENT_LABELS.get(guard_intent, "GENERAL_LAB_PROCEDURE"),
                "led_color": guard_result["led_color"],
                "speech_response": guard_result["speech_response"],
                "lcd_display": guard_result["lcd_display"],
                "latency_ms": round(latency_ms, 2),
                "pipeline_stage": "DETERMINISTIC_SAFETY_OVERRIDE"
            }

        # Step 2: EdgeChemNet Neural Model Inference
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("Neural model or tokenizer not initialized in pipeline.")

        token_ids = self.tokenizer.encode(query, add_special_tokens=True)
        input_tensor = torch.tensor([token_ids], dtype=torch.long, device=self.device)
        key_padding_mask = (input_tensor == self.tokenizer.pad_id)

        with torch.no_grad():
            outputs = self.model(input_tensor, key_padding_mask=key_padding_mask)

        safety_pred = outputs["safety_logits"].argmax(dim=-1).item()
        arm_pred = outputs["arm_logits"].argmax(dim=-1).item()
        intent_pred = outputs["intent_logits"].argmax(dim=-1).item()

        # LED mapping based on safety prediction
        if safety_pred == 3:
            led_color = "RED_FLASHING"
        elif safety_pred == 2:
            led_color = "AMBER"
        elif safety_pred == 1:
            led_color = "BLUE_INFO"
        else:
            led_color = "GREEN"

        # Generate LCD summary with STRICT 16-char formatting
        safety_str = SAFETY_LABELS[safety_pred]
        intent_str = INTENT_LABELS[intent_pred]
        arm_str = ARM_LABELS[arm_pred]

        short_safety = {0: "[SAFE]", 1: "[INFO]", 2: "[WARN]", 3: "[CRIT]"}[safety_pred]
        intent_abbrev = intent_str[:9]
        lcd_line1 = f"{short_safety} {intent_abbrev}".strip()[:16].ljust(16)
        lcd_line2 = f"PTR: {arm_str}".strip()[:16].ljust(16)
        lcd_display = f"{lcd_line1}\n{lcd_line2}"

        # Default pedagogical speech synthesis text
        speech_response = f"Analysis complete. Status {safety_str.lower()}. Intent detected as {intent_str.lower().replace('_', ' ')}. Directing attention to {arm_str.lower().replace('_', ' ')}."

        latency_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "query": query,
            "safety_level": safety_pred,
            "safety_label": safety_str,
            "arm_target": arm_pred,
            "arm_label": arm_str,
            "intent": intent_pred,
            "intent_label": intent_str,
            "led_color": led_color,
            "speech_response": speech_response,
            "lcd_display": lcd_display,
            "latency_ms": round(latency_ms, 2),
            "pipeline_stage": "EDGE_NEURAL_INFERENCE"
        }
