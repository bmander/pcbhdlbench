+++
title = "A voltage divider"
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
ref = "R2"
pattern = "R_0603"
value = "10 kΩ"

[[net]]
name = "VIN"
pins = ["J1.1", "R1.1"]
[[net]]
name = "VOUT"
pins = ["R1.2", "R2.1", "J1.2"]
[[net]]
name = "GND"
pins = ["R2.2", "J1.3"]
+++

Two 10 kΩ 0603 resistors in series between VIN and GND, their midpoint brought out as VOUT. A
1×3 header at 2.54 mm pitch carries VIN, VOUT and GND on pins 1, 2 and 3. The board is a 15 × 10 mm
rectangle with one corner at the origin.
