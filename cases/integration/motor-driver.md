+++
title = "A three-phase motor driver"
tags = ["integration", "real", "power", "hierarchy"]
status = "sketch"
layers = 4
rules = "std-4"
checks = ["parts", "connectivity", "rules", "outline", "replica", "width", "loop", "pour", "near"]
+++

Three half-bridges of the `reuse/nested` kind at 20 A a phase, with a gate driver, current sensing, a microcontroller and a CAN transceiver. Four layers; the power and reuse cases' rules, together.
