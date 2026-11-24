+++
title = "Twelve LEDs in a ring"
tags = ["parametric", "pattern", "polar"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed"]

[board]
outline = [[0, 0], [30, 0], [30, 30], [0, 30]]

[[part]]
ref = "J1"
pattern = "HDR_1x2_2.54"
at = [13.73, 15.0]
rotation = 0
[[part]]
ref = "D1"
pattern = "LED_0603"
at = [25.0, 15.0]
rotation = 90.0
[[part]]
ref = "D2"
pattern = "LED_0603"
at = [23.6603, 20.0]
rotation = 120.0
[[part]]
ref = "D3"
pattern = "LED_0603"
at = [20.0, 23.6603]
rotation = 150.0
[[part]]
ref = "D4"
pattern = "LED_0603"
at = [15.0, 25.0]
rotation = 180.0
[[part]]
ref = "D5"
pattern = "LED_0603"
at = [10.0, 23.6603]
rotation = 210.0
[[part]]
ref = "D6"
pattern = "LED_0603"
at = [6.3397, 20.0]
rotation = 240.0
[[part]]
ref = "D7"
pattern = "LED_0603"
at = [5.0, 15.0]
rotation = 270.0
[[part]]
ref = "D8"
pattern = "LED_0603"
at = [6.3397, 10.0]
rotation = 300.0
[[part]]
ref = "D9"
pattern = "LED_0603"
at = [10.0, 6.3397]
rotation = 330.0
[[part]]
ref = "D10"
pattern = "LED_0603"
at = [15.0, 5.0]
rotation = 0.0
[[part]]
ref = "D11"
pattern = "LED_0603"
at = [20.0, 6.3397]
rotation = 30.0
[[part]]
ref = "D12"
pattern = "LED_0603"
at = [23.6603, 10.0]
rotation = 60.0

[[net]]
name = "VIN"
pins = ["J1.1", "D12.A"]
[[net]]
name = "GND"
pins = ["J1.2", "D1.K"]
[[net]]
name = "L1"
pins = ["D1.A", "D2.K"]
[[net]]
name = "L2"
pins = ["D2.A", "D3.K"]
[[net]]
name = "L3"
pins = ["D3.A", "D4.K"]
[[net]]
name = "L4"
pins = ["D4.A", "D5.K"]
[[net]]
name = "L5"
pins = ["D5.A", "D6.K"]
[[net]]
name = "L6"
pins = ["D6.A", "D7.K"]
[[net]]
name = "L7"
pins = ["D7.A", "D8.K"]
[[net]]
name = "L8"
pins = ["D8.A", "D9.K"]
[[net]]
name = "L9"
pins = ["D9.A", "D10.K"]
[[net]]
name = "L10"
pins = ["D10.A", "D11.K"]
[[net]]
name = "L11"
pins = ["D11.A", "D12.K"]
+++

12 0603 LEDs equally spaced on a circle of radius 10 mm about the middle of a 30 × 30 mm
board, (15, 15). LED *k*, counting from 1, is at angle 30·(*k* − 1)° from the x axis, counter-clockwise, and
lies along the circle, turned 30·(*k* − 1)° + 90°, so that its anode leads counter-clockwise toward
the next LED's cathode. They are a series string: each LED's anode is joined to the next one's
cathode. A two-pin header at the middle of the board, pin 1 at (13.73, 15) and pin 2 at (16.27, 15), feeds
the string: pin 1 to the anode of D12, the last LED, and pin 2 to the cathode of D1.

Every position follows from one rule, and the case's header has them worked out. An implementation
should state the rule, not the twelve positions.
