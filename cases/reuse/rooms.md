+++
title = "Each block in its own room"
tags = ["reuse", "hierarchy", "placement"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "keepout"]
+++

A power supply, a microcontroller and a radio, each a module in the design, each given a rectangle on the board. Every part lies within its module's rectangle, and so does every track of a net that is internal to the module.
