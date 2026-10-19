"""Equation and chemistry reference context supplied to the conversational model.
This is retrieval context, not a claim of exhaustive chemistry coverage.
"""

EQUATIONS = """
Core equations:
- Amount of substance: n = m / M
- Molarity: c = n / V, with V in litres
- Dilution: C1 V1 = C2 V2
- General stoichiometry: use balanced-equation mole ratios
- Ideal gas law: PV = nRT
- pH: pH = -log10([H3O+])
- pOH: pOH = -log10([OH-]); at 25 C, pH + pOH = 14.00
- Water autoionization: Kw = [H3O+][OH-]
- Henderson-Hasselbalch: pH = pKa + log10([A-]/[HA])
- Acid dissociation: Ka = [H3O+][A-]/[HA]
- Base dissociation: Kb = [BH+][OH-]/[B]
- Percent yield: yield% = actual yield / theoretical yield * 100
- Beer-Lambert law: A = epsilon * b * c
- Heat: q = m c_specific DeltaT
- Gibbs energy: DeltaG = DeltaH - T DeltaS
- Nernst equation: E = E0 - (RT/nF) ln Q
- Arrhenius equation: k = A exp(-Ea/(RT))
- First-order half-life: t1/2 = ln(2)/k

Titration rules:
- At equivalence, calculate from the balanced reaction, not automatically C1V1=C2V2.
- For a 1:1 reaction only: CaVa = CbVb.
- Convert millilitres to litres before calculating moles.
- Report units, significant figures, and an uncertainty when measurements are supplied.

Safety rules:
- Never invent a compatibility judgment from an incomplete chemical name.
- Concentrated acid is added slowly to water, never water to concentrated acid.
- Never mix bleach with acids or ammonia.
- Treat cyanide plus acid and nitric acid plus organics as emergency hazards.
- For exposure or unknown reactions: stop, isolate, evacuate as appropriate, use the SDS and contact trained emergency personnel.
"""


def context():
    return EQUATIONS.strip()
