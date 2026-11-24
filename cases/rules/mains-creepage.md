+++
title = "Creepage between mains and low voltage"
tags = ["rules", "safety", "creepage"]
status = "sketch"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "creepage"]
+++

A mains input, an isolated AC-DC module and an optocoupler. Six millimetres of creepage separate every primary conductor from every secondary one. Under the optocoupler the pads are 7.6 mm apart and that is enough; a 1 mm slot is asked for under the module, and counts toward the path.
