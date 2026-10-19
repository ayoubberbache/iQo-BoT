"""Topic catalogue: label + response for every situation the bot knows.
Each topic fixes intent / safety / arm zone and the LCD + TTS output.
The neural model learns to map free text -> topic (embedding head) and
-> the 3 classification heads; this table renders the answer."""
from config import lcd, SAFETY, INTENTS, ARM

T = {}


def add(tid, intent, safety, zone, l1, l2, tts):
    T[tid] = dict(intent=intent, safety=safety, zone=zone, lcd=(l1, l2), tts=tts)


# ---------------- titration (Demo 1) ----------------
add("titr_meniscus", "TITRATION_GUIDANCE", "SAFE", "BURETTE_STAND",
    "READ MENISCUS", "BOTTOM,EYE LEVEL",
    "Read the bottom of the concave meniscus with your eye level to the liquid surface. "
    "Hold a white card behind the burette so the curve is easy to see.")
add("titr_overshoot", "TITRATION_GUIDANCE", "INFO", "BURETTE_STAND",
    "OVERSHOT ENDPT", "NOTE VOL.REPEAT",
    "The dark magenta means you overshot the endpoint. Record the overshot volume, discard the "
    "solution in the waste carboy, and repeat the titration adding titrant dropwise near the end.")
add("titr_indicator", "TITRATION_GUIDANCE", "INFO", "BURETTE_STAND",
    "PHENOLPHTHALEIN", "PH 8.2-10.0",
    "For a strong acid with a strong base, use phenolphthalein. It changes from colourless to pale "
    "pink between pH 8.2 and 10, which brackets the steep equivalence region near pH 7.")

# ---------------- reagent chemistry / concepts ----------------
add("h3o_so4", "REAGENT_COMPATIBILITY", "INFO", "BENCH_WORKSTATION",
    "H3O+ + SO4 2-", "CONJUGATE PAIR",
    "Hydronium and sulfate are a conjugate acid base system in equilibrium: two hydronium plus "
    "sulfate gives sulfuric acid and water. In dilute solution this is not hazardous.")
add("acidbase_dilute", "REAGENT_COMPATIBILITY", "SAFE", "BENCH_WORKSTATION",
    "DILUTE ACID/BASE", "SAFE AT BENCH",
    "Dilute acid with dilute base is a normal neutralisation. It releases mild heat and forms salt "
    "and water. Wear goggles and add slowly while swirling.")
add("conc_acid", "GENERAL_LAB_PROCEDURE", "WARNING", "FUME_HOOD",
    "CONC ACID: HOOD", "ACID INTO WATER",
    "Concentrated acid must be handled in the fume hood with goggles, gloves and a lab coat. "
    "Always add acid slowly to water, never water to acid.")

# ---------------- life-critical (Stage-1 guardrail topics) ----------------
add("water_into_acid", "SAFETY_EMERGENCY", "CRITICAL", "EYEWASH_STATION",
    "STOP! SPLATTER", "ACID INTO WATER",
    "Stop. Never pour water into concentrated acid; the heat can cause violent splattering. "
    "Step back. If anything touched you, go to the eyewash station. Always add acid to water.")
add("bleach_ammonia", "SAFETY_EMERGENCY", "CRITICAL", "FUME_HOOD",
    "EVACUATE NOW!", "CHLORAMINE GAS",
    "Evacuate now. Bleach and ammonia make toxic chloramine gas. Leave the room, get fresh air, "
    "alert everyone and call emergency services. Do not try to clean it up.")
add("bleach_acid", "SAFETY_EMERGENCY", "CRITICAL", "FUME_HOOD",
    "EVACUATE NOW!", "CHLORINE GAS",
    "Evacuate now. Bleach with acid releases chlorine gas. Leave the room, get fresh air, "
    "alert everyone and call emergency services.")
add("cyanide_acid", "SAFETY_EMERGENCY", "CRITICAL", "FUME_HOOD",
    "EVACUATE NOW!", "HCN GAS RELEASE",
    "Evacuate immediately. Acid with cyanide releases lethal hydrogen cyanide gas. Raise the alarm, "
    "call emergency services, and do not re-enter.")
add("nitric_organics", "SAFETY_EMERGENCY", "CRITICAL", "FUME_HOOD",
    "STOP! EXPLOSION", "NITRIC+ORGANIC",
    "Stop. Nitric acid with organic compounds can react violently or explode. Step back, add "
    "nothing more, and alert your instructor now.")
add("alkali_water", "SAFETY_EMERGENCY", "CRITICAL", "FUME_HOOD",
    "STEP BACK! FIRE", "NA/K + WATER",
    "Step back. Sodium or potassium with water releases hydrogen and can ignite. "
    "Use a Class D extinguisher or dry sand, never water. Alert your instructor.")
add("splash", "SAFETY_EMERGENCY", "CRITICAL", "EYEWASH_STATION",
    "EYEWASH NOW", "FLUSH 15 MIN",
    "Go to the eyewash station now. Flush the skin or eyes with water continuously for fifteen "
    "minutes, remove contaminated clothing, and get medical help.")

