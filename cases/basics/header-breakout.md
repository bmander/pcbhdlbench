+++
title = "Two headers, pin for pin"
tags = ["through-hole", "hello-world"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed"]

[board]
outline = [[0, 0], [20, 0], [20, 12], [0, 12]]

[[part]]
ref = "J1"
pattern = "HDR_1x4_2.54"
at = [3, 2.19]
rotation = 90
[[part]]
ref = "J2"
pattern = "HDR_1x4_2.54"
at = [17, 2.19]
rotation = 90

[[net]]
name = "A"
pins = ["J1.1", "J2.1"]
[[net]]
name = "B"
pins = ["J1.2", "J2.2"]
[[net]]
name = "C"
pins = ["J1.3", "J2.3"]
[[net]]
name = "D"
pins = ["J1.4", "J2.4"]
+++

Two 1×4 headers at 2.54 mm pitch on a 20 × 12 mm board, each standing along y: J1 with pin 1 at
(3, 2.19) and J2 with pin 1 at (17, 2.19), both with pin 4 toward +y. Pin *n* of one is joined to
pin *n* of the other.

Both parts are placed by the case, so this one tests routing alone, and that a toolchain can put a
part exactly where it is told: a part's `at` is where its pattern's origin (pin 1, for a header)
lies, and its rotation turns it counter-clockwise about that point, seen from the top.
