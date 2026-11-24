+++
title = "One channel laid out, eight times over"
tags = ["reuse", "hierarchy", "replica"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "replica"]

[[replica]]
of = [["RS1", "C1", "RL1"], ["RS2", "C2", "RL2"], ["RS3", "C3", "RL3"], ["RS4", "C4", "RL4"], ["RS5", "C5", "RL5"], ["RS6", "C6", "RL6"], ["RS7", "C7", "RL7"], ["RS8", "C8", "RL8"]]

[board]
outline = [[0, 0], [40, 0], [40, 30], [0, 30]]

[[part]]
ref = "J1"
pattern = "HDR_1x8_2.54"
[[part]]
ref = "J2"
pattern = "HDR_1x8_2.54"
[[part]]
ref = "J3"
pattern = "HDR_1x2_2.54"
[[part]]
ref = "RS1"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C1"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL1"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "RS2"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C2"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL2"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "RS3"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C3"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL3"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "RS4"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C4"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL4"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "RS5"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C5"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL5"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "RS6"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C6"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL6"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "RS7"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C7"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL7"
pattern = "R_0603"
value = "100 kΩ"
[[part]]
ref = "RS8"
pattern = "R_0603"
value = "1 kΩ"
[[part]]
ref = "C8"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "RL8"
pattern = "R_0603"
value = "100 kΩ"

[[net]]
name = "IN1"
pins = ["J1.1", "RS1.1"]
[[net]]
name = "OUT1"
pins = ["RS1.2", "C1.1", "RL1.1", "J2.1"]
[[net]]
name = "IN2"
pins = ["J1.2", "RS2.1"]
[[net]]
name = "OUT2"
pins = ["RS2.2", "C2.1", "RL2.1", "J2.2"]
[[net]]
name = "IN3"
pins = ["J1.3", "RS3.1"]
[[net]]
name = "OUT3"
pins = ["RS3.2", "C3.1", "RL3.1", "J2.3"]
[[net]]
name = "IN4"
pins = ["J1.4", "RS4.1"]
[[net]]
name = "OUT4"
pins = ["RS4.2", "C4.1", "RL4.1", "J2.4"]
[[net]]
name = "IN5"
pins = ["J1.5", "RS5.1"]
[[net]]
name = "OUT5"
pins = ["RS5.2", "C5.1", "RL5.1", "J2.5"]
[[net]]
name = "IN6"
pins = ["J1.6", "RS6.1"]
[[net]]
name = "OUT6"
pins = ["RS6.2", "C6.1", "RL6.1", "J2.6"]
[[net]]
name = "IN7"
pins = ["J1.7", "RS7.1"]
[[net]]
name = "OUT7"
pins = ["RS7.2", "C7.1", "RL7.1", "J2.7"]
[[net]]
name = "IN8"
pins = ["J1.8", "RS8.1"]
[[net]]
name = "OUT8"
pins = ["RS8.2", "C8.1", "RL8.1", "J2.8"]
[[net]]
name = "GND"
pins = ["J3.1", "J3.2", "C1.2", "C2.2", "C3.2", "C4.2", "C5.2", "C6.2", "C7.2", "C8.2", "RL1.2", "RL2.2", "RL3.2", "RL4.2", "RL5.2", "RL6.2", "RL7.2", "RL8.2"]
+++

An input channel of three 0603 parts, used eight times on a 40 × 30 mm board. In channel *k*,
RS*k* (1 kΩ) runs from the input IN*k* to the output OUT*k*, and C*k* (100 nF) and RL*k* (100 kΩ)
each run from OUT*k* to ground: a filter and its load. The inputs come in on a 1×8 header J1,
IN*k* on pin *k*; the outputs leave on a 1×8 header J2, OUT*k* on pin *k*; a two-pin header J3 is
ground on both pins.

The eight channels are laid out alike: the three parts of each stand to one another as the three
of channel 1 do, each channel being the first one moved, and turned if need be, to somewhere else
on the same side of the board. Where the channels go, and how one is arranged, is free. Only the
parts are compared so far, not the tracks.

This is what a module in an HDL should buy: the channel is written once, and so it should be laid
out once.
