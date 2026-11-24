+++
title = "A small single-board computer"
tags = ["integration", "real", "bga", "highspeed", "hard"]
status = "sketch"
layers = 6
rules = "hdi-6"
checks = ["parts", "connectivity", "rules", "outline", "length", "pair", "impedance", "reference", "pour", "vias"]
+++

An application processor in 0.65 mm BGA, DDR3 memory with its matched byte lanes, eMMC, a PMIC with four rails, USB and Ethernet. Six layers, some four hundred parts. The hardest case: no open toolchain is expected to pass it yet.
