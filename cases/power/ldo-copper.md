+++
title = "Copper to cool a regulator"
tags = ["power", "thermal", "pour"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "copper", "vias"]

[[copper]]
net = "VOUT"
layer = "F.Cu"
min = 200.0

[[copper]]
net = "VOUT"
layer = "B.Cu"
min = 200.0

[[vias]]
net = "VOUT"
min = 6

[board]
outline = [[0, 0], [30, 0], [30, 25], [0, 25]]

[[part]]
ref = "U1"
pattern = "SOT-223"
value = "3.3 V LDO"
[[part]]
ref = "C1"
pattern = "C_0805"
value = "10 µF"
[[part]]
ref = "C2"
pattern = "C_0805"
value = "22 µF"
[[part]]
ref = "J1"
pattern = "HDR_1x2_2.54"
[[part]]
ref = "J2"
pattern = "HDR_1x2_2.54"

[[net]]
name = "VIN"
pins = ["J1.1", "U1.3", "C1.1"]
[[net]]
name = "GND"
pins = ["J1.2", "J2.2", "U1.1", "C1.2", "C2.2"]
[[net]]
name = "VOUT"
pins = ["U1.2", "C2.1", "J2.1"]
+++

A 1 A linear regulator in SOT-223, pinned as the 1117 is (1 ground, 2 output, 3 input, and
the tab the output again), on a 30 × 25 mm board, with a 10 µF 0805 capacitor C1 from its input to
ground and a 22 µF one, C2, from its output to ground. A two-pin header J1 brings in the input on
pin 1 and ground on pin 2; another, J2, takes out the output on pin 1 and ground on pin 2.

Dropping 5 V to 3.3 V at an amp is 1.7 W, and a SOT-223 sheds it through its tab into the board.
So the output net, which the tab is on, has at least 200 mm² of copper on the top layer, at least
200 mm² more on the bottom, and at least six vias joining the two. The board is 750 mm² a side,
and the input and ground still have to be routed.
