# pcbhdl-bench specification, version 0.4 (a proposal)

pcbhdl-bench works like Rosetta Code. Each **case** describes a circuit board in plain words. Each
**toolchain** has its own **implementation** of each case, written the way its users write: in its
own language, with its own library and idioms. A **runner** lays the board out and writes it as a
file. The **harness** grades every file the same way.

The harness reads the checks `parts`, `connectivity`, `rules`, `outline`, `fixed`, `side`,
`layers`, `near`, `replica` (of parts, not yet of tracks), `loop`, `apart`, `copper`, `width` and
`vias`, and refusals. The other checks are named and defined below and not yet read, so a case
that names one cannot be specified yet.

## Principles

- **No canonical design file.** A case is a description, not code. A specified case also carries a
  netlist, which is the answer the harness checks against, not an input to translate: an
  implementation is written from the description, in the toolchain's idiom (a loop for a ring of
  LEDs, a module for a repeated channel).
- **Graded from the copper.** The harness reads the geometry of the board file (pads, tracks, vias,
  zones, outline) and derives the connectivity itself. It does not trust the file's net names or
  any tool's DRC report, and it runs no toolchain's checker.
- **Checks, not scores.** A layout has no single right answer, so a case names predicates that any
  right answer satisfies. Each is decided from geometry alone. Wirelength, via count, board area
  and time are reported and not graded.
- **A refusal ranks above a wrong board.** A toolchain that says "I cannot route this" is more
  useful than one that writes a board with a short. A case with no implementation is *missing*.
- **Some boards cannot be made.** The `unsatisfiable` cases have no layout, each for a reason that
  can be proved in a line. Refusing them is passing.
- **No person at the mouse.** A runner runs unattended. A layout made by hand and stored beside
  the implementation is not a result, except where the case is about reusing one.

## A case

`cases/<category>/<name>.md`; its id is the path without the extension. A TOML header between
`+++` lines, then the description in Markdown.

```
+++
title = "An RC low-pass filter"
tags = ["passives"]
status = "specified"            # or "sketch": described, not yet gradable
layers = 2                      # copper layers
rules = "std-2"                 # a rule set of rules.toml
checks = ["parts", "connectivity", "rules", "outline"]

[board]
outline = [[0, 0], [15, 0], [15, 10], [0, 10]]

[[part]]
ref = "R1"
pattern = "R_0603"              # a land pattern of patterns.toml
value = "10 kΩ"                 # for the reader; not graded
# at = [x, y], rotation = degrees, side = "top": only where the case places the part

[[net]]
name = "OUT"
pins = ["R1.2", "C1.1", "J1.3"]
+++
```

- **Units** are millimetres and degrees. x is to the right and y is up, seen from the top side;
  a rotation is counter-clockwise seen from the top. The outline's first corner is usually the
  origin.
- **A part's position** is that of its pattern's origin. A part on the bottom is mirrored in x
  before it is turned.
- **A pin left out of every net** is unconnected, and copper joining it to anything is a short.
- **`copper`**, where a case names the `layers` check, is the layers its tracks may be on: a list
  of names (`["F.Cu"]`), or a number of layers, whichever they are (`1`). One layer allows no via.
- **Where the board lies** in its file is the toolchain's business. The harness moves it so that
  its outline's lower left corner is the case's, and reads every position from there.
- **A part is found** by its reference, and its pads by their names; where a toolchain's library
  names a pattern's pads otherwise (an LED's anode `1` and not `A`), its entry in
  `toolchains.json` says so under `pads`. The part's place and turn are worked out from where its
  pads are, not read from the file.
- **The description must have one reading.** If two careful readers would build different
  netlists from it, that is a bug in the case. The header's netlist settles it.

## The checks

Every case names `parts`, `connectivity`, `rules` and `outline`, or names `refuse` alone.

| Check | Holds when |
| --- | --- |
| `parts` | Every part is on the board once, its pads agreeing with its land pattern to 0.05 mm, and nothing else is |
| `connectivity` | The copper joins exactly the pins each net names: no opens, no shorts |
| `rules` | The rule set holds: track width, clearance, drills, annular rings, distance from the edge |
| `outline` | The outline is the case's; every courtyard lies inside it and overlaps no other on its side of the board |
| `fixed` | Placed parts are where the case puts them, to 0.01 mm |
| `side` | Each part is on the side the case names |
| `layers` | Copper is only on the layers the case allows |
| `near` | Bounded distances between pads, parts or tracks are within bounds |
| `keepout` | Closed regions are empty of what they are closed to |
| `width` | Between two named pins there is a way along the copper at least as wide as asked |
| `length` | Named nets have the lengths asked, or match as closely as asked |
| `pair` | Each differential pair runs coupled at the stated width and gap, its tracks matched |
| `impedance` | A track's impedance, computed from its width and the case's stackup, is as asked |
| `reference` | Named nets run over unbroken copper of their reference net |
| `pour` | The pours and planes asked for exist, are joined to their nets, and have no dead islands |
| `vias` | The vias the case counts are there |
| `creepage` | The shortest path over the surface between separated conductors is long enough |
| `loop` | A named loop encloses no more area than allowed |
| `replica` | Named instances of a module are congruent, parts and tracks: each is the first, moved and turned, not mirrored |
| `pattern` | Arrayed parts are at the positions the case's rule gives |
| `apart` | Two nets the case names come no nearer one another than allowed, on any layer |
| `copper` | A named net's copper, pads, tracks and pours, is no more than the area allowed, or no less than the area asked |
| `refuse` | No board satisfies the case, and the toolchain says so |

