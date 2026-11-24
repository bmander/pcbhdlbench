"""Writes a case as a placed, unrouted KiCad board: what a router is given.

    python3 harness/place.py routing/bus-8 out/        # out/board.kicad_pcb, out/board.kicad_pro

Only a case that places every one of its parts (`at` on each) can be written: the board has the
case's outline, its parts where it puts them with the pads of their land patterns, the nets on the
pads, and nothing else. The rule set goes into the project file, as the board's least sizes and as
the default net class, which is where KiCad keeps them. A plane the case asks for (a `[[copper]]`
with a layer and a least area) is drawn as an unfilled zone of its net over the whole board, and a
layer the case closes to tracks (`copper = ["F.Cu"]`) is closed by a rule area. Standard library
only."""
import json
import pathlib
import sys
import tomllib
import uuid

import geom

ROOT = pathlib.Path(__file__).resolve().parent.parent
ORIGIN = (100.0, 100.0)  # where the case's lower left corner goes on KiCad's page
COPPER = [("F.Cu", 0), ("In1.Cu", 4), ("In2.Cu", 6), ("In3.Cu", 8), ("In4.Cu", 10), ("B.Cu", 2)]
OTHER = '''(9 "F.Adhes" user "F.Adhesive") (11 "B.Adhes" user "B.Adhesive") (13 "F.Paste" user)
    (15 "B.Paste" user) (5 "F.SilkS" user "F.Silkscreen") (7 "B.SilkS" user "B.Silkscreen")
    (1 "F.Mask" user) (3 "B.Mask" user) (17 "Dwgs.User" user "User.Drawings")
    (19 "Cmts.User" user "User.Comments") (21 "Eco1.User" user "User.Eco1") (23 "Eco2.User" user "User.Eco2")
    (25 "Edge.Cuts" user) (27 "Margin" user) (31 "F.CrtYd" user "F.Courtyard") (29 "B.CrtYd" user "B.Courtyard")
    (35 "F.Fab" user) (33 "B.Fab" user)'''


def placeable(case):
    """Whether the case places every part, on the top, so that a router can be given it."""
    return (case.get("status") == "specified" and "part" in case
            and all("at" in p and p.get("side", "top") == "top" for p in case["part"]))


def uid(*what):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "pcbhdl-bench/" + "/".join(map(str, what))))


def layers_of(n):
    """The copper layers of a board of `n`, outer first then inner, as KiCad orders them."""
    inner = [name for name, _ in COPPER[1:-1]][:n - 2]
    return ["F.Cu", *inner, "B.Cu"] if n > 1 else ["F.Cu"]


