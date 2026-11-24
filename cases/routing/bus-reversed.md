+++
title = "An eight-bit bus, reversed"
tags = ["routing", "bus", "via"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed"]

[board]
outline = [[0, 0], [20, 0], [20, 24], [0, 24]]

[[part]]
ref = "J1"
pattern = "HDR_1x8_2.54"
at = [3, 3.11]
rotation = 90
[[part]]
ref = "J2"
pattern = "HDR_1x8_2.54"
at = [17, 20.89]
rotation = 270

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

Two 1×8 headers standing face to face on a 20 × 24 mm board: J1 up the west side, pin 1 at
(3, 3.11) and pin 8 at (3, 20.89); J2 down the east side, turned the other way, pin 1 at
(17, 20.89) and pin 8 at (17, 3.11). Pin *n* of one is joined to pin *n* of the other, so the
straight route of every net crosses that of every other.

Two layers are enough, and the headers' own holes change layer for nothing. The vias are
reported.
