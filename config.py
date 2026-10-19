"""IQO Bot shared constants: hardware map, label spaces, tokenizer."""
import numpy as np

LCD_WIDTH = 16


def lcd(line: str) -> str:
    """Hard 16-char guarantee for the 16x2 character LCD."""
    return line[:LCD_WIDTH].ljust(LCD_WIDTH)


# (pan_deg, tilt_deg, reach_cm) per the hardware spec
ZONES = {
    "GOGGLE_RACK":       (-45, +30, 20),
    "EYEWASH_STATION":   (-80, -10, 45),
    "FUME_HOOD":         (-120, +15, 50),
    "CHEMICAL_WASTE":    (+85, -20, 40),
    "BURETTE_STAND":     (0, +45, 35),
    "REAGENT_SHELF":     (0, +60, 55),
    "BENCH_WORKSTATION": (0, -30, 25),
}
ARM = {**ZONES, "REST": (0, 0, 10)}          # 8th class = idle pose
ARM_CLASSES = list(ARM)

SAFETY = ["SAFE", "INFO", "WARNING", "CRITICAL"]
LED = {
    "SAFE": "SOLID GREEN",
    "INFO": "CYAN BLUE",
    "WARNING": "SOLID AMBER",
    "CRITICAL": "FLASHING RED",
}
INTENTS = [
    "TITRATION_GUIDANCE", "REAGENT_COMPATIBILITY", "SAFETY_EMERGENCY",
    "PPE_VIOLATION", "CALCULATION_STOICHIOMETRY", "MSDS_INQUIRY",
    "WASTE_DISPOSAL", "GENERAL_LAB_PROCEDURE",
]

# ---- character-level tokenizer (robust to typos, tiny vocab) ----
MAX_LEN = 96
CHARS = " abcdefghijklmnopqrstuvwxyz0123456789.,%+-/()?!'^=:*"
VOCAB = {c: i + 2 for i, c in enumerate(CHARS)}   # 0=<pad>, 1=<unk>
VOCAB_SIZE = len(VOCAB) + 2

_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻−", "0123456789" "0123456789" "+--")


def normalize(text: str) -> str:
    return " ".join(text.translate(_SUB).lower().split())


def encode(text: str) -> np.ndarray:
    t = normalize(text)[:MAX_LEN]
    ids = [VOCAB.get(c, 1) for c in t] + [0] * (MAX_LEN - len(t))
    return np.asarray(ids, dtype=np.int64)[None, :]
