"""Writes a playground board as the run of floats the router reads, for playground/router/examples/route.rs.

    python3 playground/boards/floats.py playground/boards/corne-keyboard.json /tmp/corne.f32

The nets the board leaves to a pour are written as no net, as the page writes them."""
import json
import struct
import sys

b = json.load(open(sys.argv[1]))
pour = b.get("pour") or []
v = [b["width"], b["height"], b["pitch"], b["track"], b["clearance"], b["via"], b["edge"], len(b["outline"])]
for x, y in b["outline"]:
    v += [x, y]
v.append(len(b["pads"]))
for p in b["pads"]:
    v += [p["x"], p["y"], p["w"], p["h"], p["side"], 1 if p["round"] else 0, -1 if p["net"] in pour else p["net"]]
open(sys.argv[2], "wb").write(struct.pack(f"<{len(v)}f", *v))
