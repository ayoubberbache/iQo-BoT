"""Synthetic training-data generator for the electronics pack (templates x slots x noise). No downloads."""
import random
from topics import T, TOPIC_INDEX
from config import SAFETY, INTENTS, ARM_CLASSES

BAT = ["lipo", "li-po pack", "li-ion cell", "lithium battery", "18650", "battery pack", "drone battery", "phone battery"]
BHAZ = ["swollen", "puffed up", "smoking", "hissing", "venting", "on fire", "bulging", "getting very hot", "leaking and hot", "melting"]
MAINS = ["230v mains", "120v mains", "mains", "240v supply", "wall socket", "220v"]
MVERB = ["probe", "probing", "open up", "repair", "fix", "solder on", "touch", "work on", "poke around in"]
PARTS = ["lm317", "lm7805", "2n2222", "ne555", "atmega328p", "esp32", "1n4007", "lm358"]

ACTIVE_BF = ["my {b} is {h}", "the {b} is {h}", "{b} {h} help", "my {b} started {h}", "just noticed the {b} {h}"]
CONCEPT_BF = ["why do {b}s swell and catch fire", "what happens when a {b} overheats", "explain thermal runaway in a {b}",
              "why is a damaged {b} dangerous", "how does a {b} catch fire"]
ACTIVE_BS = ["i shorted the {b}", "wire touched both terminals of the {b}", "short circuit across the {b}",
             "accidentally shorted the {b} with a screwdriver", "i connected positive to negative on the {b}"]
CONCEPT_BS = ["why is shorting a {b} dangerous", "what happens if you short circuit a {b}", "explain what a shorted {b} does",
              "how does a short circuit damage a {b}"]
ACTIVE_LM = ["can i {v} {m} while it is plugged in", "i am going to {v} {m} board with power on", "{v} {m} supply live",
             "opening the plugged in power supply to fix it", "repairing a plugged in charger with {m}", "i want to {v} {m} without unplugging"]
CONCEPT_LM = ["why is working on live {m} dangerous", "what happens if you {v} {m} while powered", "explain why we unplug {m} before repair"]

STATIC = {
 "mains_shock": ["i got an electric shock", "i just got shocked by the power supply", "i touched a live wire", "she got electrocuted",
   "i was zapped by the mains", "felt a shock from the soldering station", "electric shock help", "got shocked touching the plug pins"],
 "smoke_burning": ["smoke is coming from my circuit", "burning smell from the board", "the resistor is smoking", "sparks from the power supply",
   "capacitor exploded", "my circuit caught fire", "flames on the breadboard", "something popped and smells burnt", "the chip is on fire",
   "the regulator is smoking hot and smells burnt"],
 "voltage_safety": ["is 12v dangerous", "how much voltage can kill", "is 5v safe to touch", "is mains 230v dangerous", "what voltage is safe to touch",
   "can a 9v battery shock me", "what happens in an electric shock", "why is mains more dangerous than usb power"],
 "cap_polarity": ["which way round does an electrolytic capacitor go", "i put the capacitor in backwards", "capacitor stripe means what",
   "why do electrolytic capacitors explode when reversed", "capacitor voltage rating too low what happens", "capacitor polarity marking",
   "the capacitor is bulging", "put the electrolytic in the wrong way round"],
 "cap_discharge": ["how do i discharge a capacitor safely", "discharging the big capacitor before repair", "capacitor still holds charge after unplugging",
   "safe way to drain a charged capacitor", "bleed resistor for capacitor", "how long until a capacitor discharges after switching off"],
 "lipo_charging": ["how do i charge a lipo safely", "charging lithium battery tips", "can i leave the lipo charging overnight", "storing lipo batteries",
   "lipo charger settings", "what is balance charging", "how to store lithium cells"],
 "no_ventilation": ["soldering without the fume extractor", "flux fumes making me cough", "breathing solder fumes", "do i need ventilation for soldering",
   "fume extractor not on", "solder smoke in my face", "the soldering iron is smoking"],
 "soldering_burn": ["i burned my finger on the soldering iron", "touched the hot iron tip", "burn from solder splash", "soldering iron burn first aid",
   "grabbed the hot iron by mistake", "hot solder dropped on my hand"],
 "no_goggles": ["no safety glasses while soldering", "where are the goggles", "can i clip leads without goggles", "forgot my safety glasses",
   "camera sees no goggles", "do i need eye protection for soldering", "working without goggles"],
 "multimeter_current": ["how do i measure current with a multimeter", "multimeter amps mode how to connect", "measure current in a circuit",
   "meter in series for current reading", "which jack for measuring amps", "can i put the meter across the battery in amp mode"],
 "esd": ["do i need a wrist strap for this ic", "static damage to chips", "how to avoid esd", "handling a cmos chip without antistatic mat",
   "got a static shock from my sweater near the chips", "why do i need an esd mat", "is static dangerous for microcontrollers"],
 "ohms_law": ["what is ohms law", "how much current flows through {r} ohm at {v} volts", "calculate current for {v}v and {r} ohms",
   "find resistance from voltage and current", "power dissipated in a {r} ohm resistor at {v}v", "v = i r help", "how do i calculate watts from volts and amps"],
 "led_resistor": ["what resistor do i need for an led on {v} volts", "led current limiting resistor for {v}v supply", "calculate led series resistor",
   "which resistor for a red led on arduino 5v", "how to power an led from {v}v without burning it", "led resistor value for {i} ma"],
 "voltage_divider": ["how do i make a voltage divider", "divider with {r1}k and {r2}k what output", "step down {v}v to 3.3v using resistors",
   "vout formula for two resistors", "calculate voltage divider output"],
 "rc_time": ["time constant of {r1}k resistor and {c} uf capacitor", "how long does a capacitor take to charge through a resistor", "what is tau in an rc circuit",
   "rc charging time calculation", "rc filter time constant"],
 "resistor_code": ["what does brown black red mean on a resistor", "how to read resistor colour bands", "resistor colour code help",
   "what is a resistor with yellow violet orange", "decode 4 band resistor"],
 "multimeter_voltage": ["how do i measure voltage with a multimeter", "multimeter voltage reading dc", "where do i put the probes to measure volts",
   "measure battery voltage with meter", "check supply voltage on the breadboard", "how to hook the meter across a component to read volts"],
 "continuity": ["how to test continuity", "multimeter beep test", "check if a wire is broken", "measure resistance of a resistor in circuit",
   "ohms mode on the meter", "is this fuse blown"],
 "scope_probe": ["how do i connect an oscilloscope probe", "oscilloscope probe compensation", "scope ground clip where does it go",
   "my scope trace looks distorted", "x10 probe setting scope"],
 "logic_levels": ["can i connect 5v output to a 3.3v input", "esp32 with 5v sensor", "do i need a level shifter", "3.3v logic vs 5v logic",
   "arduino to raspberry pi gpio voltage", "is it ok to wire a 5v pin into an esp32 pin"],
 "pull_up": ["what is a pull up resistor", "button input floating why pull up", "pull down vs pull up resistor value", "i2c pull up resistor values",
   "why does my input read random values"],
 "flyback": ["do i need a diode across a relay coil", "motor kickback protection", "flyback diode placement", "how to protect transistor from relay coil spike",
   "inductive load diode"],
 "datasheet": ["where do i find the datasheet", "what is the maximum voltage of the {p}", "pinout of the {p}", "absolute maximum ratings explained", "datasheet for {p}"],
 "ewaste": ["where do i throw old batteries", "dispose of burnt components", "e waste bin for circuit boards", "how to dispose of lithium cells",
   "can i put solder waste in the normal bin", "where do broken resistors go", "old batteries and dead boards which bin"],
 "soldering_tips": ["how do i solder a joint", "tips for soldering through hole parts", "my solder joint is dull and balled up",
   "how to tin the soldering iron tip", "cold solder joint fix", "solder will not stick to the pad"],
 "general": ["how do i set up the breadboard", "how to wire up the power rails", "how do i use the bench power supply", "set the current limit on the supply",
   "how to strip wire", "how do i test my circuit step by step"],
 "greeting": ["hello", "hi iqo", "hey robot", "good morning", "are you there", "who are you", "thanks", "thank you", "what can you do", "help"],
}
FILLER = ["", "", "", " please", " quickly", " robot", " iqo", " ?"]


