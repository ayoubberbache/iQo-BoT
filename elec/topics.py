"""Electronics-bench topic catalogue: label + response for every situation the bot knows."""
from config import lcd, SAFETY, INTENTS, ARM

T = {}


def add(tid, intent, safety, zone, l1, l2, tts):
    T[tid] = dict(intent=intent, safety=safety, zone=zone, lcd=(l1, l2), tts=tts)


# ---------------- life-critical (Stage-1 guardrail topics) ----------------
add("mains_shock", "SAFETY_EMERGENCY", "CRITICAL", "POWER_SUPPLY",
    "SHOCK! POWER OFF", "CALL EMERGENCY",
    "Cut the power at the source, or unplug it only if you can do so safely. Do not touch the person "
    "while they may still be in contact with the supply. Call emergency services and alert your instructor.")
add("battery_fire", "SAFETY_EMERGENCY", "CRITICAL", "FIRE_EXTINGUISHER",
    "BATTERY HAZARD", "MOVE AWAY NOW",
    "Stop and move away from the battery. Do not charge, squeeze or puncture it. If it is smoking or on "
    "fire, evacuate, raise the alarm and call emergency services. Only trained staff should fight a battery fire.")
add("battery_short", "SAFETY_EMERGENCY", "CRITICAL", "FIRE_EXTINGUISHER",
    "SHORT CIRCUIT!", "DISCONNECT NOW",
    "Remove the short only if you can do it without touching hot parts. A shorted battery can overheat, "
    "vent or ignite. Keep clear, tell your instructor, and do not use that battery again until it is checked.")
add("smoke_burning", "SAFETY_EMERGENCY", "CRITICAL", "POWER_SUPPLY",
    "POWER OFF NOW", "SMOKE/BURN SMELL",
    "Switch off and unplug the power now. Step back and do not touch hot parts. If there is fire or heavy "
    "smoke, evacuate and call emergency services.")
add("live_mains_work", "SAFETY_EMERGENCY", "CRITICAL", "POWER_SUPPLY",
    "STOP! LIVE MAINS", "ISOLATE FIRST",
    "Stop. Never work on mains powered circuits while they are plugged in. Unplug the equipment, wait for the "
    "capacitors to discharge, and have your instructor check it before you open it.")

# concept versions: educational question -> WARNING with explanation, not an alarm
add("battery_fire_concept", "COMPONENT_COMPATIBILITY", "WARNING", "FIRE_EXTINGUISHER",
    "LIPO FIRE RISK", "DAMAGE=THERMAL",
    "Lithium cells can enter thermal runaway when damaged, overcharged, overheated or shorted. They swell, "
    "vent flammable gas and can ignite. Never use a swollen or damaged cell.")
add("battery_short_concept", "COMPONENT_COMPATIBILITY", "WARNING", "FIRE_EXTINGUISHER",
    "SHORTING BATTERY", "HEAT/FIRE RISK",
    "A battery has very low internal resistance, so a short circuit draws a huge current. The wires and cell "
    "heat up fast and the cell can vent or ignite. Use fuses and never bridge battery terminals.")
add("live_mains_work_concept", "COMPONENT_COMPATIBILITY", "WARNING", "POWER_SUPPLY",
    "LIVE MAINS RISK", "ISOLATE FIRST",
    "Mains voltage can drive a lethal current through the body, and the circuit stays dangerous even after "
    "switching off because capacitors store charge. Always unplug, wait, and verify with a meter.")
add("voltage_safety", "COMPONENT_COMPATIBILITY", "INFO", "POWER_SUPPLY",
    "MAINS = LETHAL", "12V IS LOW RISK",
    "Mains voltage can kill. Low voltage such as 5 or 12 volts is generally low risk to touch, but short "
    "circuits and batteries can still cause burns and fires, so keep fuses and current limits in place.")

# ---------------- warnings ----------------
add("cap_polarity", "COMPONENT_COMPATIBILITY", "WARNING", "BENCH_WORKSTATION",
    "CHECK POLARITY", "STRIPE = NEG",
    "Electrolytic capacitors are polarised. The stripe marks the negative lead. Connecting one backwards or "
    "above its voltage rating can make it overheat or burst. Check before powering up.")
add("cap_discharge", "SAFETY_EMERGENCY", "WARNING", "POWER_SUPPLY",
    "DISCHARGE CAP", "USE RESISTOR",
    "Switch off and unplug first. Discharge a large capacitor through a suitable resistor, for example a few "
    "kilo ohms, then confirm with a multimeter that the voltage is near zero. Never short it with a screwdriver.")
