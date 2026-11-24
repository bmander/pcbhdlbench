+++
title = "A 555 blinker"
tags = ["integration", "real"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline"]

[board]
outline = [[0, 0], [20, 0], [20, 15], [0, 15]]

[[part]]
ref = "U1"
pattern = "SOIC-8"
value = "NE555"
[[part]]
ref = "R1"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "R2"
pattern = "R_0603"
value = "470 kΩ"
[[part]]
ref = "R3"
pattern = "R_0603"
value = "330 Ω"
[[part]]
ref = "C1"
pattern = "C_0603"
value = "1 µF"
[[part]]
ref = "C2"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "D1"
pattern = "LED_0603"
[[part]]
ref = "J1"
pattern = "HDR_1x2_2.54"

[[net]]
name = "VCC"
pins = ["J1.1", "U1.8", "U1.4", "R1.1", "C2.1"]
[[net]]
name = "GND"
pins = ["J1.2", "U1.1", "C1.2", "C2.2", "D1.K"]
[[net]]
name = "DISCH"
pins = ["U1.7", "R1.2", "R2.1"]
[[net]]
name = "TRIG"
pins = ["U1.2", "U1.6", "R2.2", "C1.1"]
[[net]]
name = "OUT"
pins = ["U1.3", "R3.1"]
[[net]]
name = "LED_A"
pins = ["R3.2", "D1.A"]
+++

The 555 astable of the datasheet, in SOIC-8 on a 20 × 15 mm board. R1 (1 kΩ) from VCC to the
discharge pin, 7; R2 (470 kΩ) from there to the threshold and trigger pins, 6 and 2, tied
together; the timing capacitor C1 (1 µF) from those to ground. Reset, pin 4, is tied to VCC, pin
8; pin 1 is ground. C2 (100 nF) decouples VCC to ground. The output, pin 3, drives the LED's anode
through R3 (330 Ω), and the LED's cathode goes to ground. A two-pin header brings in VCC on pin 1
and ground on pin 2. The control pin, 5, is left unconnected.

The first real board: eight parts, six nets, two of them with five pins.
