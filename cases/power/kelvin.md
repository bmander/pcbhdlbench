+++
title = "Kelvin connections to a shunt"
tags = ["power", "analog"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "near", "width"]
+++

A 2512 current-sense resistor in a 5 A path, read by an amplifier. The sense tracks leave from the inner edges of the shunt's pads, run as a pair no more than 0.3 mm apart to the amplifier, and join the power copper nowhere else. The case's netlist names the sense nets apart from the power nets and says where they meet.
