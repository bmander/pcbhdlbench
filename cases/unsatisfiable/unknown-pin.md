+++
title = "A net on a pin the part does not have"
tags = ["refusal", "netlist"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["refuse"]
control = "basics/led-resistor"

[board]
outline = [[0, 0], [20, 0], [20, 10], [0, 10]]

[[part]]
ref = "J1"
pattern = "HDR_1x4_2.54"
[[part]]
ref = "R1"
pattern = "R_0603"

[[net]]
name = "A"
pins = ["J1.1", "R1.1"]
[[net]]
name = "B"
pins = ["J1.5", "R1.2"]
+++

A 1×4 header and a 0603 resistor on a 20 × 10 mm board. Net A joins the header's pin 1 to the
resistor's pad 1, and net B joins the header's pin 5 to the resistor's pad 2.

A 1×4 header has no pin 5. The design as written cannot be built, and a toolchain should say so,
not drop the connection and lay out the rest.
