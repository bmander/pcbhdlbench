+++
title = "An RC low-pass filter"
tags = ["passives"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline"]

[board]
outline = [[0, 0], [15, 0], [15, 10], [0, 10]]

[[part]]
ref = "J1"
pattern = "HDR_1x3_2.54"
[[part]]
ref = "R1"
pattern = "R_0603"
value = "10 kΩ"
[[part]]
ref = "C1"
pattern = "C_0603"
value = "100 nF"

[[net]]
name = "IN"
pins = ["J1.1", "R1.1"]
[[net]]
name = "GND"
pins = ["J1.2", "C1.2"]
[[net]]
name = "OUT"
pins = ["R1.2", "C1.1", "J1.3"]
+++

A 10 kΩ resistor from IN to OUT and a 100 nF capacitor from OUT to GND. A 1×3 header carries IN,
GND and OUT on pins 1, 2 and 3. The board is a 15 × 10 mm rectangle with one corner at the origin.

GND is the header's middle pin, so OUT or IN passes it: between the header's pads, round the
header, or on the other layer. The first case with a net of three pins.
