"""Synthetic training-data generator (templates x slot synonyms x noise).
No downloads. Replace/extend with real student queries when you have them."""
import random
from topics import T, TOPIC_INDEX
from config import SAFETY, INTENTS, ARM_CLASSES

BLEACH = ["bleach", "sodium hypochlorite", "naocl", "clorox", "household bleach"]
AMMONIA = ["ammonia", "nh3", "ammonium hydroxide", "nh4oh"]
ACIDS = ["hcl", "hydrochloric acid", "sulfuric acid", "h2so4", "vinegar", "an acid"]
CYAN = ["cyanide", "kcn", "sodium cyanide", "nacn"]
NITRIC = ["nitric acid", "hno3", "conc nitric acid"]
ORG = ["acetone", "ethanol", "organic solvent", "methanol", "ether", "alcohol", "turpentine"]
ALKALI = ["sodium metal", "potassium metal", "a piece of sodium", "na metal", "k metal", "alkali metal"]
WATER = ["water", "h2o", "tap water"]
CONC = ["concentrated", "conc", "98%", "96%", "fuming", "neat", "18m"]
SACID = ["sulfuric acid", "h2so4", "hydrochloric acid", "nitric acid"]
CHEMS = ["sulfuric acid", "naoh", "hcl", "acetone", "ethanol", "nitric acid", "ammonia", "phenolphthalein", "bleach"]
WASTES = ["acid waste", "base waste", "titration solution", "used reagent", "leftover naoh", "organic solvent"]

ACTIVE_T = ["i just mixed {a} and {b}", "i am adding {a} to {b}", "mixing {a} with {b} now",
            "we poured {a} into the {b}", "can i mix {a} and {b}", "{a} spilled into {b}",
            "adding {b} to {a} in the beaker", "combine {a} and {b} in a flask", "oops mixed {a} with {b}",
            "help i added {a} to {b}"]
CONCEPT_T = ["what happens if you mix {a} and {b}", "why is mixing {a} and {b} dangerous",
             "explain the reaction between {a} and {b}", "is it dangerous to combine {a} and {b}",
             "why cant {a} be stored with {b}", "theory: {a} plus {b} hazards",
             "what if we merge {a} and {b}", "how does {a} react with {b}"]
PAIRS = {  # topic -> (list A, list B)
    "bleach_ammonia": (BLEACH, AMMONIA), "bleach_acid": (BLEACH, ACIDS),
    "cyanide_acid": (CYAN, ACIDS), "nitric_organics": (NITRIC, ORG),
    "alkali_water": (ALKALI, WATER),
}

