"""Strict chemistry domain gate. Unknown or unrelated questions never reach the Llama brain."""
import re

CHEM = re.compile(r"\b(acid|base|alkali|chemical|chemistry|mole|molar|molarity|ph|poh|titration|titrate|burette|reagent|solvent|bleach|ammonia|cyanide|nitric|sulfuric|hcl|naoh|sds|msds|ghs|goggle|eyewash|waste|reaction|concentration|dilution|meniscus|stoichiometr|titrant|phenolphthalein|organic solvent)\b", re.I)

def is_in_domain(text):
    return bool(CHEM.search(text))

def refusal():
    return "I am the chemistry brain. I only answer trusted chemistry and laboratory-safety questions."
