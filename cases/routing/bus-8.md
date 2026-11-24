+++
title = "An eight-bit bus round a corner"
tags = ["routing", "bus"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed", "layers"]
copper = ["F.Cu"]

[board]
outline = [[0, 0], [31, 0], [31, 31], [0, 31]]

[[part]]
ref = "J1"
pattern = "HDR_1x8_2.54"
at = [10, 3]
rotation = 0
[[part]]
ref = "J2"
pattern = "HDR_1x8_2.54"
at = [3, 10]
rotation = 90

[[net]]
name = "D0"
pins = ["J1.1", "J2.1"]
[[net]]
name = "D1"
pins = ["J1.2", "J2.2"]
[[net]]
name = "D2"
pins = ["J1.3", "J2.3"]
[[net]]
name = "D3"
pins = ["J1.4", "J2.4"]
[[net]]
name = "D4"
pins = ["J1.5", "J2.5"]
[[net]]
name = "D5"
pins = ["J1.6", "J2.6"]
[[net]]
name = "D6"
pins = ["J1.7", "J2.7"]
[[net]]
name = "D7"
pins = ["J1.8", "J2.8"]
+++

Two 1×8 headers at right angles on a 31 × 31 mm board: J1 along the south edge, pin 1 at
(10, 3) and pin 8 at (27.78, 3); J2 up the west edge, pin 1 at (3, 10) and pin 8 at (3, 27.78).
Pin *n* of one is joined to pin *n* of the other. All tracks are on the top layer, and there are
no vias.

The pin 1s are nearest the corner, so the bus turns it as eight nested bends with no crossing.
