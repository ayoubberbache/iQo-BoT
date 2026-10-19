"""Strict electronics domain gate. Unknown or unrelated questions never reach the Llama brain."""
import re

ELEC = re.compile(r"\b(electr|circuit|voltage|current|resistor|resistance|capacitor|inductor|diode|led|transistor|mosfet|arduino|esp32|raspberry|gpio|ohm|watt|power supply|battery|lithium|lipo|solder|multimeter|oscilloscope|datasheet|logic|fuse|esd|motor|relay|wire|mains|ac|dc|pcb|sensor|voltage divider)\w*\b", re.I)

def is_in_domain(text):
    return bool(ELEC.search(text))

def refusal():
    return "I am the electronics brain. I only answer trusted electronics and bench-safety questions."
