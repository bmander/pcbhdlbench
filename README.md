# pcbhdl-bench

Rosetta Code for PCB HDLs. Each case describes a circuit board in plain words: its parts, its
nets, its outline and what its layout must respect. Each toolchain writes the board in its own
language and lays it out, and every result is graded the same way, from the copper it drew.

Results: **[bmander.github.io/pcbhdlbench](https://bmander.github.io/pcbhdlbench/)**.

Modelled on [brep-bench](https://github.com/bmander/brep-bench), which does the same for B-rep
kernels.

**Status: early.** 82 cases in 11 categories, 23 of them specified down to the netlist and the
rest one-paragraph sketches. The harness grades fourteen of the checks (`parts`, `connectivity`,
`rules`, `outline`, `fixed`, `side`, `layers`, `near`, `replica`, `loop`, `apart`, `copper`,
`width`, `vias`) and refusals, which is what those 23 cases ask. Two toolchains are entered, tscircuit and netsmith, and three routers (Freerouting, fastroute and
KiCadRoutingTools) on the cases that place every part; their results are on the site.

## Why

Hardware description languages for circuit boards keep appearing (tscircuit, atopile, Zener, SKiDL,
JITX, Polymorphic Blocks), and most stop at the netlist. The step after it, from a design to a
placed and routed board, is the one now being handed to autorouters and LLM agents. The benchmarks
of that step ([a survey](landscape.json), on the site as *Prior work*) each give one canonical file
to an agent or a router. None compares the languages, and none isolates the difficulties.

## Cases

| Category | Asks |
| --- | --- |
| `basics` | Can the toolchain read a design, place, route and write a board at all |
| `placement` | Parts near a pin, on an edge, out of a keepout, under a ceiling |
| `routing` | Crossings, buses, channels, mazes, QFN and BGA fanouts |
| `power` | Width for current, pours and planes, hot loops, Kelvin and star connections |
| `highspeed` | Differential pairs, impedance, matched lengths, return paths |
| `rules` | Clearance, creepage, annular rings, edges, silkscreen |
| `outline` | Round, L-shaped and slotted boards; Uno shield, Pi HAT, M.2 |
| `reuse` | A module laid out once and used many times, congruently |
| `parametric` | Rings, grids and ladders that follow from a number |
| `unsatisfiable` | Boards that cannot be made: the right answer is a refusal |
| `integration` | Real boards, from a 555 blinker to a single-board computer |

A case is `cases/<category>/<name>.md`: a TOML header, then the description. A *specified* case's
header holds its outline, parts and nets ([`patterns.toml`](patterns.toml) has the land patterns,
[`rules.toml`](rules.toml) the rule sets); a *sketch* has only its title, layers and the checks it
would name.

## Grading, as proposed

A runner writes a KiCad `.kicad_pcb`. The harness reads its geometry and nothing else, works out
from the copper what is joined to what, and checks what the case names: always that the parts are
there, that the copper joins exactly the case's nets, that the rule set holds and that everything is
inside the outline; then, by case, fixed positions, distances, keepouts, widths, lengths, pairs,
impedance, pours, creepage, loop area, congruent replicas. **Pass** is every check. **Placed** is a
legal placement not fully routed. **Refused** ranks above **wrong**. See [SPEC.md](SPEC.md).

## Running it

```bash
(cd toolchains/tscircuit && npm install)   # tscircuit, and bun, which its CLI runs on
# netsmith, from source (it has no binary for an Intel Mac); its chips use an installed KiCad's footprints
git clone https://github.com/noahdgrant/netsmith toolchains/netsmith/upstream
(cd toolchains/netsmith/upstream && NETSMITH_SKIP_WEB=1 CARGO_TARGET_DIR=../target cargo build --release -p netsmith-cli --locked)
# the routers; all three need an installed KiCad, whose Python writes and reads Specctra and fills zones
gh release download v2.1.0 -R freerouting/freerouting -p freerouting-2.1.0.jar -D toolchains/freerouting   # runs on Java 21
gh release download v0.1.14 -R parisxmas/fastroute -p 'fastroute-0.1.14-macos-x64.tar.gz' -D toolchains/fastroute
mkdir -p toolchains/fastroute/bin && tar -xzf toolchains/fastroute/*.tar.gz -C toolchains/fastroute/bin
git clone https://github.com/drandyhaas/KiCadRoutingTools toolchains/krt/upstream
python3 -m venv toolchains/krt/venv && toolchains/krt/venv/bin/pip install numpy scipy shapely Pillow
(cd toolchains/krt/upstream && ../venv/bin/python build_router.py)
python3 harness/run.py                     # run every specified case: results/
python3 harness/site.py                    # render the board: site/
python3 -m http.server -d site             # serve it
```

The harness is Python 3.11+, standard library only; a runner needs its toolchain (tscircuit's needs
Node). `run.py --case basics/rc-lowpass` runs one case, `--toolchain NAME` one toolchain. Each
board is kept at `results/<toolchain>/<case>/board.kicad_pcb`, and the site draws it from there.

## The playground

`playground/` is a page for watching autorouters work: place pads, name nets, pick a strategy
(Lee, bidirectional, A*, Hadlock, rip-up and reroute, negotiated congestion, simulated annealing),
with tracks square or at 45°, and see the search spread and the tracks
laid. The routers are a small Rust crate with no dependencies, `playground/router`, compiled to
WebAssembly behind a C ABI; the page around it is plain JavaScript and a canvas. The cases that
place every part of a two-layer board are among the boards it starts from, and so are three
boards of open hardware with their routing taken away (`playground/boards`, which says whose
they are and under what licences): an Arduino Uno R3, the Castor & Pollux synthesiser's
mainboard and the Corne keyboard.

```bash
cargo test --release --manifest-path playground/router/Cargo.toml
cargo build --release --target wasm32-unknown-unknown --manifest-path playground/router/Cargo.toml
python3 harness/site.py     # copies the page and the module to site/playground/
```

A board can be routed with no page, for timing: `python3 playground/boards/floats.py
playground/boards/corne-keyboard.json /tmp/corne.f32`, then `cargo run --release --example route
--manifest-path playground/router/Cargo.toml -- /tmp/corne.f32 6 1 300` (the strategy's number, 1
for diagonal steps, and the seconds to go on for).

These are teaching routers on a coarse grid, not entrants: they are not on the routers' board.

## Adding a toolchain

Write a runner (`<command> <case id> <out dir>`, see [SPEC.md](SPEC.md#a-runner)) and an
implementation of each specified case under `toolchains/<name>/`, and give the toolchain's entry
in `toolchains.json` its `command`, `version` and `source`. `toolchains/tscircuit` and
`toolchains/netsmith` are the two to copy from. A toolchain that numbers its own parts says which
is which in its `result.json` (`refs`), as netsmith's runner does.

## Open questions

- **Who is entered.** As written, a toolchain: a language with whatever places and routes for it,
  an LLM agent included. The cases would serve as well for agents alone, each given the case and
  any language it likes.
- **Land patterns.** The bench defines its own in `patterns.toml` and checks pads, not names. A
  large case will need a few hundred; importing a subset of KiCad's library by name may be saner.
- **What "placed" is worth**, when most of these languages cannot route.
- **Electrical checks beyond geometry.** Impedance and creepage are computed from geometry here;
  nothing is simulated.
