+++
title = "Free pins on a resistor network"
tags = ["routing", "swap"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline"]
+++

Eight signals pass through an 8-element isolated resistor network between two connectors whose pin orders are scrambled. The case says the elements are interchangeable and each can be turned end for end; with the right assignment the board routes on one layer. Any assignment that connects every signal through exactly one element passes; the vias are reported.
