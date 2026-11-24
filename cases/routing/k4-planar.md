+++
title = "Four headers, six nets, one layer"
tags = ["routing", "single-layer", "planarity"]
status = "specified"
layers = 1
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "layers"]
copper = 1

[board]
outline = [[0, 0], [30, 0], [30, 30], [0, 30]]

[[part]]
ref = "J1"
pattern = "HDR_1x4_2.54"
[[part]]
ref = "J2"
pattern = "HDR_1x4_2.54"
[[part]]
ref = "J3"
pattern = "HDR_1x4_2.54"
[[part]]
ref = "J4"
pattern = "HDR_1x4_2.54"

[[net]]
name = "N12"
pins = ["J1.1", "J2.1"]
[[net]]
name = "N13"
pins = ["J1.2", "J3.1"]
[[net]]
name = "N14"
pins = ["J1.3", "J4.1"]
[[net]]
name = "N23"
pins = ["J2.2", "J3.2"]
[[net]]
name = "N24"
pins = ["J2.3", "J4.2"]
[[net]]
name = "N34"
pins = ["J3.3", "J4.3"]
+++

Four 1×4 headers on a 30 × 30 mm board, each joined to each of the others by one net: the
complete graph K4, six nets, on a header's pins 1 to 3 in the order of the headers it goes to. Pin
4 of each is unconnected. All tracks are on one layer, either one, and there are no vias.

K4 is planar, so the board routes on one layer, with one net run round the outside or between a
header's pins. Nothing is placed for you: a good placement makes the routing easy.
