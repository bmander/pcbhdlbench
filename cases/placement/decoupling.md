+++
title = "Decoupling capacitors at their pins"
tags = ["placement", "power"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "near"]
[[near]]
from = "C1.1"
to = "U1.4"
max = 2.0
[[near]]
from = "C2.1"
to = "U1.12"
max = 2.0
[[near]]
from = "C3.1"
to = "U1.20"
max = 2.0
[[near]]
from = "C4.1"
to = "U1.28"
max = 2.0

[board]
outline = [[0, 0], [25, 0], [25, 25], [0, 25]]

[[part]]
ref = "U1"
pattern = "TQFP-32"
[[part]]
ref = "J1"
pattern = "HDR_1x2_2.54"
[[part]]
ref = "C1"
pattern = "C_0402"
value = "100 nF"
[[part]]
ref = "C2"
pattern = "C_0402"
value = "100 nF"
[[part]]
ref = "C3"
pattern = "C_0402"
value = "100 nF"
[[part]]
ref = "C4"
pattern = "C_0402"
value = "100 nF"

[[net]]
name = "VDD"
pins = ["J1.1", "U1.4", "U1.12", "U1.20", "U1.28", "C1.1", "C2.1", "C3.1", "C4.1"]
[[net]]
name = "GND"
pins = ["J1.2", "U1.5", "U1.13", "U1.21", "U1.29", "C1.2", "C2.2", "C3.2", "C4.2"]
+++

A TQFP-32 microcontroller on a 25 × 25 mm board, with a VDD pin and a ground pin beside it on
each of its four sides: VDD on pins 4, 12, 20 and 28, ground on pins 5, 13, 21 and 29. Each VDD pin
has a 100 nF 0402 capacitor of its own to ground: C1 for pin 4, C2 for pin 12, C3 for pin 20 and C4
for pin 28. A two-pin header brings in VDD on pin 1 and ground on pin 2. The other pins are
unconnected.

Each capacitor's VDD pad is within 2 mm of its own VDD pin, copper edge to copper edge. All four
capacitors are on one net, so the netlist is satisfied wherever they are; the capacitor is named
for its pin, and one at the wrong pin is in the wrong place.
