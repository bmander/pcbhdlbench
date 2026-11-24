+++
title = "Fanning out a BGA-256"
tags = ["routing", "fanout", "bga", "four-layer", "scale"]
status = "specified"
layers = 4
rules = "std-4"
checks = ["parts", "connectivity", "rules", "outline", "fixed", "vias", "copper"]
timeout = 1800

# no via in a ball's pad
[[vias]]
not_in = "U1"

# the two inner layers are planes
[[copper]]
net = "GND"
layer = "In1.Cu"
min = 2500.0

[[copper]]
net = "VCC"
layer = "In2.Cu"
min = 2500.0

[board]
outline = [[0, 0], [60, 0], [60, 60], [0, 60]]

[[part]]
ref = "U1"
pattern = "BGA-256"
at = [30, 30]
rotation = 0
[[part]]
ref = "J1"
pattern = "HDR_2x14_2.54"
at = [13.49, 52]
rotation = 90
[[part]]
ref = "J2"
pattern = "HDR_2x14_2.54"
at = [52, 46.51]
rotation = 0
[[part]]
ref = "J3"
pattern = "HDR_2x14_2.54"
at = [46.51, 8]
rotation = 270
[[part]]
ref = "J4"
pattern = "HDR_2x14_2.54"
at = [8, 13.49]
rotation = 180
[[part]]
ref = "J5"
pattern = "HDR_1x2_2.54"
at = [4, 4]
rotation = 0