def _noise(s, rng):
    if rng.random() < 0.35 and len(s) > 6:
        i = rng.randrange(1, len(s) - 1)
        s = s[:i] + (s[i + 1] + s[i] if rng.random() < .5 else "") + s[i + 2:]
    if rng.random() < 0.2:
        s = s.upper()
    if rng.random() < 0.3:
        s = s.replace("?", "").replace(",", "")
    return (s + rng.choice(FILLER)).strip()


def _render(tid, rng):
    b, m, v = rng.choice(BAT), rng.choice(MAINS), rng.choice(MVERB)
    if tid == "battery_fire":          return rng.choice(ACTIVE_BF).format(b=b, h=rng.choice(BHAZ))
    if tid == "battery_fire_concept":  return rng.choice(CONCEPT_BF).format(b=b)
    if tid == "battery_short":         return rng.choice(ACTIVE_BS).format(b=b)
    if tid == "battery_short_concept": return rng.choice(CONCEPT_BS).format(b=b)
    if tid == "live_mains_work":       return rng.choice(ACTIVE_LM).format(m=m, v=v)
    if tid == "live_mains_work_concept": return rng.choice(CONCEPT_LM).format(m=m, v=v)
    return rng.choice(STATIC[tid]).format(r=rng.choice([100, 220, 470, 1000, 4700]), v=rng.choice([3, 5, 9, 12, 24]),
                                          i=rng.choice([5, 10, 20]), r1=rng.choice([1, 2.2, 4.7, 10]),
                                          r2=rng.choice([1, 2.2, 4.7, 10]), c=rng.choice([1, 10, 100, 470]),
                                          p=rng.choice(PARTS))


def generate(per_topic=700, seed=0):
    rng = random.Random(seed)
    X, y_safe, y_arm, y_int, y_top = [], [], [], [], []
    for tid, d in T.items():
        for _ in range(per_topic):
            X.append(_noise(_render(tid, rng), rng))
            y_safe.append(SAFETY.index(d["safety"]))
            y_arm.append(ARM_CLASSES.index(d["zone"]))
            y_int.append(INTENTS.index(d["intent"]))
            y_top.append(TOPIC_INDEX[tid])
    idx = list(range(len(X)))
    rng.shuffle(idx)
    pick = lambda L: [L[i] for i in idx]
    return pick(X), pick(y_safe), pick(y_arm), pick(y_int), pick(y_top)


if __name__ == "__main__":
    X, *_ = generate(3)
    print(len(X), "samples; e.g.", X[:6])
