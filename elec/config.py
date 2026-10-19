"""IQO Bot - ELECTRONICS bench pack: hardware map, label spaces, tokenizer."""
import numpy as np

LCD_WIDTH = 16
ARTIFACT = "edge_elec_net"
HEADER = "iqo_elec_embedded_config.h"


def lcd(line: str) -> str:
    """Hard 16-char guarantee for the 16x2 character LCD."""
    return line[:LCD_WIDTH].ljust(LCD_WIDTH)


# (pan_deg, tilt_deg, reach_cm). PLACEHOLDERS: calibrate to your bench layout.
ZONES = {
    "GOGGLE_RACK":       (-45, +30, 20),
    "FIRE_EXTINGUISHER": (-110, 0, 50),
    "FUME_EXTRACTOR":    (-120, +15, 50),
    "SOLDERING_STATION": (+45, -15, 30),
    "POWER_SUPPLY":      (+80, -10, 40),
    "TEST_EQUIPMENT":    (+30, +20, 35),
    "EWASTE_BIN":        (+110, -20, 40),
    "BENCH_WORKSTATION": (0, -30, 25),
}
ARM = {**ZONES, "REST": (0, 0, 10)}
ARM_CLASSES = list(ARM)

SAFETY = ["SAFE", "INFO", "WARNING", "CRITICAL"]
LED = {"SAFE": "SOLID GREEN", "INFO": "CYAN BLUE", "WARNING": "SOLID AMBER", "CRITICAL": "FLASHING RED"}
INTENTS = [
    "MEASUREMENT_GUIDANCE", "COMPONENT_COMPATIBILITY", "SAFETY_EMERGENCY", "PPE_VIOLATION",
    "CIRCUIT_CALCULATION", "DATASHEET_INQUIRY", "EWASTE_DISPOSAL", "GENERAL_BENCH_PROCEDURE",
]

MAX_LEN = 96
CHARS = " abcdefghijklmnopqrstuvwxyz0123456789.,%+-/()?!'^=:*"
VOCAB = {c: i + 2 for i, c in enumerate(CHARS)}
VOCAB_SIZE = len(VOCAB) + 2

_SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻−", "0123456789" "0123456789" "+--")


def normalize(text: str) -> str:
    t = text.translate(_SUB).lower()
    t = t.replace("ω", " ohm ").replace("µ", "u").replace("μ", "u").replace("°", " deg ")
    return " ".join(t.split())


def encode(text: str) -> np.ndarray:
    t = normalize(text)[:MAX_LEN]
    ids = [VOCAB.get(c, 1) for c in t] + [0] * (MAX_LEN - len(t))
    return np.asarray(ids, dtype=np.int64)[None, :]