def board(case, patterns, rules):
    """The case as the text of a .kicad_pcb."""
    rule = rules[case["rules"]]
    height = max(p[1] for p in case["board"]["outline"])

    def page(p):  # the case's frame, y up, to KiCad's page, y down
        return (ORIGIN[0] + p[0], ORIGIN[1] + height - p[1])

    def n(v):
        return f"{v:.6f}".rstrip("0").rstrip(".")

    copper = layers_of(rule["layers"])
    ids = dict(COPPER)
    out = ['(kicad_pcb (version 20241229) (generator "pcbhdl-bench") (generator_version "0.3")',
           "  (general (thickness 1.6) (legacy_teardrops no))", '  (paper "A4")',
           "  (layers " + " ".join(f'({ids[name]} "{name}" signal)' for name in copper), "    " + OTHER + ")",
           "  (setup (pad_to_mask_clearance 0))", '  (net 0 "")']
    net_of, number = {}, {}
    for i, net in enumerate(case["net"], 1):
        number[net["name"]] = i
        out.append(f'  (net {i} "{net["name"]}")')
        for pin in net["pins"]:
            net_of[pin] = net["name"]

    for part in case["part"]:
        pat, rot = patterns[part["pattern"]], part.get("rotation", 0)
        x, y = page(part["at"])
        drilled = any(len(p) > 5 for p in pat["pads"])
        cx0, cy0, cx1, cy1 = pat["courtyard"]
        out += [f'  (footprint "bench:{part["pattern"]}" (layer "F.Cu") (uuid "{uid(case["id"], part["ref"])}")',
                f"    (at {n(x)} {n(y)} {n(rot)})",
                f'    (property "Reference" "{part["ref"]}" (at 0 {n(-cy1 - 1)} {n(rot)}) (layer "F.SilkS") '
                f'(uuid "{uid(case["id"], part["ref"], "ref")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
                f'    (property "Value" "{part.get("value", part["pattern"])}" (at 0 {n(-cy0 + 1)} {n(rot)}) (layer "F.Fab") '
                f'(uuid "{uid(case["id"], part["ref"], "value")}") (effects (font (size 0.8 0.8) (thickness 0.12))))',
                f'    (attr {"through_hole" if drilled else "smd"})',
                f'    (fp_rect (start {n(cx0)} {n(-cy1)}) (end {n(cx1)} {n(-cy0)}) (stroke (width 0.05) (type solid)) '
                f'(fill no) (layer "F.CrtYd") (uuid "{uid(case["id"], part["ref"], "yard")}"))']
        for k, pad in enumerate(pat["pads"]):
            name, px, py, w, h = pad[:5]
            net = net_of.get(f"{part['ref']}.{name}")
            joined = f' (net {number[net]} "{net}")' if net else ""
            if len(pad) > 5:
                shape = "circle" if w == h else "oval"
                kind = f'thru_hole {shape} (at {n(px)} {n(-py)} {n(rot)}) (size {n(w)} {n(h)}) (drill {n(pad[5])}) (layers "*.Cu" "*.Mask")'
            else:
                shape = "circle" if part["pattern"].startswith("BGA") else "rect"
                kind = f'smd {shape} (at {n(px)} {n(-py)} {n(rot)}) (size {n(w)} {n(h)}) (layers "F.Cu" "F.Mask" "F.Paste")'
            out.append(f'    (pad "{name}" {kind}{joined} (uuid "{uid(case["id"], part["ref"], "pad", k)}"))')
        out.append("  )")

    corners = [page(p) for p in case["board"]["outline"]]
    for i, (a, b) in enumerate(geom.edges(corners)):
        out.append(f'  (gr_line (start {n(a[0])} {n(a[1])}) (end {n(b[0])} {n(b[1])}) (stroke (width 0.1) (type solid)) '
                   f'(layer "Edge.Cuts") (uuid "{uid(case["id"], "edge", i)}"))')
    pts = " ".join(f"(xy {n(x)} {n(y)})" for x, y in corners)

    # the planes the case asks for: a zone of the net over the whole board, for KiCad to fill
    for i, plane in enumerate(c for c in case.get("copper", []) if "layer" in c and "min" in c):
        out.append(f'  (zone (net {number[plane["net"]]}) (net_name "{plane["net"]}") (layer "{plane["layer"]}") '
                   f'(uuid "{uid(case["id"], "plane", i)}") (hatch edge 0.5) (connect_pads (clearance {n(rule["clearance"])})) '
                   f'(min_thickness {n(rule["track"])}) (filled_areas_thickness no) '
                   f'(fill (thermal_gap {n(rule["clearance"])}) (thermal_bridge_width {n(2 * rule["track"])})) '
                   f"(polygon (pts {pts})))")
    # the layers the case closes to tracks: a rule area over the whole board on each of the others
    only = case.get("copper") if isinstance(case.get("copper"), list) and all(isinstance(c, str) for c in case["copper"]) else None
    for layer in ([name for name in copper if name not in only] if only else []):
        out.append(f'  (zone (net 0) (net_name "") (layer "{layer}") (uuid "{uid(case["id"], "closed", layer)}") '
                   f'(name "closed to tracks") (hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.1) '
                   f"(filled_areas_thickness no) (keepout (tracks not_allowed) (vias not_allowed) (pads allowed) "
                   f"(copperpour allowed) (footprints allowed)) (placement (enabled no) (sheetname \"\")) "
                   f"(fill (thermal_gap 0.5) (thermal_bridge_width 0.5)) (polygon (pts {pts})))")
    out.append(")")
    return "\n".join(out) + "\n"


def project(case, rules):
    """The rule set as a KiCad project: the board's least sizes, and the default net class."""
    r = rules[case["rules"]]
    via, drill = r.get("via_pad", 0.6), r.get("via_drill", 0.3)
    return json.dumps({
        "board": {"design_settings": {
            "rules": {"min_clearance": r["clearance"], "min_track_width": r["track"], "min_via_diameter": via,
                      "min_through_hole_diameter": drill, "min_via_annular_width": (via - drill) / 2,
                      "min_copper_edge_clearance": r["edge"], "min_hole_clearance": r["clearance"],
                      "min_hole_to_hole": 0.25},
            "track_widths": [0.0, r["track"]], "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": via, "drill": drill}],
            "zones_allow_external_fillets": False}},
        "meta": {"filename": "board.kicad_pro", "version": 3},
        "net_settings": {"classes": [{"name": "Default", "clearance": r["clearance"], "track_width": r["track"],
                                      "via_diameter": via, "via_drill": drill, "microvia_diameter": 0.3,
                                      "microvia_drill": 0.1, "diff_pair_width": r["track"], "diff_pair_gap": r["clearance"],
                                      "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12, "line_style": 0,
                                      "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}],
                         "meta": {"version": 4}},
    }, indent=1) + "\n"


def write(case, out):
    patterns = tomllib.loads((ROOT / "patterns.toml").read_text())
    rules = tomllib.loads((ROOT / "rules.toml").read_text())
    out.mkdir(parents=True, exist_ok=True)
    (out / "board.kicad_pcb").write_text(board(case, patterns, rules))
    (out / "board.kicad_pro").write_text(project(case, rules))


if __name__ == "__main__":
    import run
    case = run.read_case(ROOT / "cases" / f"{sys.argv[1]}.md")
    if not placeable(case):
        raise SystemExit(f"{case['id']} does not place every part: no router can be given it")
    write(case, pathlib.Path(sys.argv[2]))