[[net]]
name = "A1"
pins = ["U1.A1", "J1.1"]
[[net]]
name = "A2"
pins = ["U1.A2", "J1.2"]
[[net]]
name = "B2"
pins = ["U1.B2", "J1.3"]
[[net]]
name = "A3"
pins = ["U1.A3", "J1.4"]
[[net]]
name = "B3"
pins = ["U1.B3", "J1.5"]
[[net]]
name = "A4"
pins = ["U1.A4", "J1.6"]
[[net]]
name = "B4"
pins = ["U1.B4", "J1.7"]
[[net]]
name = "A5"
pins = ["U1.A5", "J1.8"]
[[net]]
name = "B5"
pins = ["U1.B5", "J1.9"]
[[net]]
name = "A6"
pins = ["U1.A6", "J1.10"]
[[net]]
name = "B6"
pins = ["U1.B6", "J1.11"]
[[net]]
name = "A7"
pins = ["U1.A7", "J1.12"]
[[net]]
name = "B7"
pins = ["U1.B7", "J1.13"]
[[net]]
name = "A8"
pins = ["U1.A8", "J1.14"]
[[net]]
name = "B8"
pins = ["U1.B8", "J1.15"]
[[net]]
name = "A9"
pins = ["U1.A9", "J1.16"]
[[net]]
name = "B9"
pins = ["U1.B9", "J1.17"]
[[net]]
name = "A10"
pins = ["U1.A10", "J1.18"]
[[net]]
name = "B10"
pins = ["U1.B10", "J1.19"]
[[net]]
name = "A11"
pins = ["U1.A11", "J1.20"]
[[net]]
name = "B11"
pins = ["U1.B11", "J1.21"]
[[net]]
name = "A12"
pins = ["U1.A12", "J1.22"]
[[net]]
name = "B12"
pins = ["U1.B12", "J1.23"]
[[net]]
name = "A13"
pins = ["U1.A13", "J1.24"]
[[net]]
name = "B13"
pins = ["U1.B13", "J1.25"]
[[net]]
name = "A14"
pins = ["U1.A14", "J1.26"]
[[net]]
name = "B14"
pins = ["U1.B14", "J1.27"]
[[net]]
name = "A15"
pins = ["U1.A15", "J1.28"]
[[net]]
name = "A16"
pins = ["U1.A16", "J2.1"]
[[net]]
name = "B16"
pins = ["U1.B16", "J2.2"]
[[net]]
name = "B15"
pins = ["U1.B15", "J2.3"]
[[net]]
name = "C16"
pins = ["U1.C16", "J2.4"]
[[net]]
name = "C15"
pins = ["U1.C15", "J2.5"]
[[net]]
name = "D16"
pins = ["U1.D16", "J2.6"]
[[net]]
name = "D15"
pins = ["U1.D15", "J2.7"]
[[net]]
name = "E16"
pins = ["U1.E16", "J2.8"]
[[net]]
name = "E15"
pins = ["U1.E15", "J2.9"]
[[net]]
name = "F16"
pins = ["U1.F16", "J2.10"]
[[net]]
name = "F15"
pins = ["U1.F15", "J2.11"]
[[net]]
name = "G16"
pins = ["U1.G16", "J2.12"]
[[net]]
name = "G15"
pins = ["U1.G15", "J2.13"]
[[net]]
name = "H16"
pins = ["U1.H16", "J2.14"]
[[net]]
name = "H15"
pins = ["U1.H15", "J2.15"]
[[net]]
name = "J16"
pins = ["U1.J16", "J2.16"]
[[net]]
name = "J15"
pins = ["U1.J15", "J2.17"]
[[net]]
name = "K16"
pins = ["U1.K16", "J2.18"]
[[net]]
name = "K15"
pins = ["U1.K15", "J2.19"]
[[net]]
name = "L16"
pins = ["U1.L16", "J2.20"]
[[net]]
name = "L15"
pins = ["U1.L15", "J2.21"]
[[net]]
name = "M16"
pins = ["U1.M16", "J2.22"]
[[net]]
name = "M15"
pins = ["U1.M15", "J2.23"]
[[net]]
name = "N16"
pins = ["U1.N16", "J2.24"]
[[net]]
name = "N15"
pins = ["U1.N15", "J2.25"]
[[net]]
name = "P16"
pins = ["U1.P16", "J2.26"]
[[net]]
name = "P15"
pins = ["U1.P15", "J2.27"]
[[net]]
name = "R16"
pins = ["U1.R16", "J2.28"]
[[net]]
name = "T16"
pins = ["U1.T16", "J3.1"]
[[net]]
name = "T15"
pins = ["U1.T15", "J3.2"]
[[net]]
name = "R15"
pins = ["U1.R15", "J3.3"]
[[net]]
name = "T14"
pins = ["U1.T14", "J3.4"]
[[net]]
name = "R14"
pins = ["U1.R14", "J3.5"]
[[net]]
name = "T13"
pins = ["U1.T13", "J3.6"]
[[net]]
name = "R13"
pins = ["U1.R13", "J3.7"]
[[net]]
name = "T12"
pins = ["U1.T12", "J3.8"]
[[net]]
name = "R12"
pins = ["U1.R12", "J3.9"]
[[net]]
name = "T11"
pins = ["U1.T11", "J3.10"]
[[net]]
name = "R11"
pins = ["U1.R11", "J3.11"]
[[net]]
name = "T10"
pins = ["U1.T10", "J3.12"]
[[net]]
name = "R10"
pins = ["U1.R10", "J3.13"]
[[net]]
name = "T9"
pins = ["U1.T9", "J3.14"]
[[net]]
name = "R9"
pins = ["U1.R9", "J3.15"]
[[net]]
name = "T8"
pins = ["U1.T8", "J3.16"]
[[net]]
name = "R8"
pins = ["U1.R8", "J3.17"]
[[net]]
name = "T7"
pins = ["U1.T7", "J3.18"]
[[net]]
name = "R7"
pins = ["U1.R7", "J3.19"]
[[net]]
name = "T6"
pins = ["U1.T6", "J3.20"]
[[net]]
name = "R6"
pins = ["U1.R6", "J3.21"]
[[net]]
name = "T5"
pins = ["U1.T5", "J3.22"]
[[net]]
name = "R5"
pins = ["U1.R5", "J3.23"]
[[net]]
name = "T4"
pins = ["U1.T4", "J3.24"]
[[net]]
name = "R4"
pins = ["U1.R4", "J3.25"]
[[net]]
name = "T3"
pins = ["U1.T3", "J3.26"]
[[net]]
name = "R3"
pins = ["U1.R3", "J3.27"]
[[net]]
name = "T2"
pins = ["U1.T2", "J3.28"]
[[net]]
name = "T1"
pins = ["U1.T1", "J4.1"]
[[net]]
name = "R1"
pins = ["U1.R1", "J4.2"]
[[net]]
name = "R2"
pins = ["U1.R2", "J4.3"]
[[net]]
name = "P1"
pins = ["U1.P1", "J4.4"]
[[net]]
name = "P2"
pins = ["U1.P2", "J4.5"]
[[net]]
name = "N1"
pins = ["U1.N1", "J4.6"]
[[net]]
name = "N2"
pins = ["U1.N2", "J4.7"]
[[net]]
name = "M1"
pins = ["U1.M1", "J4.8"]
[[net]]
name = "M2"
pins = ["U1.M2", "J4.9"]
[[net]]
name = "L1"
pins = ["U1.L1", "J4.10"]
[[net]]
name = "L2"
pins = ["U1.L2", "J4.11"]
[[net]]
name = "K1"
pins = ["U1.K1", "J4.12"]
[[net]]
name = "K2"
pins = ["U1.K2", "J4.13"]
[[net]]
name = "J1"
pins = ["U1.J1", "J4.14"]
[[net]]
name = "J2"
pins = ["U1.J2", "J4.15"]
[[net]]
name = "H1"
pins = ["U1.H1", "J4.16"]
[[net]]
name = "H2"
pins = ["U1.H2", "J4.17"]
[[net]]
name = "G1"
pins = ["U1.G1", "J4.18"]
[[net]]
name = "G2"
pins = ["U1.G2", "J4.19"]
[[net]]
name = "F1"
pins = ["U1.F1", "J4.20"]
[[net]]
name = "F2"
pins = ["U1.F2", "J4.21"]
[[net]]
name = "E1"
pins = ["U1.E1", "J4.22"]
[[net]]
name = "E2"
pins = ["U1.E2", "J4.23"]
[[net]]
name = "D1"
pins = ["U1.D1", "J4.24"]
[[net]]
name = "D2"
pins = ["U1.D2", "J4.25"]
[[net]]
name = "C1"
pins = ["U1.C1", "J4.26"]
[[net]]
name = "C2"
pins = ["U1.C2", "J4.27"]
[[net]]
name = "B1"
pins = ["U1.B1", "J4.28"]
[[net]]
name = "GND"
pins = ["J5.2", "U1.C3", "U1.C5", "U1.C7", "U1.C9", "U1.C11", "U1.C13", "U1.D4", "U1.D6", "U1.D8", "U1.D10", "U1.D12", "U1.D14", "U1.E3", "U1.E5", "U1.E7", "U1.E9", "U1.E11", "U1.E13", "U1.F4", "U1.F6", "U1.F8", "U1.F10", "U1.F12", "U1.F14", "U1.G3", "U1.G5", "U1.G7", "U1.G9", "U1.G11", "U1.G13", "U1.H4", "U1.H6", "U1.H8", "U1.H10", "U1.H12", "U1.H14", "U1.J3", "U1.J5", "U1.J7", "U1.J9", "U1.J11", "U1.J13", "U1.K4", "U1.K6", "U1.K8", "U1.K10", "U1.K12", "U1.K14", "U1.L3", "U1.L5", "U1.L7", "U1.L9", "U1.L11", "U1.L13", "U1.M4", "U1.M6", "U1.M8", "U1.M10", "U1.M12", "U1.M14", "U1.N3", "U1.N5", "U1.N7", "U1.N9", "U1.N11", "U1.N13", "U1.P4", "U1.P6", "U1.P8", "U1.P10", "U1.P12", "U1.P14"]
[[net]]
name = "VCC"
pins = ["J5.1", "U1.C4", "U1.C6", "U1.C8", "U1.C10", "U1.C12", "U1.C14", "U1.D3", "U1.D5", "U1.D7", "U1.D9", "U1.D11", "U1.D13", "U1.E4", "U1.E6", "U1.E8", "U1.E10", "U1.E12", "U1.E14", "U1.F3", "U1.F5", "U1.F7", "U1.F9", "U1.F11", "U1.F13", "U1.G4", "U1.G6", "U1.G8", "U1.G10", "U1.G12", "U1.G14", "U1.H3", "U1.H5", "U1.H7", "U1.H9", "U1.H11", "U1.H13", "U1.J4", "U1.J6", "U1.J8", "U1.J10", "U1.J12", "U1.J14", "U1.K3", "U1.K5", "U1.K7", "U1.K9", "U1.K11", "U1.K13", "U1.L4", "U1.L6", "U1.L8", "U1.L10", "U1.L12", "U1.L14", "U1.M3", "U1.M5", "U1.M7", "U1.M9", "U1.M11", "U1.M13", "U1.N4", "U1.N6", "U1.N8", "U1.N10", "U1.N12", "U1.N14", "U1.P3", "U1.P5", "U1.P7", "U1.P9", "U1.P11", "U1.P13"]
+++

