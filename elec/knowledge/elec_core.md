# IQO electronics notes (retrieval corpus)

Ohm's law: voltage equals current times resistance, V = I R. Power is P = V I, which also equals I squared R and V squared over R. Resistors must be rated above the power they dissipate, with a safety margin of about two times.

LED series resistor: R = (Vsupply - Vforward) / I. Typical forward voltages are about 1.8 to 2.2 V for red, about 2 to 3 V for green and yellow, and about 3 to 3.4 V for blue and white. Indicator LEDs usually run at 5 to 20 mA. Example: 5 V supply, red LED at 2 V and 10 mA gives 300 ohms, so use the next standard value, 330 ohms.

Standard E12 resistor values per decade: 10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68 and 82. Resistor colour code digits: black 0, brown 1, red 2, orange 3, yellow 4, green 5, blue 6, violet 7, grey 8, white 9. For four bands the third band is the multiplier and the fourth is tolerance, gold 5 percent and silver 10 percent. Brown black red is 10 times 100, which is 1 kilo ohm.

Voltage divider: Vout = Vin times R2 divided by R1 plus R2. The divider only works well when the load draws much less current than flows through R1 and R2, so it is suitable for signals and not for powering loads.

RC circuits: the time constant tau equals R times C. A charging capacitor reaches 63 percent of the supply after one tau and more than 99 percent after five tau. The cutoff frequency of a first order RC filter is 1 divided by 2 pi R C.

Electrolytic capacitors are polarised. The stripe marks the negative lead. Reverse polarity or exceeding the voltage rating can make them overheat, vent or burst. Choose a working voltage at least 1.5 to 2 times the circuit voltage. A bulging or leaking capacitor must be replaced.

Discharging capacitors: switch off and unplug first, then discharge through a resistor of a few kilo ohms with a suitable power rating, and confirm near zero volts with a multimeter. Never short a charged capacitor with a screwdriver because the spark and current can damage the capacitor and injure you.

Decoupling: place a 100 nF ceramic capacitor as close as possible to every integrated circuit supply pin to supply fast current spikes and reduce noise.

Pull-up and pull-down resistors keep a digital input at a defined level when nothing drives it. Typical values are 4.7 to 10 kilo ohms. I2C lines need pull-ups to the supply, commonly 4.7 kilo ohms.

Logic levels: a 3.3 V input such as an ESP32 or Raspberry Pi GPIO is not 5 V tolerant. Use a level shifter or a resistor divider when a 5 V output drives it. An Arduino Uno pin should source about 20 mA, with 40 mA as the absolute maximum.

Flyback diode: connect a diode across a relay or motor coil, cathode to the positive side, so the inductive voltage spike at switch-off is clamped and cannot damage the driving transistor.

Transistor switch: for a bipolar transistor used as a switch, set the base current to roughly one tenth of the collector current to saturate it, and add a base resistor. For a MOSFET, use a logic level type when driving from 3.3 V or 5 V logic.

Multimeter: for voltage set the dial to volts, DC or AC, and place the probes across the component in parallel. For current break the circuit and place the meter in series using the current socket, and never connect it across a voltage source in current mode. For resistance and continuity power the circuit off first. A beep means low resistance.

Oscilloscope: compensate the probe on the calibration output, use the x10 setting for most work, and connect the ground clip only to circuit ground. Never connect scope ground to a live mains point, because the scope earth is connected to mains earth.

Bench power supply: set the current limit before connecting the circuit, start at a low voltage, and increase slowly while watching the current. A current limit protects wires and parts from a short circuit.

Voltage hazard levels: mains voltage of 120 or 230 V can be lethal. Voltages above about 50 V AC or 120 V DC are generally treated as hazardous. Low voltage such as 5 V or 12 V is usually low risk to touch, but a short circuit on a battery or supply can still cause burns and fires.

Working near mains: unplug the equipment, wait for capacitors to discharge, verify with a meter, and never work alone. Use an isolation transformer, a residual current device, and the one hand rule when probing is unavoidable and your instructor has approved it.

Lithium polymer and lithium ion cells: nominal 3.7 V per cell, fully charged 4.2 V, storage about 3.8 V per cell, and do not discharge below about 3.0 V per cell. Charge with a balance charger at the rated current, supervised, in a fire resistant bag. Never charge a swollen, punctured or damaged cell, and never short the terminals.

Soldering: leaded solder melts at about 183 degrees Celsius and lead free SAC305 at about 217 degrees. Heat the pad and lead together, feed solder onto the joint, and use a fume extractor and safety glasses. A good joint is shiny and cone shaped, a dull balled joint is a cold joint.

Soldering burns: cool the burn under running water for twenty minutes, do not use ice or creams, and seek medical help for anything large or deep. Flux fumes irritate the lungs, so use extraction.

Electrostatic discharge: wear a wrist strap with a one mega ohm series resistor, work on an antistatic mat, and store chips in antistatic bags. Static discharge can damage CMOS parts without any visible sign.

Fuses: choose a fuse rating a little above normal operating current, about 1.25 to 1.5 times, and below the cable and circuit limit. A fuse that blows repeatedly means there is a fault to find, not a bigger fuse to fit.

Electronic waste: put boards and components in the e-waste bin, keep batteries in a separate collection box, and never put lithium cells in general waste. Collect lead solder offcuts for hazardous waste disposal.