# concept versions of the dangerous pairs: educational question -> WARNING, not alarm
_CONCEPT = {
    "water_into_acid": ("DILUTION RULE", "ACID INTO WATER",
        "Water added to concentrated acid can boil locally and spit acid. Remember the rule: "
        "add acid slowly to water, with stirring, in the fume hood."),
    "bleach_ammonia": ("BLEACH+AMMONIA", "TOXIC GAS-NO MIX",
        "Bleach and ammonia form chloramine gas, which damages the lungs. Never mix or store them together."),
    "bleach_acid": ("BLEACH + ACID", "CL2 GAS-NO MIX",
        "Hypochlorite plus acid releases chlorine gas. Never mix bleach with acids or vinegar."),
    "cyanide_acid": ("CYANIDE + ACID", "HCN GAS-NO MIX",
        "Cyanide salts with acid release hydrogen cyanide, a lethal gas. They are kept strictly apart."),
    "nitric_organics": ("HNO3+ORGANICS", "EXPLOSIVE-NO MIX",
        "Concentrated nitric acid is a strong oxidiser and can react explosively with organic solvents."),
    "alkali_water": ("NA/K + WATER", "H2 FIRE-KEEP DRY",
        "Alkali metals reduce water, releasing hydrogen and heat that can ignite it. They are stored under oil."),
}
for _k, (_a, _b, _s) in _CONCEPT.items():
    add(_k + "_concept", "REAGENT_COMPATIBILITY", "WARNING", "FUME_HOOD", _a, _b, _s)

# ---------------- PPE, calc, msds, waste, general ----------------
add("no_goggles", "PPE_VIOLATION", "WARNING", "GOGGLE_RACK",
    "PPE: NO GOGGLES", "WEAR GOGGLES",
    "I cannot see safety goggles. Please put on chemical splash goggles from the rack before "
    "touching any reagent.")
add("stoich", "CALCULATION_STOICHIOMETRY", "SAFE", "BENCH_WORKSTATION",
    "STOICHIOMETRY", "MOLES=C x V",
    "Use moles equal concentration times volume in litres. For one to one acid base titration, "
    "C acid times V acid equals C base times V base at the endpoint.")
add("msds", "MSDS_INQUIRY", "INFO", "REAGENT_SHELF",
    "SDS / GHS INFO", "CHECK SHELF SDS",
    "Check the safety data sheet on the reagent shelf for hazard statements, pictograms and "
    "required protection. Corrosives need goggles, nitrile gloves and a lab coat.")
add("waste", "WASTE_DISPOSAL", "INFO", "CHEMICAL_WASTE",
    "WASTE: CARBOY", "LABEL+SEGREGATE",
    "Pour chemical waste only into the correct labelled carboy. Keep acids, bases and organics "
    "separate and never use the sink unless your instructor confirms.")
add("general", "GENERAL_LAB_PROCEDURE", "SAFE", "BENCH_WORKSTATION",
    "LAB PROCEDURE", "FOLLOW SOP",
    "Follow the written procedure step by step, keep the bench tidy, and ask me if you are unsure "
    "about any step.")
add("greeting", "GENERAL_LAB_PROCEDURE", "SAFE", "REST",
    "IQO BOT READY", "ASK ME CHEMISTRY",
    "Hello, I am IQO Bot. Ask me about titration, reagent safety, calculations or waste disposal.")

TOPIC_IDS = list(T)
TOPIC_INDEX = {t: i for i, t in enumerate(TOPIC_IDS)}

# generic fallback when topic confidence is low: answer by intent head
GENERIC = {
    "TITRATION_GUIDANCE": ("TITRATION HELP", "ASK STEP/TOPIC", "Ask me about reading the burette, indicators or the endpoint."),
    "REAGENT_COMPATIBILITY": ("CHECK SDS FIRST", "BEFORE MIXING", "Check the safety data sheet before mixing any reagents."),
    "SAFETY_EMERGENCY": ("SAFETY ALERT", "STOP, STEP BACK", "Stop what you are doing, step back and tell your instructor."),
    "PPE_VIOLATION": ("PPE CHECK", "WEAR GOGGLES", "Put on goggles, gloves and a lab coat."),
    "CALCULATION_STOICHIOMETRY": ("CALCULATION", "MOLES=C x V", "Tell me the concentrations and volumes and we can work it through."),
    "MSDS_INQUIRY": ("SDS / GHS INFO", "CHECK SHELF SDS", "Check the safety data sheet on the reagent shelf."),
    "WASTE_DISPOSAL": ("WASTE: CARBOY", "LABEL+SEGREGATE", "Use the correct labelled waste carboy."),
    "GENERAL_LAB_PROCEDURE": ("LAB PROCEDURE", "FOLLOW SOP", "Follow the written procedure and ask if unsure."),
}

for _t, _d in T.items():
    assert _d["safety"] in SAFETY and _d["intent"] in INTENTS and _d["zone"] in ARM, _t
    assert all(len(x) <= 16 for x in _d["lcd"]), (_t, _d["lcd"])
for _i, (_a, _b, _) in GENERIC.items():
    assert len(_a) <= 16 and len(_b) <= 16, _i
