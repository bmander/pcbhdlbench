+++
title = "A board too small for its parts"
tags = ["refusal", "placement"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["refuse"]
control = "basics/voltage-divider"

[board]
outline = [[0, 0], [10, 0], [10, 10], [0, 10]]

[[part]]
ref = "J1"
pattern = "HDR_1x4_2.54"
[[part]]
ref = "J2"
pattern = "HDR_1x4_2.54"
[[part]]
ref = "J3"
pattern = "HDR_1x4_2.54"

[[net]]
name = "N1"
pins = ["J1.1", "J2.1", "J3.1"]
[[net]]
name = "N2"
pins = ["J1.2", "J2.2", "J3.2"]
[[net]]
name = "N3"
pins = ["J1.3", "J2.3", "J3.3"]
[[net]]
name = "N4"
pins = ["J1.4", "J2.4", "J3.4"]
+++

Three 1×4 headers, pin *n* of each joined to pin *n* of the others, on a 10 × 10 mm board.

A header's courtyard is 11.22 × 3.6 mm, longer than the board is wide or tall, and its diagonal
fits no better turned: one header alone does not fit, on either side. No board exists.
