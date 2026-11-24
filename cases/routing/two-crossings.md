+++
title = "Two nets that cross"
tags = ["routing", "via"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed"]

[board]
outline = [[0, 0], [15, 0], [15, 15], [0, 15]]

[[part]]
ref = "R1"
pattern = "R_0603"
at = [3, 3]
rotation = 0
[[part]]
ref = "R2"
pattern = "R_0603"
at = [12, 3]
rotation = 0
[[part]]
ref = "R3"
pattern = "R_0603"
at = [12, 12]
rotation = 0
[[part]]
ref = "R4"
pattern = "R_0603"
at = [3, 12]
rotation = 0

[[net]]
name = "A"
pins = ["R1.2", "R3.1"]
[[net]]
name = "B"
pins = ["R2.1", "R4.2"]
+++

Four 0603 resistors at the corners of a square on a 15 × 15 mm board, each lying along x with
pad 1 to the left: R1 at (3, 3), R2 at (12, 3), R3 at (12, 12) and R4 at (3, 12). Net A joins R1's
pad 2 to R3's pad 1, and net B joins R2's pad 1 to R4's pad 2: the two diagonals, between the
inner pads. The other four pads are left unconnected.

The straight routes cross. One net changes layer, or goes round the end of the other between a
resistor's pads, or round the resistor. Any of these passes; the vias are reported.
