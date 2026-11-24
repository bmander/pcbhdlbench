+++
title = "A buck converter's hot loop"
tags = ["power", "switching", "loop"]
status = "specified"
layers = 2
rules = "std-2"
checks = ["parts", "connectivity", "rules", "outline", "loop", "apart", "copper"]

# The hot loop: from the input capacitor along the copper to the VIN pin, through the regulator
# to its ground pin, along the copper back to the capacitor, and through the capacitor.
[[loop]]
name = "the input loop"
path = ["C1.1", "U1.3", "U1.1", "C1.2"]
max = 12.0

# The feedback net keeps clear of the switch node, the regulator's own two pads apart.
[[apart]]
net = "FB"
from = "SW"
except = ["U1"]
min = 1.0

[[copper]]
net = "SW"
max = 25.0

[board]
outline = [[0, 0], [25, 0], [25, 20], [0, 20]]

[[part]]
ref = "U1"
pattern = "SOT-23-6"
value = "TPS562201"
[[part]]
ref = "C1"
pattern = "C_0805"
value = "10 µF"
[[part]]
ref = "C2"
pattern = "C_0603"
value = "100 nF"
[[part]]
ref = "C3"
pattern = "C_0805"
value = "22 µF"
[[part]]
ref = "L1"
pattern = "L_4x4"
value = "2.2 µH"
[[part]]
ref = "R1"
pattern = "R_0603"
value = "33 kΩ"
[[part]]
ref = "R2"
pattern = "R_0603"
value = "10 kΩ"
[[part]]
ref = "J1"
pattern = "HDR_1x2_2.54"
[[part]]
ref = "J2"
pattern = "HDR_1x2_2.54"

[[net]]
name = "VIN"
pins = ["J1.1", "U1.3", "U1.5", "C1.1"]
[[net]]
name = "GND"
pins = ["J1.2", "J2.2", "U1.1", "C1.2", "C3.2", "R2.2"]
[[net]]
name = "SW"
pins = ["U1.2", "L1.1", "C2.2"]
[[net]]
name = "BST"
pins = ["U1.6", "C2.1"]
[[net]]
name = "VOUT"
pins = ["L1.2", "C3.1", "R1.1", "J2.1"]
[[net]]
name = "FB"
pins = ["U1.4", "R1.2", "R2.1"]
+++

A 2 A synchronous buck regulator in SOT-23-6, as the TPS562201 is pinned: 1 ground, 2 switch,
3 VIN, 4 feedback, 5 enable, 6 bootstrap. On a 25 × 20 mm board:

- the input capacitor C1 (10 µF, 0805) from VIN to ground, and the enable pin tied to VIN;
- the bootstrap capacitor C2 (100 nF, 0603) from the bootstrap pin (pad 1) to the switch pin;
- the inductor L1 (2.2 µH, 4 mm square) from the switch pin (pad 1) to VOUT;
- the output capacitor C3 (22 µF, 0805) from VOUT to ground;
- the feedback divider, R1 (33 kΩ) from VOUT to the feedback pin and R2 (10 kΩ) from there to
  ground, for 3.3 V;
- a two-pin header J1 for the input, VIN on pin 1 and ground on pin 2, and another, J2, for the
  output, VOUT on pin 1 and ground on pin 2.

What makes a buck converter's layout good or bad is three things, and the case asks for each:

1. **The hot loop is small.** The input capacitor's current is switched at full amplitude, and
   the loop it runs round radiates in proportion to its area. Take the loop from C1's pad 1 along
   the copper to the VIN pin, straight through the regulator to its ground pin, along the copper
   to C1's pad 2, and straight back through the capacitor: it encloses no more than 12 mm². The
   way along the copper is the shortest one, along the tracks' centre lines.
2. **The feedback net keeps away from the switch node.** No copper of the feedback net comes
   within 1 mm of copper of the switch net, on either layer, the regulator's own two pads apart
   (they are 0.95 mm from one another, and cannot be helped).
3. **The switch node is small.** It swings the full input voltage in nanoseconds, and every
   square millimetre of it is an antenna: its copper, pads and tracks together, is no more than
   25 mm². Its three pads are 6.1 mm² of that.

The VIN and ground pins are on one side of the regulator with the switch pin between them, so the
input capacitor that sits closest is in the switch node's way out.
