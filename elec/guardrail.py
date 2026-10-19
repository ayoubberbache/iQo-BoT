"""Stage 1 (electronics): deterministic zero-tolerance guardrail, runs before any neural net.
Keyword-gated pre-compiled regexes. Deliberately conservative for life-safety hazards."""
import re
from config import normalize

R = re.compile

BAT = r"(lipo|li-?po|li-?ion|lithium|18650|battery|batteries|cell|pack)"
BAT_HAZ = R(BAT + r"[^.]{0,40}(swoll|swell|puff|bulg|smok|hiss|vent|on fire|catch(es)? fire|caught fire|burning|flame|melt|leak|very hot|getting hot|overheat|too hot)"
            r"|(swoll|puff|smok|hiss|vent|overheat)\w*[^.]{0,25}" + BAT)
BAT_ONLY = R(BAT)
BAT_SHORT = R(r"(shorted|shorting|short[- ]circuit(ed|ing)?|short out|across (the )?(battery )?terminals|both (battery )?terminals|"
              r"positive (to|and|with) negative)")
SMOKE = R(r"smok(e|ing)|burn(t|ing)?\b[^.]{0,15}smell|smell\w* (like )?(burn|burnt|burning)|spark(s|ing)?\b|caught fire|on fire|flames?\b|"
          r"exploded|\b(capacitor|cap)\b[^.]{0,25}(popped|vent(ed|ing)|burst|bang)|popped[^.]{0,20}(smell|smoke)")
SMOKE_OK = R(r"extinguisher")
SOLDER_FUME = R(r"(solder|flux)\w*[^.]{0,20}(smok|fume)|(smok|fume)\w*[^.]{0,20}(solder|flux)")
FIRE_WORDS = R(r"fire|flame|burning smell|burnt smell|spark|explod|popped")
SHOCK = R(r"electric(al)? shock|electrocut|\bzapped\b|\b(got|been|felt|received|get)\b[^.]{0,15}\bshock(ed)?\b|shocked by|"
          r"touch\w*[^.]{0,15}\blive (wire|conductor|terminal|mains)")
MAINS = R(r"\bmains\b|\b(110|115|120|220|230|240)\s?v(ac)?\b|wall (outlet|socket|power)")
MAINS_VERB = R(r"probe|probing|\bopen|repair|\bfix|work(ing)? on|solder|touch|rewire|measur|pok(e|ing)")
MAINS_SAFE = R(r"(?<!without )(?<!not )(unplug|disconnect|isolat|switched off|powered off|power off|de-?energi)")
PLUGGED = R(r"plugged in|powered on|power on|while (it is |its )?on\b|live")
PLUG_VERB = R(r"\bopen|repair|\bfix|solder|replace|probe|probing|inside|pok(e|ing)")
PLUG_OBJ = R(r"power supply|\bpsu\b|smps|charger|adapter|appliance|mains|\bboard\b|transformer")
BURN = R(r"(burn(ed|t)?|touched|grabbed|hot)\b[^.]{0,30}(soldering iron|iron tip|solder|hot tip|\biron\b)|"
         r"(soldering iron|iron tip|hot solder)[^.]{0,30}(burn|burnt|on my)")
VENT = R(r"solder\w*[^.]{0,40}(without|\bno\b|off|forgot)[^.]{0,20}(extract|ventilat|\bfan|fume)|"
         r"(breath\w*|inhal\w*|smell\w*)[^.]{0,20}(flux|solder)|flux fumes|solder(ing)? fumes|"
         r"(solder|flux)\w*[^.]{0,20}smok|smok\w*[^.]{0,20}(solder|flux)")
ACTIVE = R(r"\b(just|already|accidentally|oops|help|now|got|felt|my|our|i'm|im|we're|right now)\b")
EDU = R(r"\b(why|what if|what happens|explain|theory|theoretical|how does|dangerous|hazard|safe|stored?|storing|rule)\b")


def _battery_fire(q): return bool(BAT_HAZ.search(q))
def _battery_short(q): return bool(BAT_ONLY.search(q) and BAT_SHORT.search(q))
def _shock(q): return bool(SHOCK.search(q)) and "static" not in q
def _smoke(q):
    if not SMOKE.search(q) or SMOKE_OK.search(q):
        return False
    return not (SOLDER_FUME.search(q) and not FIRE_WORDS.search(q))      # solder fumes -> ventilation rule
def _live_mains(q):
    if MAINS.search(q) and MAINS_VERB.search(q) and not MAINS_SAFE.search(q):
        return True
    return bool(PLUGGED.search(q) and PLUG_VERB.search(q) and PLUG_OBJ.search(q) and not MAINS_SAFE.search(q))

# (gate substrings, test, critical topic, concept topic or None=fall through to Stage 2)
RULES = [
    (("shock", "electrocut", "zapped", "live wire", "live mains"), _shock, "mains_shock", "voltage_safety"),
    (("lipo", "li-po", "li-ion", "lithium", "18650", "batter", "cell", "pack"), _battery_fire, "battery_fire", "battery_fire_concept"),
    (("lipo", "li-po", "li-ion", "lithium", "18650", "batter", "cell", "pack"), _battery_short, "battery_short", "battery_short_concept"),
    (("mains", "110", "115", "120", "220", "230", "240", "wall", "plugged", "powered", "live", "power on", " on"), _live_mains, "live_mains_work", "live_mains_work_concept"),
    (("smok", "burn", "spark", "fire", "flame", "explod", "popped", "cap", "vent", "burst", "bang"), _smoke, "smoke_burning", None),
]


def check(text: str, goggles=None):
    """Return a topic id (see topics.py) or None. goggles: None/True/False from the overhead camera."""
    q = " " + normalize(text) + " "
    active = bool(ACTIVE.search(q))
    edu = bool(EDU.search(q)) and not active

    for gate, test, crit, concept in RULES:
        if any(g in q for g in gate) and test(q):
            if edu:
                if concept:
                    return concept
                continue
            return crit

    if goggles is False:
        return "no_goggles"                         # camera flag -> amber + goggle rack
    if ("burn" in q or "hot" in q) and BURN.search(q):
        return "soldering_burn"
    if ("solder" in q or "flux" in q) and VENT.search(q):
        return "no_ventilation"
    return None
