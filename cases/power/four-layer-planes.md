+++
title = "Ground and power planes"
tags = ["power", "plane"]
status = "sketch"
layers = 4
rules = "std-4"
checks = ["parts", "connectivity", "rules", "outline", "pour", "layers"]
+++

A four-layer board: signal, ground, 3.3 V, signal. The inner layers are unbroken planes but for via clearances, and carry no tracks. Every power and ground pad reaches its plane through its own via within 1.5 mm.
