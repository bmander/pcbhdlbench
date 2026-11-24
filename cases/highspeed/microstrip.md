+++
title = "A 50 Ω microstrip"
tags = ["highspeed", "impedance"]
status = "sketch"
layers = 4
rules = "std-4"
checks = ["parts", "connectivity", "rules", "outline", "impedance", "reference"]
+++

An SMA edge connector to a 0402 pad, 25 mm, on the top layer of a stackup the case gives (prepreg thickness, permittivity, copper weight). The case does not give the width. The harness computes the track's impedance from its width and the stackup and wants 50 Ω within 10%; ground runs unbroken beneath it.
