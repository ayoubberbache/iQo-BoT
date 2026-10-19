"""
Dataset Generator & Compiler for IQO Bot Chemistry AI
Translates laboratory domain knowledge into an annotated multi-task dataset.
"""

import json
import os
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

# Class label mappings
SAFETY_LEVELS = {
    "SAFE": 0,
    "INFO": 1,
    "WARNING": 2,
    "CRITICAL": 3
}

ARM_TARGETS = {
    "NONE": 0,
    "GOGGLE_RACK": 1,
    "EYEWASH_STATION": 2,
    "FUME_HOOD": 3,
    "CHEMICAL_WASTE": 4,
    "BURETTE_STAND": 5,
    "REAGENT_SHELF": 6,
    "BENCH_WORKSTATION": 7
}

INTENTS = {
    "TITRATION_GUIDANCE": 0,
    "REAGENT_COMPATIBILITY": 1,
    "SAFETY_EMERGENCY": 2,
    "PPE_VIOLATION": 3,
    "CALCULATION_STOICHIOMETRY": 4,
    "MSDS_INQUIRY": 5,
    "WASTE_DISPOSAL": 6,
    "GENERAL_LAB_PROCEDURE": 7
}


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def build_augmented_queries():
    dataset = []

    # 1. Incompatible chemicals & dangerous reactions
    incompatibles = load_json(RAW_DIR / "incompatible_chemicals.json")
    prefix_templates = [
        "Can I mix {chem_a} and {chem_b}?",
        "What happens if I combine {chem_a} with {chem_b}?",
        "Is it safe to add {chem_a} to {chem_b}?",
        "I am about to pour {chem_a} into {chem_b}, is that okay?",
        "Mixing {chem_a} together with {chem_b} in my flask.",
        "Accidentally mixed {chem_a} and {chem_b}!",
        "Can we put {chem_a} into the same beaker as {chem_b}?",
        "Is {chem_a} compatible with {chem_b} in this reaction?",
        "Should I dilute {chem_a} with {chem_b} directly?",
        "What is the reaction between {chem_a} and {chem_b}?"
    ]

    for item in incompatibles:
        ca = item["chemical_a"].split("(")[0].strip()
        cb = item["chemical_b"].split("(")[0].strip()
        ca_short = item["chemical_a"].split("(")[-1].replace(")", "").strip() if "(" in item["chemical_a"] else ca
        cb_short = item["chemical_b"].split("(")[-1].replace(")", "").strip() if "(" in item["chemical_b"] else cb

        all_a = list(set([ca.lower(), ca_short.lower()]))
        all_b = list(set([cb.lower(), cb_short.lower()]))

        for a_name in all_a:
            for b_name in all_b:
                for tmpl in prefix_templates:
                    q = tmpl.format(chem_a=a_name, chem_b=b_name)
                    dataset.append({
                        "query": q,
                        "safety_level": SAFETY_LEVELS[item["hazard_level"]],
                        "arm_target": ARM_TARGETS[item["arm_target"]],
                        "intent": INTENTS["REAGENT_COMPATIBILITY"],
                        "led_color": item["led_color"],
                        "speech_response": item["warning_speech"],
                        "lcd_display": item["lcd_message"]
                    })

        for tr in item.get("triggers", []):
            dataset.append({
                "query": tr,
                "safety_level": SAFETY_LEVELS[item["hazard_level"]],
                "arm_target": ARM_TARGETS[item["arm_target"]],
                "intent": INTENTS["REAGENT_COMPATIBILITY"],
                "led_color": item["led_color"],
                "speech_response": item["warning_speech"],
                "lcd_display": item["lcd_message"]
            })

    # 2. PPE Violations & Lab Dress Code
    ppe_templates = [
        ("I forgot my safety goggles on the desk", "Safety alert! Safety goggles are mandatory at all times at the chemistry workbench. Put on your protective eye goggles immediately.", "PPE VIOLATION:\nWEAR GOGGLES NOW!", "GOGGLE_RACK"),
        ("Can I take off my safety goggles for a second?", "No, never remove safety goggles at the bench while chemicals or glassware are in use.", "NEVER REMOVE\nGOGGLES AT BENCH", "GOGGLE_RACK"),
        ("My goggles are foggy, can I work without them?", "Step back from the bench to clear fogging, but never remove goggles while working with reagents.", "GOGGLES FOGGED:\nSTEP BACK & CLEAN", "GOGGLE_RACK"),
        ("Is it fine to wear sandals or open shoes in lab?", "Violent hazard! Open-toed shoes are strictly prohibited. Wear closed-toe shoes to prevent chemical burn injuries.", "NO OPEN SHOES:\nCLOSED TOE ONLY", "BENCH_WORKSTATION"),
        ("Should I tie back long hair near the Bunsen burner?", "Yes, long hair must be tied securely to prevent accidental ignition from open flames.", "FIRE SAFETY:\nTIE BACK LONG HAIR", "BENCH_WORKSTATION"),
        ("Can I eat or drink water at the bench?", "Strict prohibition! Never consume food or beverages in the chemical laboratory due to contamination risks.", "NO FOOD/DRINK\nCONTAMINATION RISK", "BENCH_WORKSTATION"),
        ("Do I need nitrile gloves for handling concentrated sodium hydroxide?", "Yes, wear nitrile gloves and eye protection. Sodium hydroxide causes rapid saponification of skin tissues.", "WEAR GLOVES:\nCORROSIVE NAOH", "REAGENT_SHELF"),
        ("Student detected at bench with no eye protection", "Warning! Webcam detects missing safety goggles. Goggles required prior to handling laboratory glassware.", "WEAR GOGGLES:\nEYE SAFETY REQ", "GOGGLE_RACK")
    ]
    for q_base, sp, lcd, arm in ppe_templates:
        for prefix in ["", "Excuse me, ", "Hey bot, ", "Question: ", "Is it allowed: "]:
            dataset.append({
                "query": prefix + q_base,
                "safety_level": SAFETY_LEVELS["WARNING"],
                "arm_target": ARM_TARGETS[arm],
                "intent": INTENTS["PPE_VIOLATION"],
                "led_color": "AMBER",
                "speech_response": sp,
                "lcd_display": lcd
            })

    # 3. Emergency Responses (Skin, Eyes, Spills, Inhalation)
    emergency_templates = [
        ("I splashed acid into my eye!", "Emergency! Immediately flush eyes at the eyewash station for 15 minutes holding eyelids open. Calling supervisor.", "EMERGENCY: EYEWASH\nFLUSH 15 MINUTES!", "EYEWASH_STATION"),
        ("Chemical splashed in my eyes!", "Emergency! Keep eyes open and flush continuously with cold water at the eyewash station for 15 minutes.", "EMERGENCY EYEWASH\n15 MIN FLUSH!", "EYEWASH_STATION"),
        ("I spilled concentrated sulfuric acid on my arm!", "Emergency! Strip contaminated clothing and rinse skin under continuous running water for fifteen minutes.", "ACID ON SKIN:\nRINSE WATER 15M", "EYEWASH_STATION"),
        ("Sodium hydroxide spilled on my fingers!", "Wash hands thoroughly with cold running water for 15 minutes. Report caustic alkali contact to the lab instructor.", "BASE ON SKIN:\nWASH COPIOUS H2O", "EYEWASH_STATION"),
        ("I inhaled pungent gas and coughing violently!", "Evacuate the area immediately to fresh air. Notify the instructor. Seek medical evaluation for chemical vapor inhalation.", "GAS INHALATION:\nEVACUATE TO AIR", "FUME_HOOD"),
        ("The reaction flask is boiling over with heavy smoke!", "Turn off heating mantle immediately. Lower the fume hood sash and step away from the workbench.", "SMOKE & BOILOVER:\nCUT HEAT & SASH", "FUME_HOOD"),
        ("Glass beaker broke and someone has a cut!", "Apply gentle pressure with sterile gauze. Inform the lab supervisor immediately and dispose of broken glass in designated sharps bin.", "FIRST AID: CUT\nPRESSURE & REPORT", "BENCH_WORKSTATION")
    ]
    for q_base, sp, lcd, arm in emergency_templates:
        for prefix in ["Help! ", "Emergency: ", "Urgent: ", "", "Oh no, "]:
            dataset.append({
                "query": prefix + q_base,
                "safety_level": SAFETY_LEVELS["CRITICAL"],
                "arm_target": ARM_TARGETS[arm],
                "intent": INTENTS["SAFETY_EMERGENCY"],
                "led_color": "RED_FLASHING",
                "speech_response": sp,
                "lcd_display": lcd
            })

    # 4. Titration Guidance & Procedures
    titration_templates = [
        ("How do I read the burette meniscus correctly?", "Position your eye level with the liquid meniscus and read the graduation mark at the bottom of the curve.", "BURETTE READING:\nBOTTOM OF CURVE", "BURETTE_STAND"),
        ("Why is my titration solution bright purple or dark magenta?", "The endpoint was overshot by adding too much sodium hydroxide. Discard this titration run and repeat dropwise near the end.", "OVERSHOT ENDPOINT\nDISCARD & RE-RUN", "CHEMICAL_WASTE"),
        ("What color should the phenolphthalein turn at the equivalence point?", "The endpoint of phenolphthalein is the first faint, pale pink color that persists for thirty seconds.", "ENDPT COLOR:\nPALE FAINT PINK", "BURETTE_STAND"),
        ("There is an air bubble trapped in my burette tip, how to remove it?", "Open the stopcock fully to flush a rapid stream of titrant into a waste beaker until the air bubble is expelled.", "AIR BUBBLE TIP:\nFLUSH STOPCOCK", "BURETTE_STAND"),
        ("Should I rinse the burette with water or titrant?", "After washing with water, always rinse the burette twice with small portions of the titrant solution before filling.", "BURETTE RINSE:\nUSE TITRANT 2X", "BURETTE_STAND"),
        ("How many drops of indicator should I add to the flask?", "Add only two to three drops of indicator. Excess indicator alters the volume required for neutralization.", "INDICATOR DOSE:\n2 TO 3 DROPS", "BURETTE_STAND"),
        ("How do I know when I am close to the titration endpoint?", "When pink flashes persist for several seconds while swirling, slow down and add the titrant drop by drop, or half-drops.", "APPROACHING END:\nADD HALF DROPS", "BURETTE_STAND"),
        ("Which indicator for strong acid and strong base?", "Phenolphthalein or bromothymol blue are suitable because the pH curve transitions sharply between pH 4 and 10.", "INDICATOR: PHPH\nOR BROMOTHYMOL", "BURETTE_STAND")
    ]
    for q_base, sp, lcd, arm in titration_templates:
        for prefix in ["", "Can you explain ", "How do I do: ", "Tell me: ", "Step for: "]:
            dataset.append({
                "query": prefix + q_base,
                "safety_level": SAFETY_LEVELS["SAFE"] if "purple" not in q_base else SAFETY_LEVELS["WARNING"],
                "arm_target": ARM_TARGETS[arm],
                "intent": INTENTS["TITRATION_GUIDANCE"],
                "led_color": "GREEN" if "purple" not in q_base else "AMBER",
                "speech_response": sp,
                "lcd_display": lcd
            })

    # 5. Calculations & Stoichiometry
    calc_templates = [
        ("How do I calculate the concentration of unknown HCl from titration?", "Use C_acid times V_acid equals C_base times V_base. Divide the moles of base consumed by the volume of acid aliquot.", "CALCULATION:\nCa = (Cb*Vb)/Va", "BENCH_WORKSTATION"),
        ("What is the formula for calculating pH?", "pH is defined as minus the logarithm in base ten of the hydrogen ion concentration, pH equals minus log of H plus.", "PH FORMULA:\nPH = -LOG[H+]", "BENCH_WORKSTATION"),
        ("How to calculate dilution volume C1 V1 equals C2 V2?", "Initial concentration times initial volume equals final concentration times final volume. Solve for the unknown volume.", "DILUTION EQ:\nC1*V1 = C2*V2", "BENCH_WORKSTATION"),
        ("How do I find the molar mass from a chemical formula?", "Sum the atomic masses of all constituent atoms multiplied by their stoichiometry subscripts from the periodic table.", "MOLAR MASS:\nSUM(ATOMIC WEIGHT)", "BENCH_WORKSTATION"),
        ("How to calculate percent error in titration?", "Percent error is the absolute value of experimental value minus theoretical value, divided by theoretical value, times 100 percent.", "PERCENT ERROR:\n|EXP-THEO|/THEO*100", "BENCH_WORKSTATION"),
        ("How many moles are in 5 grams of sodium hydroxide?", "Five grams divided by the molar mass of forty grams per mole equals zero point one two five moles of NaOH.", "MOLES NAOH:\n5g / 40g/mol=0.125", "BENCH_WORKSTATION")
    ]
    for q_base, sp, lcd, arm in calc_templates:
        for prefix in ["", "Help with math: ", "Formula please: ", "Solve this: "]:
            dataset.append({
                "query": prefix + q_base,
                "safety_level": SAFETY_LEVELS["SAFE"],
                "arm_target": ARM_TARGETS[arm],
                "intent": INTENTS["CALCULATION_STOICHIOMETRY"],
                "led_color": "GREEN",
                "speech_response": sp,
                "lcd_display": lcd
            })

    # 6. Waste Disposal
    waste_templates = [
        ("Where do I dispose of the titrated neutralized solution?", "Neutralized salt solutions can be discarded in the aqueous inorganic waste container, never municipal drain.", "WAQUEOUS WASTE:\nINORGANIC CARBOY", "CHEMICAL_WASTE"),
        ("Can I pour heavy metal waste down the sink?", "Never dispose of heavy metal ions like silver, lead, copper, or nickel in the sink. Use the heavy metal carboy.", "PROHIBITED SINK:\nHEAVY METAL TANK", "CHEMICAL_WASTE"),
        ("Where does organic solvent waste go?", "Dispose of acetone, ethanol, and hexane in the designated halogenated or non-halogenated organic solvent waste carboys.", "ORGANIC WASTE:\nSOLVENT CARBOY", "CHEMICAL_WASTE"),
        ("Where do I throw away broken glass test tubes?", "Broken glass must be deposited in the rigid yellow broken glass box, never in ordinary paper trash bins.", "BROKEN GLASS:\nSHARPS BIN ONLY", "CHEMICAL_WASTE"),
        ("What should I do with excess concentrated acid?", "Do not pour concentrated acid down the drain. Neutralize slowly in an ice bath with sodium bicarbonate first.", "EXCESS ACID:\nNEUTRALIZE FIRST", "CHEMICAL_WASTE")
    ]
    for q_base, sp, lcd, arm in waste_templates:
        for prefix in ["", "Disposal question: ", "Where does this go: ", "Tell me where to dump: "]:
            dataset.append({
                "query": prefix + q_base,
                "safety_level": SAFETY_LEVELS["WARNING"],
                "arm_target": ARM_TARGETS[arm],
                "intent": INTENTS["WASTE_DISPOSAL"],
                "led_color": "AMBER",
                "speech_response": sp,
                "lcd_display": lcd
            })

    # 7. MSDS & Chemical Properties
    msds = load_json(RAW_DIR / "msds_knowledge.json")
    for chem in msds:
        cname = chem["name"].split("(")[0].strip()
        cformula = chem["formula"]
        target = ARM_TARGETS.get(chem.get("target_station", "REAGENT_SHELF"), ARM_TARGETS["REAGENT_SHELF"])

        queries = [
            f"What are the hazards of {cname}?",
            f"MSDS sheet for {cformula}",
            f"How do I safely handle {cname}?",
            f"How to store {cformula}?",
            f"How do I neutralize spilled {cname}?",
            f"What is the CAS number and hazard class of {cformula}?",
            f"Show safety information for {cname}"
        ]
        resp = f"{cname} ({cformula}) is {', '.join(chem['hazard_class'])}. Neutralization: {chem['neutralization']}"
        lcd = f"MSDS: {cformula}\n{chem['hazard_class'][0][:16]}"

        for q in queries:
            dataset.append({
                "query": q,
                "safety_level": SAFETY_LEVELS["INFO"],
                "arm_target": target,
                "intent": INTENTS["MSDS_INQUIRY"],
                "led_color": "BLUE_INFO",
                "speech_response": resp,
                "lcd_display": lcd
            })

    # 8. General Lab Procedures & Equipment Setup
    gen_templates = [
        ("How to calibrate the analytical balance?", "Ensure the balance is level by checking the bubble vial, close glass draft shields, and press the tare button to zero.", "BALANCE CALIB:\nCHECK BUBBLE TARE", "BENCH_WORKSTATION"),
        ("Where can I find the distilled water carboy?", "The distilled water station is located on the central reagent shelf near bench row two.", "DISTILLED WATER:\nREAGENT SHELF", "REAGENT_SHELF"),
        ("How do I heat a mixture safely with a Bunsen burner?", "Ensure the air collar is adjusted for a non-luminous blue flame and point the test tube mouth away from all people.", "BUNSEN HEATING:\nPOINT TUBE AWAY", "BENCH_WORKSTATION"),
        ("How to use a volumetric pipette accurately?", "Use a rubber bulb or pipette filler. Draw liquid slightly above the calibration line, wipe tip, and adjust meniscus to line.", "VOL PIPETTE:\nUSE BULB TO LINE", "BENCH_WORKSTATION"),
        ("What is the function of boiling chips in reflux?", "Boiling stones promote smooth nucleation and prevent superheating and violent bumping during boiling.", "BOILING CHIPS:\nPREVENT BUMPING", "BENCH_WORKSTATION")
    ]
    for q_base, sp, lcd, arm in gen_templates:
        for prefix in ["", "Equipment question: ", "How do I: ", "Can you guide me on: "]:
            dataset.append({
                "query": prefix + q_base,
                "safety_level": SAFETY_LEVELS["SAFE"],
                "arm_target": ARM_TARGETS[arm],
                "intent": INTENTS["GENERAL_LAB_PROCEDURE"],
                "led_color": "GREEN",
                "speech_response": sp,
                "lcd_display": lcd
            })

    # Shuffle dataset
    random.seed(42)
    random.shuffle(dataset)
    return dataset


