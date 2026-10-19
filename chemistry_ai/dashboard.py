"""
IQO Bot Chemistry AI - Real-Time Terminal Dashboard
Provides a clean, direct CLI query-response loop for chemistry laboratory practicals.
"""

import os
import sys
import time
from pathlib import Path

# Configure UTF-8 encoding for cross-platform terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")

if os.name == "nt":
    os.system("")

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from chemistry_ai.src.pipeline import ChemistryAIPipeline

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"

ARM_POSITIONS = {
    "NONE": "Resting Position (Home 0°, 0°, 0°)",
    "GOGGLE_RACK": "Pointing UP-LEFT to Safety Goggle Rack (-45°, +30°, 20cm)",
    "EYEWASH_STATION": "Pointing FAR-LEFT to Emergency Eyewash (-80°, -10°, 45cm)",
    "FUME_HOOD": "Pointing REAR-LEFT into Chemical Fume Hood (-120°, +15°, 50cm)",
    "CHEMICAL_WASTE": "Pointing FAR-RIGHT to Waste Carboy (+85°, -20°, 40cm)",
    "BURETTE_STAND": "Pointing CENTER-HIGH to Burette Meniscus (0°, +45°, 35cm)",
    "REAGENT_SHELF": "Pointing REAR-CENTER to Reagent Chemical Shelf (0°, +60°, 55cm)",
    "BENCH_WORKSTATION": "Pointing DOWN-CENTER to Workspace Bench (0°, -30°, 25cm)"
}


def print_response_card(res):
    safety = res["safety_label"]
    if safety == "CRITICAL":
        badge = f"\033[41m\033[97m\033[1m CRITICAL \033[0m"
        led = f"{RED}{BOLD}● FLASHING RED (Emergency Hazard){RESET}"
    elif safety == "WARNING":
        badge = f"\033[43m\033[97m\033[1m WARNING \033[0m"
        led = f"{YELLOW}{BOLD}● SOLID AMBER (Caution / Hazard){RESET}"
    elif safety == "INFO":
        badge = f"\033[44m\033[97m\033[1m INFO \033[0m"
        led = f"{BLUE}{BOLD}● CYAN BLUE (Informational / Equilibrium){RESET}"
    else:
        badge = f"\033[42m\033[97m\033[1m SAFE \033[0m"
        led = f"{GREEN}{BOLD}● SOLID GREEN (Normal / Safe){RESET}"

    arm_key = res["arm_label"]
    arm_desc = ARM_POSITIONS.get(arm_key, arm_key)

    # Clean 16x2 LCD lines (strictly 16 characters each)
    lcd_lines = res["lcd_display"].split("\n")
    l1 = (lcd_lines[0] if len(lcd_lines) > 0 else "")[:16].ljust(16)
    l2 = (lcd_lines[1] if len(lcd_lines) > 1 else "")[:16].ljust(16)

    print("\n" + f"{CYAN}┌─────────────────────────────────────────────────────────────────────────────┐{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}Query:{RESET} \"{res['query']}\"")
    print(f"{CYAN}├─────────────────────────────────────────────────────────────────────────────┤{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}Engine Stage   :{RESET} {MAGENTA}{res['pipeline_stage']}{RESET} (Latency: {GREEN}{res['latency_ms']:.2f} ms{RESET})")
    print(f"{CYAN}│{RESET} {BOLD}Safety Rating  :{RESET} {badge} | {BOLD}Intent:{RESET} {WHITE}{res['intent_label']}{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}RGB LED State  :{RESET} {led}")
    print(f"{CYAN}├─────────────────────────────────────────────────────────────────────────────┤{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}Robotic Arm    :{RESET} {YELLOW}{BOLD}{arm_key}{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}Physical Action:{RESET} {DIM}{arm_desc}{RESET}")
    print(f"{CYAN}├─────────────────────────────────────────────────────────────────────────────┤{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}Hardware LCD Display (16x2 Screen):{RESET}")
    print(f"{CYAN}│{RESET}   ┌──────────────────┐")
    print(f"{CYAN}│{RESET}   │ {YELLOW}{l1}{RESET} │")
    print(f"{CYAN}│{RESET}   │ {CYAN}{l2}{RESET} │")
    print(f"{CYAN}│{RESET}   └──────────────────┘")
    print(f"{CYAN}├─────────────────────────────────────────────────────────────────────────────┤{RESET}")
    print(f"{CYAN}│{RESET} {BOLD}Voice Speech (TTS Audio Output):{RESET}")

    words = res["speech_response"].split()
    line_buf = "   \""
    for w in words:
        if len(line_buf) + len(w) + 1 > 72:
            print(f"{CYAN}│{RESET}{WHITE}{line_buf}{RESET}")
            line_buf = "    " + w
        else:
            line_buf += (" " if line_buf != "   \"" else "") + w
    print(f"{CYAN}│{RESET}{WHITE}{line_buf}\"{RESET}")
    print(f"{CYAN}└─────────────────────────────────────────────────────────────────────────────┘{RESET}\n")


def main():
    ckpt = PROJECT_ROOT / "checkpoints" / "best_model.pt"
    vocab = PROJECT_ROOT / "data" / "processed" / "vocab.json"

    print(f"\n{BOLD}{CYAN}========================================================================{RESET}")
    print(f"{BOLD}{WHITE}                   IQO BOT - CHEMISTRY AI DASHBOARD                     {RESET}")
    print(f"{BOLD}{CYAN}========================================================================{RESET}")
    print(f"{DIM}Loading Edge Model: {ckpt.name} | Vocab: {vocab.name}{RESET}")

    pipeline = ChemistryAIPipeline.load_from_checkpoint(
        checkpoint_path=str(ckpt),
        vocab_path=str(vocab),
        device="cpu"
    )

    print(f"{GREEN}[Ready]{RESET} Enter any question, chemical mixture, or 'exit' to quit.")
    print(f"{DIM}Tip: Prefix with '!goggles' to simulate webcam detecting missing eye protection.{RESET}\n")

    while True:
        try:
            query = input(f"{BOLD}{CYAN}Enter the query: {RESET}").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting dashboard.")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            print(f"{GREEN}Dashboard session closed.{RESET}")
            break

        missing_goggles = False
        if query.startswith("!goggles"):
            missing_goggles = True
            query = query.replace("!goggles", "").strip() or "Student near reagents without goggles"

        res = pipeline.process(query, visual_missing_goggles=missing_goggles)
        print_response_card(res)


if __name__ == "__main__":
    main()
