+++
title = "Thirteen tracks through a neck that fits twelve"
tags = ["refusal", "routing"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["refuse"]
control = "routing/channel"

[board]
outline = [[0, 0], [13, 0], [13, 16.85], [17, 16.85], [17, 0], [30, 0], [30, 36], [17, 36], [17, 19.15], [13, 19.15], [13, 36], [0, 36]]

[[part]]
ref = "J1"
pattern = "HDR_1x13_2.54"
at = [3, 2.76]
rotation = 90
[[part]]
ref = "J2"
pattern = "HDR_1x13_2.54"
at = [27, 2.76]
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
[[net]]
name = "D9"
pins = ["J1.9", "J2.9"]
[[net]]
name = "D10"
pins = ["J1.10", "J2.10"]
[[net]]
name = "D11"
pins = ["J1.11", "J2.11"]
[[net]]
name = "D12"
pins = ["J1.12", "J2.12"]
[[net]]
name = "D13"
pins = ["J1.13", "J2.13"]
+++

The board of `routing/channel`, 2 mm taller, with 1×13 headers: two halves, each 13 × 36 mm,
joined by a neck 4 mm long and 2.3 mm wide between y = 16.85 and y = 19.15. J1 has pin 1 at
(3, 2.76) and J2 at (27, 2.76), pins running toward +y, and pin *n* of one is joined to pin *n* of
the other.

No board exists. The neck is the only way across. Copper keeps 0.3 mm from each edge, leaving
1.7 mm, and seven tracks of 0.15 mm with 0.15 mm between them take 1.95: a layer carries six, two
layers twelve, and there are thirteen nets. A via is 0.6 mm across and carries no more than a
track does.