A 256-ball BGA, 16 × 16 at 0.8 mm pitch, in the middle of a 60 × 60 mm four-layer board, with a
2 × 14 header along each side and a two-pin header in the south-west corner for the supply. Every
part is placed by the case: this is routing alone, and a lot of it, 112 signals and two planes.

**The parts.** U1 is at (30, 30), ball A1 at its top left: rows A to T run down (there is no I, O,
Q or S) and columns 1 to 16 run across. The four headers have pin 1 at the origin of their pattern,
pin 2 beside it and the pairs running on from there. J1, along the north side, has pin 1 at
(13.49, 52), its pairs running east and its even pins on the outside. J2, down the east side, has
pin 1 at (52, 46.51), its pairs running south. J3, along the south side, has pin 1 at (46.51, 8),
its pairs running west. J4, up the west side, has pin 1 at (8, 13.49), its pairs running north. On
each, the odd pins are the row nearer the BGA. J5 is at (4, 4), pin 2 to its east.

**The signals** are the balls of the two outer rings, 60 and 52 of them. Each side of the BGA
takes a ring's row less its last corner, going round clockwise: of the outer ring, the north side
has A1 to A15, the east A16 to R16, the south T16 to T2 and the west T1 to B1; of the second ring,
the north has B2 to B14, the east B15 to P15, the south R15 to R3 and the west R2 to C2. That is
28 balls a side, and they go to that side's header in their order along it from its pin 1 (and of
two balls in one column or row, the outer ring's first): the first to pin 1, the second to pin 2,
and so on, two to each pair of pins. Each net is named for its ball.

**The planes.** The inner twelve by twelve balls, rows C to P and columns 3 to 14, are a
chessboard of ground and supply: ground where the row's and the column's numbers (A is 1) add up
to an even number, as at C3, and VCC where they are odd. The second layer is a ground plane and
the third a VCC plane, each at least 2500 mm² of the board's 3600, and every one of the 144 balls
reaches its plane. J5 brings in VCC on pin 1 and ground on pin 2.

**The rules** are the four-layer set's: 0.127 mm tracks and spaces, a 0.5 mm via with a 0.3 mm
hole. No via stands in a ball's pad. That leaves the textbook fanout: a track leaves each ball of
the outer ring outward, one from the second ring passes between two pads of the outer (0.48 mm
between them, and a track with its spaces takes 0.381), and each inner ball has a short track to a
via in the middle of four pads, where a 0.5 mm via is 0.156 mm from each.
