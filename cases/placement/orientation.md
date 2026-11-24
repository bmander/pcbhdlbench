+++
title = "Polarised parts all the same way round"
tags = ["placement", "assembly"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "fixed"]
+++

Eight tantalum capacitors and eight SOD-123 diodes. For assembly, every polarised part of one kind has the same rotation: all the capacitors' positive pads to the north, all the diodes' cathodes to the east. The netlist wants half of them the other way round electrically, so the routing, not the rotation, gives way.
