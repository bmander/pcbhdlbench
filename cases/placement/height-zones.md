+++
title = "A low ceiling over half the board"
tags = ["placement", "mechanical"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "keepout"]
+++

Half the board lies under a battery, 1.2 mm above the surface: no part taller than 1.0 mm stands there. The case gives each part's height. The tall parts (an electrolytic capacitor, an inductor, a header) must be in the other half; the low passives may go anywhere.