STATIC = {
 "titr_meniscus": ["how do i read the meniscus", "where do i read the burette", "reading the burette volume",
   "what is the meniscus", "burette reading tips eye level", "how to read volume on burette", "read bottom of meniscus?"],
 "titr_overshoot": ["i overshot the endpoint it is dark magenta", "the solution turned dark pink too much naoh",
   "passed the endpoint what now", "endpoint overshoot magenta", "my titration went too far", "indicator is deep magenta"],
 "titr_indicator": ["which indicator for hcl and naoh", "what indicator for strong acid strong base titration",
   "why phenolphthalein", "indicator for titration endpoint", "ph range of phenolphthalein", "methyl orange or phenolphthalein"],
 "h3o_so4": ["what if we merge h3o and so4", "mix hydronium and sulfate", "h3o+ plus so4 2-",
   "what happens when hydronium meets sulfate ions", "combine h3o+ and so4^2- in solution",
   "hydronium sulfate conjugate", "is h3o and so4 dangerous", "h3o + so4 equilibrium"],
 "acidbase_dilute": ["can i mix hcl and naoh for the titration", "what happens when 0.1 m hcl meets 0.1 m naoh",
   "neutralization of dilute acid with base", "mix acetic acid and naoh", "hcl plus naoh gives what",
   "dilute hcl with dilute naoh safe?", "is neutralising dilute acid and base safe"],
 "no_goggles": ["i'm working without goggles", "no goggles on", "camera sees no safety glasses", "where are the goggles",
   "i forgot my goggles", "can i skip goggles for a quick pour", "safety glasses missing", "do i need goggles"],
 "stoich": ["how many moles in {n} g of naoh", "calculate molarity of hcl from titration volumes", "c1v1 = c2v2 help",
   "stoichiometry of acid base reaction", "how much naoh to neutralize {n} ml 0.1 m hcl", "convert grams to moles",
   "find concentration of unknown acid", "limiting reagent calculation"],
 "msds": ["show msds for {c}", "what are the ghs hazards of {c}", "is {c} corrosive", "what ppe for {c}",
   "hazard statements for {c}", "safety data sheet {c}", "ghs pictogram on {c}", "cas number of {c}"],
 "waste": ["where do i dispose of the {w}", "how do i get rid of leftover {w}", "chemical waste bin for {w}",
   "can i pour {w} down the sink", "waste carboy disposal", "dispose overshot titration solution", "where does the waste go"],
 "general": ["how do i set up the burette", "how do i clean glassware", "how do i prepare a standard solution",
   "what is the lab procedure for dilution", "how do i use a pipette", "how to rinse the burette",
   "how to weigh reagent on balance", "how do i label a flask"],
 "greeting": ["hello", "hi iqo", "hey robot", "good morning", "are you there", "who are you", "thanks",
   "thank you", "what can you do", "help"],
 "splash": ["acid splashed on my arm", "i got chemical in my eye", "naoh spilled on my hand", "splash on my skin",
   "chemicals in my eyes help", "burning on my skin from acid", "reagent splashed on face", "spilled acid on my glove and skin"],
}
WA_ACTIVE = ["i poured water into {m} {s}", "adding water to {m} {s}", "water into the {m} {s} bottle",
             "just added water to {m} {s}"]
WA_CONCEPT = ["why cant you add water to {m} {s}", "what happens when water is added to {m} {s}",
              "explain why acid goes into water not {s}", "theory of diluting {m} {s}"]
CONC_T = ["how do i dilute {m} {s}", "i need to handle {m} {s}", "pouring {m} {s} for dilution",
          "measuring {m} {s} at the bench", "prepare a solution from {m} {s}"]

FILLER = ["", "", "", " please", " quickly", " robot", " iqo", " ?"]


def _noise(s, rng):
    if rng.random() < 0.35 and len(s) > 6:                    # typo
        i = rng.randrange(1, len(s) - 1)
        s = s[:i] + (s[i + 1] + s[i] if rng.random() < .5 else "") + s[i + 2:]
    if rng.random() < 0.2:
        s = s.upper()
    if rng.random() < 0.3:
        s = s.replace("?", "").replace(",", "")
    return (s + rng.choice(FILLER)).strip()


def _render(tid, rng):
    if tid in PAIRS:
        a, b = rng.choice(PAIRS[tid][0]), rng.choice(PAIRS[tid][1])
        t = rng.choice(ACTIVE_T).format(a=a, b=b)
        return t
    if tid.endswith("_concept") and tid[:-8] in PAIRS:
        la, lb = PAIRS[tid[:-8]]
        return rng.choice(CONCEPT_T).format(a=rng.choice(la), b=rng.choice(lb))
    if tid == "water_into_acid":
        return rng.choice(WA_ACTIVE).format(m=rng.choice(CONC), s=rng.choice(SACID))
    if tid == "water_into_acid_concept":
        return rng.choice(WA_CONCEPT).format(m=rng.choice(CONC), s=rng.choice(SACID))
    if tid == "conc_acid":
        return rng.choice(CONC_T).format(m=rng.choice(CONC), s=rng.choice(SACID))
    return rng.choice(STATIC[tid]).format(n=rng.choice([2, 4, 5, 10, 25, 40]), c=rng.choice(CHEMS), w=rng.choice(WASTES))


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
