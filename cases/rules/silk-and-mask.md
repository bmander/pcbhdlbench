+++
title = "Silkscreen clear of pads, mask between them"
tags = ["rules", "assembly"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline"]
+++

Thirty parts, each with a reference designator on the silkscreen. No silkscreen overlaps a pad's mask opening or another designator; each designator is within 2 mm of its part and reads from the south or the east; no sliver of solder mask is narrower than 0.1 mm.
