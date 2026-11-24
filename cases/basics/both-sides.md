+++
title = "Parts on both sides"
tags = ["passives", "two-sided"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "side"]

[board]
outline = [[0, 0], [20, 0], [20, 10], [0, 10]]

[[part]]
ref = "J1"
pattern = "HDR_1x5_2.54"
[[part]]
ref = "R1"
pattern = "R_0603"
value = "10 kΩ"
side = "bottom"
[[part]]
ref = "R2"
pattern = "R_0603"
value = "10 kΩ"
side = "bottom"
[[part]]
ref = "R3"
pattern = "R_0603"
value = "10 kΩ"
side = "bottom"
[[part]]
ref = "R4"
pattern = "R_0603"
value = "10 kΩ"
side = "bottom"

[[net]]
name = "S1"
pins = ["J1.1", "R1.1"]
[[net]]
name = "S2"
pins = ["J1.2", "R2.1"]
[[net]]
name = "S3"
pins = ["J1.3", "R3.1"]
[[net]]
name = "S4"
pins = ["J1.4", "R4.1"]
[[net]]
name = "VCC"
pins = ["J1.5", "R1.2", "R2.2", "R3.2", "R4.2"]
+++

A 1×5 header on the top side: four signals on pins 1 to 4 and VCC on pin 5. Four 10 kΩ 0603
pull-ups, R1 to R4, on the bottom side, R*n* from signal *n* to VCC. The board is a 20 × 10 mm
rectangle.

The case says which side each part is on, and the grading checks it. A courtyard is on its
part's side of the board, so a resistor may stand under the header, clear of its pins' copper.
