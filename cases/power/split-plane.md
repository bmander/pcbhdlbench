+++
title = "A plane split between two supplies"
tags = ["power", "plane"]
status = "sketch"
layers = 4
rules = "std-4"
checks = ["parts", "connectivity", "rules", "outline", "pour", "reference"]
+++

As above, but the power layer is split between 3.3 V and 5 V, each region under its own loads. Four signals pass from one side to the other; the case names which outer layer they run on, and that layer's reference is the unsplit ground plane.
