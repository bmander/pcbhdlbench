+++
title = "A track for three amps"
tags = ["power", "width"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "width"]

[[width]]
path = ["J1.1", "F1.1"]
min = 1.37
neck = 2.0

[[width]]
path = ["F1.2", "Q1.3"]
min = 1.37
neck = 2.0

[[width]]
path = ["Q1.2", "J2.1"]
min = 1.37
neck = 2.0

[[width]]
path = ["J2.2", "J1.2"]
min = 1.37
neck = 2.0

[board]
outline = [[0, 0], [40, 0], [40, 20], [0, 20]]

[[part]]
ref = "J1"
pattern = "TERM_1x2_5.00"
[[part]]
ref = "F1"
pattern = "FUSE_1206"
value = "4 A"
[[part]]
ref = "Q1"
pattern = "SOT-23"
value = "P-channel MOSFET"
[[part]]
ref = "R1"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "J2"
pattern = "TERM_1x2_5.00"

[[net]]
name = "VIN"
pins = ["J1.1", "F1.1"]
[[net]]
name = "VFUSED"
pins = ["F1.2", "Q1.3"]
[[net]]
name = "VOUT"
pins = ["Q1.2", "J2.1"]
[[net]]
name = "GND"
pins = ["J1.2", "J2.2", "R1.2"]
[[net]]
name = "GATE"
pins = ["Q1.1", "R1.1"]
+++

A supply input with a fuse and reverse-polarity protection, for 3 A, on a 40 × 20 mm board.
The supply comes in on a two-way screw terminal J1, positive on pin 1 and ground on pin 2. It
passes a 1206 fuse F1, then a P-channel MOSFET Q1 in SOT-23 (1 gate, 2 source, 3 drain), drain
toward the fuse and source toward the load, and leaves on a second terminal J2, positive on pin 1
and ground on pin 2. A 100 kΩ resistor R1 holds the gate at ground, which turns the MOSFET on when
the supply is the right way round.

Three amps on 1 oz outer copper, for a 10 °C rise, want a track 1.37 mm wide by IPC-2221. So the
whole way of the current is at least that wide: from J1 to the fuse, from the fuse to the drain,
from the source to J2, and the return from J2's ground to J1's. A track may be narrower only where
it meets a pad too narrow for it, within 2 mm of the pad's centre; a pour counts as wide. The gate
and its resistor carry nothing, and may be as narrow as the rules allow.