def build_vocabulary(dataset):
    vocab = {"<PAD>": 0, "<UNK>": 1, "<SOS>": 2, "<EOS>": 3}
    for item in dataset:
        tokens = item["query"].lower().replace("?", "").replace(",", "").replace(".", "").replace("!", "").replace("(", "").replace(")", "").split()
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)
    return vocab


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dataset = build_augmented_queries()
    vocab = build_vocabulary(dataset)

    print(f"Total compiled chemistry samples: {len(dataset)}")
    print(f"Vocabulary size: {len(vocab)}")

    with open(PROCESSED_DIR / "chem_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    with open(PROCESSED_DIR / "vocab.json", "w", encoding="utf-8") as f:
        json.dump(vocab, f, indent=2, ensure_ascii=False)

    # Class distributions
    safety_counts = {}
    target_counts = {}
    intent_counts = {}
    for item in dataset:
        s = item["safety_level"]
        t = item["arm_target"]
        i = item["intent"]
        safety_counts[s] = safety_counts.get(s, 0) + 1
        target_counts[t] = target_counts.get(t, 0) + 1
        intent_counts[i] = intent_counts.get(i, 0) + 1

    print("Safety Level Distribution:", safety_counts)
    print("Arm Target Distribution:", target_counts)
    print("Intent Distribution:", intent_counts)


if __name__ == "__main__":
    main()
