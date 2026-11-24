+++
title = "A buck converter's hot loop"
tags = ["power", "switching", "loop"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "loop", "near", "pour"]
+++

A synchronous buck regulator in SOT-23-6 with its input capacitor, inductor, output capacitor and feedback divider. The loop from the input capacitor through the switch pins and back encloses no more than 12 mm²; the feedback track keeps 2 mm from the switch node; the switch node's copper is no more than 25 mm².