A clearance, a width or a distance from the edge may fall short by 0.005 mm, KiCad's own
allowance. `rules` so far reads track width, via size, clearance between copper not joined,
copper's distance from the edge and the layers used; drill-to-copper, annular rings and the solder
mask are to come.

A check that takes numbers gets them from a table of its own in the header. So far:

```
[[near]]                 # copper edge to copper edge, between two pads
from = "C1.1"
to = "U1.4"
max = 2.0

[[replica]]              # the instances of a module, each a list of its parts in the same order
of = [["RS1", "C1", "RL1"], ["RS2", "C2", "RL2"]]

[[loop]]                 # the area a loop encloses, mm²: from pin to pin, along the copper where
name = "the input loop"  # the two are of one net (the shortest way, by the tracks' centre lines),
path = ["C1.1", "U1.3", "U1.1", "C1.2"]   # and straight through the part where they are not
max = 12.0

[[apart]]                # copper of one net no nearer copper of another, on any layer;
net = "FB"               # `except` leaves out the pads of the parts it names
from = "SW"
except = ["U1"]
min = 1.0

[[copper]]               # a net's copper, mm²: `max` or `min`, summed over the layers or on
net = "SW"               # one (`layer = "F.Cu"`)
max = 25.0

[[width]]                # a way between two pins of a net at least so wide: by tracks that wide,
path = ["J1.1", "F1.1"]  # pads, vias and pours, and by a narrower track only within `neck` of a
min = 1.37               # pad too narrow for the width
neck = 2.0

[[vias]]                 # the vias on a net, at least so many
net = "VOUT"
min = 6
```

Two pads of one name in a land pattern (a regulator's tab and its middle pin) are one pin, joined
inside the part: copper to either reaches the pin.

A pattern that follows from a rule (a ring, a grid) needs no check of its own: the case's header
has the positions worked out, as `at` and `rotation` on each part, and `fixed` checks them. The
other checks' tables are not yet fixed; the sketches state them in prose.

## Outcomes

| Outcome | Means |
| --- | --- |
| **pass** | Every check the case names holds |
| **placed** | `parts`, `outline` and the placement checks hold, and there are no shorts, but some net is open |
| **refused** | The runner said it cannot lay the board out, and why |
| **wrong** | A board was written and a check fails some other way: a short, a missing part, a broken rule |
| **crashed**, **timeout** | The runner died, or ran past the case's limit |
| **missing** | No implementation |

In order: pass, placed, refused, wrong. For a `refuse` case, any board is wrong, and a refusal
passes only from a toolchain that passes the case's **control**: the case its header names as
`control`, a board beside it that can be made (the neck with twelve nets, beside the neck with
thirteen). A toolchain that refuses both has shown nothing, and its refusal stays *refused*. A
refusal for a mistake in the implementation is caught the same way, where the control shares it; the board is graded all the same, by the four checks every case names, to say what is wrong
with it, and a board that passed them would show the case to have a layout after all.

A toolchain that checks its own work and reports a fault in the board it made (a net it could not
route, tracks too close) has refused: its runner says so in the toolchain's words. The board is
kept, shown, and graded for the record, which changes nothing: a refusal stays a refusal. A
toolchain that reports nothing is graded on its board.

A runner has 600 seconds for a case, unless the case's header gives a `timeout` of its own. It
starts from nothing: a toolchain's cache of routes it has found before is cleared first.

## A runner

`<command> <case id> <out directory>`, run from the repository's root. It reads its own
implementation of the case and writes `board.kicad_pcb` (KiCad 9's format) and `result.json`:
`{"outcome": "built"}`, `{"outcome": "refused", "why": "…"}`, or `{"outcome": "missing"}` where it
has no implementation of the case. Beside the outcome it may give `refs`, the board's reference
designators to the case's (`{"R7": "RS3"}`), where the toolchain numbers its parts itself. It is timed. It does not read the
case's header: the netlist there is the harness's, to check with.

A toolchain that cannot write KiCad's format writes Gerber X2 and Excellon files, from which the
harness reads the same copper; the parts are then found by their pads.

## A router

A case that places every one of its parts, on the top, is also a routing problem that needs no
language. `harness/place.py` writes it as a placed, unrouted KiCad board: the outline, the parts
where the case puts them with the pads of their land patterns and their nets, the rule set as the
board's least sizes and its default net class (in the `.kicad_pro` beside it, where KiCad keeps
them), an unfilled zone over the whole board for each plane the case asks for, and a rule area
closing each layer the case closes to tracks.

A router's runner is `<command> <dir of the placed board> <out dir>`: it writes
`board.kicad_pcb` and `result.json` as a toolchain's does, and its board is graded by the same
checks against the same case. Routers are listed under `routers` in `toolchains.json`, and their
results are a board of their own. A router that leaves nets open and does not say so is graded on
what it wrote: *placed*, where nothing else is wrong.

## An implementation

One file a case, in the toolchain's language, as its documentation would write it. It may use the
toolchain's own library of parts where the pads agree with the case's land patterns, or the
bench's patterns translated into the toolchain's form. It may not contain coordinates for parts or
tracks the case does not give, and it may not be generated from the case's header: a ring of LEDs
is written as its rule, not as its positions. Implementations may share code, as a design's
modules would.
