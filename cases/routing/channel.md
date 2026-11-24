+++
title = "Twelve tracks through a neck that fits twelve"
tags = ["routing", "density", "outline"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed"]

[board]
outline = [[0, 0], [13, 0], [13, 15.85], [17, 15.85], [17, 0], [30, 0], [30, 34], [17, 34], [17, 18.15], [13, 18.15], [13, 34], [0, 34]]

[[part]]
ref = "J1"
pattern = "HDR_1x12_2.54"
at = [3, 3.03]
rotation = 90
[[part]]
ref = "J2"
pattern = "HDR_1x12_2.54"
at = [27, 3.03]
rotation = 90

[[net]]
name = "D1"
pins = ["J1.1", "J2.1"]
[[net]]
name = "D2"
pins = ["J1.2", "J2.2"]
[[net]]
name = "D3"
pins = ["J1.3", "J2.3"]
[[net]]
name = "D4"
pins = ["J1.4", "J2.4"]
[[net]]
name = "D5"
pins = ["J1.5", "J2.5"]
[[net]]
name = "D6"
pins = ["J1.6", "J2.6"]
[[net]]
name = "D7"
pins = ["J1.7", "J2.7"]
[[net]]
name = "D8"
pins = ["J1.8", "J2.8"]
[[net]]
name = "D9"
pins = ["J1.9", "J2.9"]
[[net]]
name = "D10"
pins = ["J1.10", "J2.10"]
[[net]]
name = "D11"
pins = ["J1.11", "J2.11"]
[[net]]
name = "D12"
pins = ["J1.12", "J2.12"]
+++

Two halves of a board, each 13 × 34 mm, joined by a neck 4 mm long and 2.3 mm wide at mid
height: the outline is a 30 × 34 mm rectangle with a 4 mm wide notch cut into it from the south
edge up to y = 15.85 and another from the north edge down to y = 18.15, both between x = 13 and
x = 17. A 1×12 header stands on each half, J1 with pin 1 at (3, 3.03) and J2 with pin 1 at
(27, 3.03), both with their pins running toward +y. Pin *n* of one is joined to pin *n* of the
other.

Every net crosses the neck. With copper 0.3 mm from each edge, the neck has 1.7 mm for tracks: six
of 0.15 mm with 0.15 mm between them take 1.65. So six cross on each layer, at the least width and
the least clearance, and the twelve nets fit with 0.05 mm to spare.
