+++
title = "A crystal beside its pins"
tags = ["placement", "analog"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "near", "keepout"]
+++

A 3225 crystal and its two load capacitors beside a QFN microcontroller. Each crystal track is under 5 mm long; no other net's copper passes under the crystal or between its tracks on any layer; the load capacitors' ground returns to the MCU's ground pin without crossing either crystal track.
