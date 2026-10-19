"""
Deterministic Safety Guardrail & Chemical Knowledge Engine for IQO Bot
Implements sub-millisecond evaluation for laboratory safety and chemical concept routing.
Strictly adheres to 16x2 character hardware LCD screen limits.
"""

import re
from typing import Optional, Dict, Any


def format_lcd_16x2(line1: str, line2: str) -> str:
    """Strictly formats and pads text to fit a 16x2 hardware LCD screen."""
    l1 = line1.strip()[:16].ljust(16)
    l2 = line2.strip()[:16].ljust(16)
    return f"{l1}\n{l2}"


class DeterministicSafetyGuard:
    """
    Sub-millisecond deterministic safety validator.
    Evaluates life-safety hazards and educational ionic equilibrium inquiries.
    """

    RULES = [
        # 1. Chemical Concept & Ionic Equilibrium (H3O+ and SO4(2-))
        {
            "id": "HYDRONIUM_SULFATE_EQUILIBRIUM",
            "regex": r"(merge|mix|combine|react|between|add)\s+.*(h3o|hydronium).*(so4|sulfate)|(h3o|hydronium)\s+.*(and|\+|\&)\s+.*(so4|sulfate)",
            "safety_level": 1,  # INFO
            "arm_target": 7,    # BENCH_WORKSTATION
            "intent": 1,        # REAGENT_COMPATIBILITY
            "led_color": "BLUE_INFO",
            "speech_response": "Combining hydronium (H3O+) and sulfate (SO4 2-) ions represents aqueous sulfuric acid in thermodynamic equilibrium. In dilute solution, this is a standard conjugate acid-base system forming hydrogen sulfate (HSO4-) and sulfuric acid. Non-hazardous at analytical concentrations; follow standard acid handling protocols.",
            "lcd_line1": "H3O+ + SO4(2-)  ",
            "lcd_line2": "[INFO] H2SO4(AQ) "
        },
        # 2. Critical: Water poured into concentrated acid
        {
            "id": "WATER_INTO_ACID",
            "regex": r"(water\s+(in|into|to)\s+(concentrated\s+)?(acid|sulfuric|h2so4|hydrochloric|hcl|nitric|hno3)|dilute\s+(acid|sulfuric|h2so4|hcl|hno3)\s+with\s+water\s+directly|pour\s+water\s+into\s+(concentrated\s+)?acid|(add|pour)\s+water\s+(to|into)\s+.*acid)",
            "safety_level": 3,  # CRITICAL
            "arm_target": 2,    # EYEWASH_STATION
            "intent": 2,        # SAFETY_EMERGENCY
            "led_color": "RED_FLASHING",
            "speech_response": "Caution! Never pour water into concentrated acid due to violent exothermic splashing. Always add acid slowly to water.",
            "lcd_line1": "DANGER: WTR->ACID",
            "lcd_line2": "[CRIT] SPLATTER "
        },
        # 3. Critical: Bleach and Ammonia
        {
            "id": "BLEACH_AND_AMMONIA",
            "regex": r"(bleach\s+(and|with|\+)\s+ammonia|naocl\s+(and|with|\+)\s+nh3|ammonia\s+(and|with|\+)\s+bleach|mix\s+bleach\s+with\s+ammonium)",
            "safety_level": 3,
            "arm_target": 3,    # FUME_HOOD
            "intent": 2,
            "led_color": "RED_FLASHING",
            "speech_response": "Critical safety hazard! Never mix bleach with ammonia. This reaction generates lethal chloramine gases. Evacuate immediately.",
            "lcd_line1": "BLEACH + NH3 HAZ",
            "lcd_line2": "[CRIT] CHLORAMIN"
        },
        # 4. Critical: Bleach and Acid
        {
            "id": "BLEACH_AND_ACID",
            "regex": r"(bleach\s+(and|with|\+)\s+(acid|hydrochloric|hcl|vinegar)|acid\s+(and|with|\+)\s+bleach|naocl\s+(and|with|\+)\s+hcl)",
            "safety_level": 3,
            "arm_target": 3,    # FUME_HOOD
            "intent": 2,
            "led_color": "RED_FLASHING",
            "speech_response": "Danger! Mixing bleach with acid liberates deadly chlorine gas. Do not combine these reagents. Use a certified chemical fume hood.",
            "lcd_line1": "BLEACH + ACID   ",
            "lcd_line2": "[CRIT] CL2 GAS  "
        },
        # 5. Critical: Cyanide and Acid
        {
            "id": "CYANIDE_AND_ACID",
            "regex": r"(cyanide.*(acid|hcl|h2so4|hno3)|(acid|hcl|h2so4|hno3).*cyanide|kcn.*acid|nacn.*acid)",
            "safety_level": 3,
            "arm_target": 3,    # FUME_HOOD
            "intent": 2,
            "led_color": "RED_FLASHING",
            "speech_response": "Fatal hazard alert! Cyanide salts combined with acid produce deadly hydrogen cyanide gas. Never mix cyanides with acidic solutions.",
            "lcd_line1": "CYANIDE + ACID  ",
            "lcd_line2": "[CRIT] HCN GAS  "
        },
        # 6. Critical: Nitric and Organic Solvents
        {
            "id": "NITRIC_AND_ORGANIC",
            "regex": r"(nitric\s+(acid|hno3)\s+(and|with|\+)\s+(ethanol|acetone|alcohol|organic)|(ethanol|acetone)\s+(and|with|\+)\s+nitric)",
            "safety_level": 3,
            "arm_target": 3,    # FUME_HOOD
            "intent": 2,
            "led_color": "RED_FLASHING",
            "speech_response": "Severe explosion risk! Nitric acid reacts violently with organic solvents. Do not mix nitric acid with alcohols or ketones.",
            "lcd_line1": "HNO3 + ORGANIC  ",
            "lcd_line2": "[CRIT] EXPLOSION"
        },
        # 7. Critical: Alkali Metals and Water
        {
            "id": "ALKALI_METAL_WATER",
            "regex": r"((sodium|potassium|alkali\s*metal)\s+.*(in|and|with|\+)\s+water|water\s+(on|to|into)\s+(sodium|potassium)|(put|drop|add)\s+(sodium|potassium)\s+.*water)",
            "safety_level": 3,
            "arm_target": 4,    # CHEMICAL_WASTE
            "intent": 2,
            "led_color": "RED_FLASHING",
            "speech_response": "Critical hazard! Sodium and potassium react explosively with water, releasing self-igniting hydrogen gas. Store under mineral oil only.",
            "lcd_line1": "NA + H2O HAZARD ",
            "lcd_line2": "[CRIT] H2 FIRE  "
        },
        # 8. Critical: Chemical in Eyes
        {
            "id": "CHEMICAL_IN_EYES",
            "regex": r"(acid\s+in\s+(my\s+)?eye|chemical\s+in\s+(my\s+)?eye|splashed\s+in\s+(my\s+)?eyes?|eyes?\s+burning|reagent\s+in\s+eyes?)",
            "safety_level": 3,
            "arm_target": 2,    # EYEWASH_STATION
            "intent": 2,
            "led_color": "RED_FLASHING",
            "speech_response": "Emergency! Chemical splash to eyes requires immediate continuous flushing at the eyewash station for fifteen minutes. Keep eyelids wide open. Notifying instructor.",
            "lcd_line1": "EYE SPLASH ALERT",
            "lcd_line2": "[CRIT] FLUSH 15M"
        },
        # 9. Critical: Chemical on Skin
        {
            "id": "CHEMICAL_ON_SKIN",
            "regex": r"(acid\s+on\s+(my\s+)?(skin|arm|hand)|base\s+on\s+(my\s+)?(skin|hand|fingers)|spilled\s+acid\s+on\s+my|chemical\s+burn)",
            "safety_level": 3,
            "arm_target": 2,    # EYEWASH_STATION
            "intent": 2,
            "led_color": "RED_FLASHING",
            "speech_response": "Emergency! Immediately wash affected skin under continuous cold running water for fifteen minutes. Remove contaminated clothing.",
            "lcd_line1": "SKIN ACID BURN! ",
            "lcd_line2": "[CRIT] FLUSH 15M"
        },
        # 10. Warning: Prohibited Sink Disposal
        {
            "id": "PROHIBITED_SINK_DISPOSAL",
            "regex": r"(pour\s+(down|in|into)\s+(the\s+)?sink|pour\s+(in|into)\s+(the\s+)?drain|dispose\s+in\s+sink|throw\s+waste\s+down\s+drain)",
            "safety_level": 2,  # WARNING
            "arm_target": 4,    # CHEMICAL_WASTE
            "intent": 6,        # WASTE_DISPOSAL
            "led_color": "AMBER",
            "speech_response": "Notice! Never dispose of chemical reagents or heavy metals down the laboratory sink. Deposit all titration and reaction waste into the designated waste carboy.",
            "lcd_line1": "NO SINK DISPOSAL",
            "lcd_line2": "USE WASTE CARBOY"
        }
    ]

    def __init__(self):
        self.compiled_rules = [
            (r["id"], re.compile(r["regex"], re.IGNORECASE), r)
            for r in self.RULES
        ]

    def evaluate(self, query: str, visual_missing_goggles: bool = False) -> Optional[Dict[str, Any]]:
        # 1. Vision sensor override
        if visual_missing_goggles:
            return {
                "triggered": True,
                "rule_id": "VISION_MISSING_GOGGLES",
                "safety_level": 2,
                "arm_target": 1,  # GOGGLE_RACK
                "intent": 3,      # PPE_VIOLATION
                "led_color": "AMBER",
                "speech_response": "Warning! Camera detects missing safety goggles near chemical reagents. Put on your safety goggles immediately.",
                "lcd_display": format_lcd_16x2("PPE HAZARD:     ", "WEAR GOGGLES NOW"),
                "latency_mode": "DETERMINISTIC_BYPASS"
            }

        # 2. Text regex evaluation
        query_clean = query.strip().lower()
        for rule_id, pattern, rule_data in self.compiled_rules:
            if pattern.search(query_clean):
                return {
                    "triggered": True,
                    "rule_id": rule_id,
                    "safety_level": rule_data["safety_level"],
                    "arm_target": rule_data["arm_target"],
                    "intent": rule_data.get("intent", 2),
                    "led_color": rule_data["led_color"],
                    "speech_response": rule_data["speech_response"],
                    "lcd_display": format_lcd_16x2(rule_data["lcd_line1"], rule_data["lcd_line2"]),
                    "latency_mode": "DETERMINISTIC_BYPASS"
                }

        return None
