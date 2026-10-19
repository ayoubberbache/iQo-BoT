"""Stage 1: deterministic zero-tolerance guardrail (runs before any neural net).
Keyword-gated, pre-compiled regexes -> sub-millisecond on a Pi 4 class CPU.
Deliberately conservative: when in doubt about a lethal combination, alarm."""
import re
from config import normalize

R = lambda p: re.compile(p)

BLEACH = R(r"bleach|hypochlorite|naocl|clorox")
AMMONIA = R(r"ammonia|\bnh3\b|nh4oh")
ACID = R(r"acid|\bhcl\b|h2so4|hno3|vinegar")
CYAN = R(r"cyanide|\bkcn\b|\bnacn\b")
NITRIC = R(r"nitric|hno3")
ORG = R(r"acetone|ethanol|methanol|alcohol|organic|solvent|\bether\b|turpentine")
ALKALI = R(r"(sodium|potassium|\bna\b|\bk\b)\s+(metal|piece|chunk|pellet)|alkali metal|a piece of (sodium|potassium)")
WATER = R(r"\bwater\b|\bh2o\b")
CONC = R(r"conc\b|concentrated|\b9[6-8]\s?%|fuming|\bneat\b|\b18\s?m\b|glacial")
STRONG_ACID = R(r"sulfuric|sulphuric|h2so4|hydrochloric|\bhcl\b|nitric|hno3|\bacid\b")
W_INTO_A = R(r"\bwater\b[^.]{0,30}\b(in|into|to|onto)\b[^.]{0,30}(acid|h2so4|\bhcl\b|hno3)")
A_INTO_W = R(r"(acid|h2so4|\bhcl\b|hno3)[^.]{0,30}\b(in|into|to|onto)\b[^.]{0,15}\bwater\b")
CONC_VERB = R(r"dilut|handl|pour|measur|transfer|\buse\b|prepar|open|bottle")
SPLASH = R(r"(splash|spill|got|burn|drip|hit)\w*[^.]{0,30}\b(skin|eyes?|face|arm|hand|hands|glove)\b"
           r"|\b(skin|eyes?|face)\b[^.]{0,25}(splash|burn|acid|chemical|naoh)")
ACTIVE = R(r"\b(just|already|accidentally|oops|spilled|poured|mixed|adding|pouring|help|now)\b")
EDU = R(r"\b(why|what if|what happens|explain|theory|theoretical|how does|dangerous|hazard|"
        r"reaction between|stored?|storing|rule)\b")

# (gate substrings, test, critical topic, concept topic)
def _pair(a, b):
    return lambda q: bool(a.search(q) and b.search(q))

RULES = [
    ("splash", ("skin", "eye", "face", "arm", "hand", "glove"),
     lambda q: bool(SPLASH.search(q)), "splash", "splash"),
    ("bleach_ammonia", ("bleach", "hypochlorite", "naocl", "clorox"),
     _pair(BLEACH, AMMONIA), "bleach_ammonia", "bleach_ammonia_concept"),
    ("bleach_acid", ("bleach", "hypochlorite", "naocl", "clorox"),
     _pair(BLEACH, ACID), "bleach_acid", "bleach_acid_concept"),
    ("cyanide_acid", ("cyanide", "kcn", "nacn"),
     _pair(CYAN, ACID), "cyanide_acid", "cyanide_acid_concept"),
    ("nitric_organics", ("nitric", "hno3"),
     _pair(NITRIC, ORG), "nitric_organics", "nitric_organics_concept"),
    ("alkali_water", ("sodium", "potassium", "alkali", " na ", " k "),
     _pair(ALKALI, WATER), "alkali_water", "alkali_water_concept"),
]


def _water_acid(q):
    return bool(W_INTO_A.search(q)) and not A_INTO_W.search(q)


def check(text: str, goggles=None):
    """Return a topic id (see topics.py) or None.
    goggles: None=unknown, True/False from overhead camera PPE detector."""
    q = " " + normalize(text) + " "
    active = bool(ACTIVE.search(q))
    edu = bool(EDU.search(q)) and not active
    warn = None

    for _name, gate, test, crit, concept in RULES:
        if any(g in q for g in gate) and test(q):
            if _name == "splash":
                return crit                      # life-safety, never downgraded
            return concept if edu else crit

    if "water" in q and _water_acid(q):
        if edu:
            return "water_into_acid_concept"
        return "water_into_acid" if CONC.search(q) else "conc_acid"

    if goggles is False:
        return "no_goggles"                      # camera flag -> amber + goggle rack

    if CONC.search(q) and STRONG_ACID.search(q) and CONC_VERB.search(q):
        warn = "conc_acid"                       # concentration-aware severity
    return warn