add("lipo_charging", "GENERAL_BENCH_PROCEDURE", "WARNING", "FIRE_EXTINGUISHER",
    "LIPO CHARGING", "SUPERVISE+BAG",
    "Charge lithium polymer cells with a proper balance charger at the rated current, only while supervised, "
    "ideally in a fire resistant bag. Never charge a swollen or damaged cell, and store cells partly charged.")
add("no_ventilation", "PPE_VIOLATION", "WARNING", "FUME_EXTRACTOR",
    "SOLDER FUMES", "USE EXTRACTOR",
    "Solder flux fumes irritate the lungs. Switch on the fume extractor and keep your face out of the smoke "
    "plume while soldering.")
add("soldering_burn", "SAFETY_EMERGENCY", "WARNING", "BENCH_WORKSTATION",
    "BURN: COOL IT", "RUNNING WATER",
    "Hold the burn under cool running water for twenty minutes, remove rings nearby, do not use ice or "
    "creams, and tell your instructor. Seek medical help for anything larger than a small area.")
add("no_goggles", "PPE_VIOLATION", "WARNING", "GOGGLE_RACK",
    "PPE: NO GOGGLES", "WEAR GOGGLES",
    "I cannot see safety goggles. Please put on safety glasses from the rack before soldering or cutting "
    "component leads.")
add("multimeter_current", "MEASUREMENT_GUIDANCE", "WARNING", "TEST_EQUIPMENT",
    "MEASURE CURRENT", "IN SERIES!",
    "To measure current, break the circuit and put the meter in series, with the red lead in the current "
    "socket. Never connect a meter in current mode across a voltage source; it acts like a short circuit.")

# ---------------- info / safe ----------------
add("esd", "GENERAL_BENCH_PROCEDURE", "INFO", "BENCH_WORKSTATION",
    "ESD CARE", "USE WRIST STRAP",
    "Static discharge can damage chips without you noticing. Wear a wrist strap, work on an antistatic mat, "
    "and keep sensitive parts in antistatic bags until you use them.")
add("ohms_law", "CIRCUIT_CALCULATION", "SAFE", "BENCH_WORKSTATION",
    "OHM'S LAW", "V = I x R",
    "Voltage equals current times resistance. Power equals voltage times current. Check that the resistor's "
    "power rating is comfortably above the power it dissipates.")
add("led_resistor", "CIRCUIT_CALCULATION", "SAFE", "BENCH_WORKSTATION",
    "LED RESISTOR", "R=(VS-VF)/I",
    "Resistor equals supply voltage minus the LED forward voltage, divided by the LED current. For a five volt "
    "supply, a red LED at about two volts and ten milliamps needs about three hundred ohms; use the next "
    "higher standard value.")
add("voltage_divider", "CIRCUIT_CALCULATION", "SAFE", "BENCH_WORKSTATION",
    "VOLTAGE DIVIDER", "R2/(R1+R2)*VIN",
    "Output voltage equals input voltage times R2 divided by R1 plus R2. A divider is fine for signals but "
    "not for powering loads, because the output sags as current is drawn.")
add("rc_time", "CIRCUIT_CALCULATION", "SAFE", "BENCH_WORKSTATION",
    "RC TIME CONST", "TAU = R x C",
    "Tau equals R times C. After one tau a charging capacitor reaches about 63 percent of the supply voltage; "
    "after five tau it is essentially fully charged.")
add("resistor_code", "CIRCUIT_CALCULATION", "SAFE", "BENCH_WORKSTATION",
    "RESISTOR CODE", "BAND-BAND-MULT",
    "Read from the end with the bands closest together. The first bands are digits, the next is the "
    "multiplier and the last is tolerance. Brown black red is one kilo ohm.")
add("multimeter_voltage", "MEASUREMENT_GUIDANCE", "SAFE", "TEST_EQUIPMENT",
    "MEASURE VOLTAGE", "PARALLEL,DC/AC",
    "To measure voltage, set the meter to volts, choose AC or DC, put the red lead in the voltage socket, and "
    "touch the probes across the component, in parallel.")
add("continuity", "MEASUREMENT_GUIDANCE", "INFO", "TEST_EQUIPMENT",
    "CONTINUITY/OHMS", "POWER OFF FIRST",
    "Turn the circuit off before measuring resistance or continuity. A beep means a low resistance connection. "
    "Measuring a part still soldered in a circuit can give misleading readings.")
add("scope_probe", "MEASUREMENT_GUIDANCE", "INFO", "TEST_EQUIPMENT",
    "SCOPE PROBE", "COMP. X10 PROBE",
    "Compensate the oscilloscope probe on the calibration output before measuring. Connect the ground clip to "
    "circuit ground only, and never to a live mains point.")
