+++
title = "Fanning out a BGA-256"
tags = ["routing", "fanout", "bga"]
status = "sketch"
layers = 4
rules = "std-4"
checks = ["parts", "connectivity", "rules", "outline", "vias"]
+++

A 16 × 16 ball BGA at 0.8 mm pitch on a four-layer board with two signal layers. A hundred and twenty of its balls go to four edge connectors; the rest are power and ground, joined to their planes. Dog-bone fanout with a 0.45 mm via fits between the balls; via-in-pad is not allowed.
