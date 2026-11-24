+++
title = "Three houses, three utilities, one layer"
tags = ["refusal", "planarity", "single-layer"]
status = "specified"
layers = 1
rules = "std-2"
checks = ["refuse"]
control = "routing/k4-planar"
track_layers = 1

[board]
outline = [[0, 0], [30, 0], [30, 30], [0, 30]]

[[part]]
ref = "H1"
pattern = "SOT-23"
[[part]]
ref = "H2"
pattern = "SOT-23"
[[part]]
ref = "H3"
pattern = "SOT-23"
[[part]]
ref = "U1"
pattern = "SOT-23"
[[part]]
ref = "U2"
pattern = "SOT-23"
[[part]]
ref = "U3"
pattern = "SOT-23"

[[net]]
name = "H1U1"
pins = ["H1.1", "U1.1"]
[[net]]
name = "H1U2"
pins = ["H1.2", "U2.1"]
[[net]]
name = "H1U3"
pins = ["H1.3", "U3.1"]
[[net]]
name = "H2U1"
pins = ["H2.1", "U1.2"]
[[net]]
name = "H2U2"
pins = ["H2.2", "U2.2"]
[[net]]
name = "H2U3"
pins = ["H2.3", "U3.2"]
[[net]]
name = "H3U1"
pins = ["H3.1", "U1.3"]
[[net]]
name = "H3U2"
pins = ["H3.2", "U2.3"]
[[net]]
name = "H3U3"
pins = ["H3.3", "U3.3"]
+++

Six SOT-23 parts on a 30 × 30 mm board, three houses H1 to H3 and three utilities U1 to U3,
every house joined to every utility: pin *j* of H*i* to pin *i* of U*j*, nine nets. All tracks are
on one layer, and there are no vias and no jumpers.

No board exists. Under this rule set no track passes through a SOT-23 between its pads (the left
pads and the right one are 0.4 mm apart, and a track with its clearances takes 0.45), so each part
is one island that every track goes round; shrink each island to a point and the tracks draw
K₃,₃, which is not planar. The right answer is a refusal.