add("logic_levels", "COMPONENT_COMPATIBILITY", "INFO", "BENCH_WORKSTATION",
    "3.3V vs 5V", "USE LEVEL SHIFT",
    "Do not drive a 3.3 volt input from a 5 volt output directly. Use a level shifter or a resistor divider, "
    "since the input may not tolerate 5 volts.")
add("pull_up", "COMPONENT_COMPATIBILITY", "INFO", "BENCH_WORKSTATION",
    "PULL-UP RESISTOR", "~4.7K TO VCC",
    "A pull up resistor holds an input at the supply voltage when nothing else drives it, which stops floating "
    "readings. Values of four point seven to ten kilo ohms are typical for logic inputs.")
add("flyback", "COMPONENT_COMPATIBILITY", "INFO", "BENCH_WORKSTATION",
    "FLYBACK DIODE", "ACROSS COIL",
    "Place a diode across a relay or motor coil, cathode to the positive side, to absorb the voltage spike when "
    "it switches off and protect the transistor.")
add("datasheet", "DATASHEET_INQUIRY", "INFO", "BENCH_WORKSTATION",
    "CHECK DATASHEET", "ABS MAX RATINGS",
    "Check the datasheet for absolute maximum ratings, pinout and recommended operating conditions before "
    "connecting a part.")
add("ewaste", "EWASTE_DISPOSAL", "INFO", "EWASTE_BIN",
    "E-WASTE BIN", "BATTERIES APART",
    "Put electronic parts in the e-waste bin and batteries in the battery collection box, kept separate. "
    "Never throw lithium cells into general waste. Collect leaded solder offcuts for proper disposal.")
add("soldering_tips", "GENERAL_BENCH_PROCEDURE", "SAFE", "SOLDERING_STATION",
    "SOLDERING TIPS", "HEAT PAD+LEAD",
    "Heat the pad and the lead together for a second or two, feed solder to the joint rather than the iron "
    "tip, then remove the solder and the iron. A good joint is shiny and cone shaped. Use the extractor and goggles.")
add("general", "GENERAL_BENCH_PROCEDURE", "SAFE", "BENCH_WORKSTATION",
    "BENCH PROCEDURE", "FOLLOW SOP",
    "Power off while wiring, check polarity and part values, set the supply current limit before connecting, "
    "then power up and measure. Ask me if you are unsure about any step.")
add("greeting", "GENERAL_BENCH_PROCEDURE", "SAFE", "REST",
    "IQO BOT READY", "ASK ELECTRONICS",
    "Hello, I am IQO Bot. Ask me about circuits, measurements, soldering, batteries or bench safety.")

TOPIC_IDS = list(T)
TOPIC_INDEX = {t: i for i, t in enumerate(TOPIC_IDS)}

GENERIC = {
    "MEASUREMENT_GUIDANCE": ("MEASUREMENT HELP", "ASK INSTRUMENT", "Tell me which instrument and what you want to measure."),
    "COMPONENT_COMPATIBILITY": ("CHECK RATINGS", "BEFORE WIRING", "Check voltage and current ratings in the datasheet before connecting parts."),
    "SAFETY_EMERGENCY": ("SAFETY ALERT", "POWER OFF,BACK", "Switch the power off, step back and tell your instructor."),
    "PPE_VIOLATION": ("PPE CHECK", "WEAR GOGGLES", "Put on safety glasses and use the fume extractor."),
    "CIRCUIT_CALCULATION": ("CALCULATION", "GIVE VALUES", "Tell me the voltages and component values and we can work it through."),
    "DATASHEET_INQUIRY": ("CHECK DATASHEET", "ABS MAX RATINGS", "Check the datasheet for ratings and pinout."),
    "EWASTE_DISPOSAL": ("E-WASTE BIN", "BATTERIES APART", "Use the e-waste bin and keep batteries separate."),
    "GENERAL_BENCH_PROCEDURE": ("BENCH PROCEDURE", "FOLLOW SOP", "Follow the written procedure and ask if unsure."),
}

for _t, _d in T.items():
    assert _d["safety"] in SAFETY and _d["intent"] in INTENTS and _d["zone"] in ARM, _t
    assert all(len(x) <= 16 for x in _d["lcd"]), (_t, _d["lcd"])
for _i, (_a, _b, _) in GENERIC.items():
    assert _i in INTENTS and len(_a) <= 16 and len(_b) <= 16, (_i, _a, _b)
