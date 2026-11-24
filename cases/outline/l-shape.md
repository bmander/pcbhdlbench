+++
title = "An L-shaped board"
tags = ["outline", "mechanical"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed"]

[board]
outline = [[0, 0], [40, 0], [40, 10], [10, 10], [10, 30], [0, 30]]

[[part]]
ref = "J1"
pattern = "HDR_1x8_2.54"
at = [20, 5]
rotation = 0
[[part]]
ref = "J2"
pattern = "HDR_1x8_2.54"
at = [5, 10]
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
+++

An L of two arms 10 mm wide: one 40 mm long along the south edge and one 30 mm long up the west
edge, sharing the corner at the origin. A 1×8 header lies along the middle of each arm: J1 with
pin 1 at (20, 5) and pin 8 at (37.78, 5), J2 with pin 1 at (5, 10) and pin 8 at (5, 27.78). Pin
*n* of one is joined to pin *n* of the other.

Eight nets go round the inside corner, each passing the pins nearer the corner than its own, in
arms with under 4 mm either side of the header. The first case whose outline is not a rectangle:
a track that cuts the corner is outside the board.
