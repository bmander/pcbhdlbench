+++
title = "An LED and its resistor"
tags = ["passives", "hello-world"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline"]

[board]
outline = [[0, 0], [20, 0], [20, 10], [0, 10]]

[[part]]
ref = "J1"
pattern = "HDR_1x2_2.54"
[[part]]
ref = "R1"
pattern = "R_0603"
value = "330 Ω"
[[part]]
ref = "D1"
pattern = "LED_0603"

[[net]]
name = "VIN"
pins = ["J1.1", "R1.1"]
[[net]]
name = "LED_A"
pins = ["R1.2", "D1.A"]
[[net]]
name = "GND"
pins = ["D1.K", "J1.2"]
+++

A two-pin header, a 330 Ω resistor and an LED in series: header pin 1 to the resistor, the resistor
to the LED's anode, the LED's cathode back to header pin 2. The board is a 20 × 10 mm rectangle with
one corner at the origin. Nothing is placed for you.

The smallest case there is: three parts, three nets, no crossing. A toolchain that passes it can
read a design, place parts inside an outline, route, and write a board the harness can read.
