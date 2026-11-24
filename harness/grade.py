"""Grades a board against its case: SPEC.md's checks, each decided from the board's geometry.

`grade(case, board, patterns, rules, names)` returns {"outcome", "why", "checks", "metrics"}:
`checks` maps each check the case names to {"ok", "notes"}. The checks read so far are `parts`,
`connectivity`, `rules`, `outline`, `fixed`, `side`, `layers`, `near` and `replica`; a case naming another cannot be
graded yet. Standard library only."""
import math

import geom
import kicad

READ = {"parts", "connectivity", "rules", "outline", "fixed", "side", "layers", "near", "replica", "loop", "apart",
        "copper", "width", "vias", "refuse"}
PAD = 0.05       # a pad's place, size and drill against its pattern's
PLACE = 0.01     # a placed part's position, and degrees of its rotation
OUTLINE = 0.01   # an outline's corners
TOUCH = 1e-6     # copper closer than this is joined
SLACK = 0.005    # what a clearance or a width may fall short by: KiCad's own DRC epsilon
# the copper layers a board of so many may use, outer first
STACK = ["F.Cu", "B.Cu", "In1.Cu", "In2.Cu", "In3.Cu", "In4.Cu"]


def pose(pattern, pads, side, names):
    """Where a part lies, from its pads: (origin, rotation), or a string saying how its pads
    disagree with its pattern. A part on the bottom is the pattern mirrored in x, then turned."""
    mirror = -1 if side == "bottom" else 1
    named = sorted(names.get(pad["name"], pad["name"]) for pad in pads)
    if named != sorted(p[0] for p in pattern["pads"]):
        ours = sorted(p[0] for p in pattern["pads"])

        def some(names):
            return ", ".join(names[:6]) + (f" … ({len(names)})" if len(names) > 6 else "")
        return f"pads named {some(named)}, where its pattern has {some(ours)}"
    # the part is laid over its pattern by the pads whose names are theirs alone
    want = {p[0]: p for p in pattern["pads"] if named.count(p[0]) == 1}
    have = {names.get(pad["name"], pad["name"]): pad for pad in pads
            if named.count(names.get(pad["name"], pad["name"])) == 1}
    local = {n: (mirror * p[1], p[2]) for n, p in want.items()}
    order = sorted(want)
    if not order:
        return "no pad with a name of its own to lay it by"
    if len(order) == 1:
        turn = 0.0
    else:
        i, j = max(((a, b) for a in order for b in order if a < b),
                   key=lambda ab: math.dist(local[ab[0]], local[ab[1]]))
        actual = geom.sub(have[j]["at"], have[i]["at"])
        ideal = geom.sub(local[j], local[i])
        turn = math.degrees(math.atan2(actual[1], actual[0]) - math.atan2(ideal[1], ideal[0])) % 360
    first = geom.rotate(local[order[0]], turn)
    origin = geom.sub(have[order[0]]["at"], first)
    for p in pattern["pads"]:
        n = p[0]
        at = geom.rotate((mirror * p[1], p[2]), turn)
        # of the pads of this name, the one nearest where the pattern has it
        pad = min((q for q in pads if names.get(q["name"], q["name"]) == n),
                  key=lambda q: math.dist((origin[0] + at[0], origin[1] + at[1]), q["at"]))
        off = math.dist((origin[0] + at[0], origin[1] + at[1]), pad["at"])
        if off > PAD:
            return f"pad {n} {off:.3f} mm from its place in the pattern"
        w, h = (pad["h"], pad["w"]) if abs((pad["angle"] - turn) % 180 - 90) < 1 else (pad["w"], pad["h"])
        if abs(w - p[3]) > PAD or abs(h - p[4]) > PAD:
            return f"pad {n} is {w:g} × {h:g}, where its pattern has {p[3]:g} × {p[4]:g}"
        drill = p[5] if len(p) > 5 else None
        if (drill is None) != (pad["drill"] is None):
            return f"pad {n} is {'drilled' if pad['drill'] else 'not drilled'}, unlike its pattern"
        if drill is not None and abs(pad["drill"] - drill) > PAD:
            return f"pad {n}'s hole is {pad['drill']:g}, where its pattern has {drill:g}"
    return origin, turn


def courtyard(pattern, origin, turn, side):
    x0, y0, x1, y1 = pattern["courtyard"]
    m = -1 if side == "bottom" else 1
    return [(origin[0] + x, origin[1] + y) for x, y in
            (geom.rotate((m * cx, cy), turn) for cx, cy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)))]


def way(pieces, start, end):
    """The shortest way along the copper from one pad's centre to another's, as points, or None
    where there is none. A way runs along a track's centre line, and straight across a pad, a via
    or a zone between the ends of the tracks that meet on it."""
    nodes = []  # (point, layers, reach): a pad's or via's centre, a track's end with half its width
    for p in pieces:
        if len(p["poly"]) == 2 and "width" in p:
            nodes += [(p["poly"][0], p["layers"], p["r"]), (p["poly"][1], p["layers"], p["r"])]
        elif len(p["poly"]) == 1 or p.get("pin") or "at" in p:
            nodes.append((p.get("at", p["poly"][0]), p["layers"], 0.0))
    nodes += [(start["at"], start["layers"], 0.0), (end["at"], end["layers"], 0.0)]
    links = {i: {} for i in range(len(nodes))}
    for p in pieces:
        on = [i for i, (pt, layers, reach) in enumerate(nodes)
              if layers & p["layers"] and geom.distance([pt], p["poly"]) <= p["r"] + reach + TOUCH]
        for i in on:
            for j in on:
                if i < j:
                    d = math.dist(nodes[i][0], nodes[j][0])
                    links[i][j] = min(d, links[i].get(j, math.inf))
                    links[j][i] = links[i][j]
    a, b = len(nodes) - 2, len(nodes) - 1
    best, back, todo = {a: 0.0}, {}, {a}
    while todo:
        i = min(todo, key=best.get)
        todo.discard(i)
        if i == b:
            break
        for j, d in links[i].items():
            if best[i] + d < best.get(j, math.inf) - 1e-12:
                best[j], back[j] = best[i] + d, i
                todo.add(j)
    if b not in best:
        return None
    path = [b]
    while path[-1] != a:
        path.append(back[path[-1]])
    return [nodes[i][0] for i in reversed(path)]


def shapes(piece):
    """A piece of copper as polygons whose union it is: a round one as a 32-gon, a grown one as its
    polygon and a rounded bar along each edge."""
    poly, r = piece["poly"], piece["r"]
    if r <= 0:
        return [poly]
    ring = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(0, 360, 360 // 32)]
    out = [poly] if len(poly) > 2 else []
    for a, b in geom.edges(poly):
        if a == b:
            out.append([(a[0] + x, a[1] + y) for x, y in ring])
            continue
        turn = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        half = [geom.rotate(p, turn - 90) for p in ring[:17]]  # the half ring beyond b
        out.append([(b[0] + x, b[1] + y) for x, y in half] + [(a[0] - x, a[1] - y) for x, y in half])
    return out


def painted(pieces, layer=None, step=0.02):
    """The area of copper, summed over the layers (or on `layer` alone): each layer's pieces cut by
    scan lines `step` apart, and the lengths of what they cover added up."""
    total = 0.0
    for name in sorted(set().union(*(p["layers"] for p in pieces)) if pieces else []):
        if layer and name != layer:
            continue
        polys = [s for p in pieces if name in p["layers"] for s in shapes(p)]
        boxes = [geom.bbox(s) for s in polys]
        top = max(b[3] for b in boxes)
        step = max(step, (top - min(b[1] for b in boxes)) / 1500)  # a plane needs no finer
        y = min(b[1] for b in boxes) + step / 2
        while y < top:
            spans = []
            for s, b in zip(polys, boxes):
                if not b[1] <= y <= b[3]:
                    continue
                xs = sorted(a[0] + (y - a[1]) * (c[0] - a[0]) / (c[1] - a[1])
                            for a, c in geom.edges(s) if (a[1] > y) != (c[1] > y))
                spans += zip(xs[::2], xs[1::2])
            reach = -math.inf
            for x0, x1 in sorted(spans):
                if x1 > reach:
                    total += (x1 - max(x0, reach)) * step
                    reach = x1
            y += step
    return total


class Joined:
    """Union-find over the pieces of copper."""

    def __init__(self, n):
        self.up = list(range(n))

    def find(self, i):
        while self.up[i] != i:
            self.up[i] = self.up[self.up[i]]
            i = self.up[i]
        return i

    def join(self, i, j):
        self.up[self.find(i)] = self.find(j)


def gap(a, b):
    return geom.distance(a["poly"], b["poly"]) - a["r"] - b["r"]


def grade(case, board, patterns, rules, names):
    """See the module's words. `names` maps a pattern to {the file's pad name: the pattern's}."""
    unread = [c for c in case["checks"] if c not in READ]
    if unread:
        raise kicad.Unsupported(f"the checks {unread}")
    if "refuse" in case["checks"]:
        # a board for a case that has none: graded as any board, to say what is wrong with it, and
        # because one that passed would show the case to be satisfiable after all
        asked = ["parts", "connectivity", "rules", "outline"] + (["layers"] if "track_layers" in case else [])
        as_built = grade({**case, "checks": asked}, board, patterns, rules, names)
        if as_built["outcome"] == "pass":
            raise AssertionError(f"{case['id']} is not unsatisfiable: this board passes")
        as_built["checks"]["refuse"] = {"ok": False, "notes": ["a board was written"]}
        return {**as_built, "outcome": "wrong",
                "why": "A board was written for a case that has none. " + as_built["why"]}
    rule = rules[case["rules"]]
    notes = {c: [] for c in case["checks"]}

    # the outline, and the board moved to lie where the case's does
    want = [tuple(p) for p in case["board"]["outline"]]
    if board["outline"] is None:
        notes["outline"].append("the board has no outline")
    else:
        b, w = geom.bbox(board["outline"]), geom.bbox(want)
        kicad.move(board, w[0] - b[0], w[1] - b[1])
        got = board["outline"]
        if len(got) != len(geom.simplify(want)) or any(
                min(math.dist(p, q) for q in got) > OUTLINE for p in want):
            notes["outline"].append(
                f"the outline is {geom.bbox(got)[2] - geom.bbox(got)[0]:g} × "
                f"{geom.bbox(got)[3] - geom.bbox(got)[1]:g} with {len(got)} corners, not the case's")
    outline = board["outline"]

    # the parts, each found by its reference and laid over its pattern
    by_ref = {}
    for part in board["parts"]:
        if part["pads"]:
            by_ref.setdefault(part["ref"], []).append(part)
    poses, pins, pin_pads = {}, {}, []  # pins: "R1.2" -> its pad (its first, where it has two)
    for p in case["part"]:
        found = by_ref.pop(p["ref"], [])
        if len(found) != 1:
            notes["parts"].append(f"{p['ref']} is on the board {len(found)} times")
            continue
        part = found[0]
        fit = pose(patterns[p["pattern"]], part["pads"], part["side"], names.get(p["pattern"], {}))
        if isinstance(fit, str):
            notes["parts"].append(f"{p['ref']}: {fit}")
            continue
        poses[p["ref"]] = (*fit, part["side"])
        for pad in part["pads"]:
            pin = f"{p['ref']}.{names.get(p['pattern'], {}).get(pad['name'], pad['name'])}"
            pins.setdefault(pin, pad)
            pin_pads.append((pin, pad))
    for ref in by_ref:
        notes["parts"].append(f"{ref} is on the board and not in the case")

    # courtyards: inside the outline, and clear of one another on a shared side
    yards = {ref: courtyard(patterns[p["pattern"]], poses[ref][0], poses[ref][1], poses[ref][2])
             for p in case["part"] if (ref := p["ref"]) in poses}
    refs = sorted(yards)
    if outline:
        for ref in refs:
            if not all(geom.inside(c, outline) or min(geom.point_segment(c, a, b) for a, b in geom.edges(outline)) < 1e-6
                       for c in yards[ref]):
                notes["outline"].append(f"{ref}'s courtyard is not inside the outline")
    for i, a in enumerate(refs):
        for b in refs[i + 1:]:
            if poses[a][2] != poses[b][2]:
                continue  # a courtyard is on its part's side, a through-hole part's too, as KiCad has it
            depth = geom.overlap(yards[a], yards[b])
            if depth > 1e-6:
                notes["outline"].append(f"{a}'s and {b}'s courtyards overlap by {depth:.3f} mm")

    # what the copper joins
    pieces = [dict(pad, pin=pin, ref=pin.split(".")[0]) for pin, pad in pin_pads]
    pieces += [dict(pad, pin=None) for part in board["parts"] for pad in part["pads"]
               if not any(pad is q for _, q in pin_pads)]
    pieces += [dict(t, pin=None) for t in board["tracks"] + board["vias"] + board["zones"]]
    boxes = [geom.bbox(p["poly"], p["r"]) for p in pieces]
    joined = Joined(len(pieces))
    reach = max(rule["clearance"], 0)
    near = []  # pairs on a shared layer close enough to matter
    for i, a in enumerate(pieces):
        for j in range(i + 1, len(pieces)):
            b = pieces[j]
            if a["layers"] & b["layers"] and geom.boxes_within(boxes[i], boxes[j], reach):
                g = gap(a, b)
                near.append((i, j, g))
                if g <= TOUCH:
                    joined.join(i, j)
    first = {}
    for i, p in enumerate(pieces):  # two pads of one pin are joined inside the part
        if p["pin"]:
            joined.join(i, first.setdefault(p["pin"], i))
    net_of = {}
    for net in case["net"]:
        for pin in net["pins"]:
            net_of[pin] = net["name"]
    for pin in pins:
        net_of.setdefault(pin, f"({pin}, unconnected)")
    groups = {}
    for i, p in enumerate(pieces):
        if p["pin"]:
            groups.setdefault(joined.find(i), []).append(p["pin"])
    shorts, opens = [], []
    for members in groups.values():
        nets = sorted({net_of[pin] for pin in members})
        if len(nets) > 1:
            shorts.append(f"{' and '.join(nets)} are shorted")
    for net in case["net"]:
        there = [pin for pin in net["pins"] if pin in pins]
        roots = {joined.find(i) for i, p in enumerate(pieces) if p["pin"] in there}
        if len(there) < len(net["pins"]) or len(roots) > 1:
            opens.append(f"{net['name']} is open")
    notes["connectivity"] += shorts + opens

    # the rule set
    r = notes["rules"]
    for t in board["tracks"]:
        if t["width"] < rule["track"] - SLACK:
            r.append(f"a track {t['width']:g} wide, under {rule['track']:g}")
            break
    for v in board["vias"]:
        if v["drill"] < rule["via_drill"] - 1e-9 or v["size"] < rule["via_pad"] - 1e-9:
            r.append(f"a via {v['size']:g}/{v['drill']:g}, under {rule['via_pad']:g}/{rule['via_drill']:g}")
            break
    worst = min((g for i, j, g in near if joined.find(i) != joined.find(j)), default=math.inf)
    if worst < rule["clearance"] - SLACK:
        n = sum(1 for i, j, g in near if joined.find(i) != joined.find(j) and g < rule["clearance"] - SLACK)
        r.append(f"clearance {worst:.3f} mm, under {rule['clearance']:g}, at {n} place{'s' if n > 1 else ''}")
    used = set().union(*(p["layers"] for p in board["tracks"] + board["zones"])) if board["tracks"] or board["zones"] else set()
    allowed = set(STACK[:rule["layers"]]) if rule["layers"] > 1 else None
    if allowed is not None and not used <= allowed:
        r.append(f"copper on {sorted(used - allowed)}, on a board of {rule['layers']} layers")
    if allowed is None and len(used) > 1:
        r.append(f"copper on {sorted(used)}, on a board of one layer")
    if outline:
        ring = geom.edges(outline)
        for p in pieces:
            d = min(geom.segment_segment(a, b, c, e) for a, b in geom.edges(p["poly"]) for c, e in ring) - p["r"]
            if not geom.inside(p["poly"][0], outline) or d < rule["edge"] - SLACK:
                r.append(f"copper {max(d, 0):.3f} mm from the edge, under {rule['edge']:g}"
                         if geom.inside(p["poly"][0], outline) else "copper outside the outline")
                break

    # what the case places
    for p in case["part"]:
        if p["ref"] not in poses:
            continue
        origin, turn, side = poses[p["ref"]]
        if "at" in p and "fixed" in notes:
            off = math.dist(origin, p["at"])
            dturn = abs((turn - p.get("rotation", 0) + 180) % 360 - 180)
            if off > PLACE or dturn > PLACE:
                notes["fixed"].append(f"{p['ref']} is at ({origin[0]:.3f}, {origin[1]:.3f}) turned {turn:g}°, "
                                      f"not ({p['at'][0]:g}, {p['at'][1]:g}) turned {p.get('rotation', 0):g}°")
        if "side" in notes and side != p.get("side", "top"):
            notes["side"].append(f"{p['ref']} is on the {side}")
    if "layers" in notes:
        only = case["track_layers"]  # the layers by name, or how many, whichever they are
        tracked = set().union(*(t["layers"] for t in board["tracks"])) if board["tracks"] else set()
        if isinstance(only, int):
            if len(tracked) > only:
                notes["layers"].append(f"tracks on {sorted(tracked)}, where the case allows {only} layer{'s' if only > 1 else ''}")
        elif not tracked <= set(only):
            n = sum(1 for t in board["tracks"] if not t["layers"] <= set(only))
            notes["layers"].append(f"{n} tracks on {sorted(tracked - set(only))}, where the case allows tracks on {sorted(only)}")
        if board["vias"] and (only == 1 or (not isinstance(only, int) and len(only) == 1)):
            notes["layers"].append(f"{len(board['vias'])} vias, where the case allows none")

    # the distances the case bounds, copper edge to copper edge
    for n in case.get("near", []) if "near" in notes else []:
        if n["from"] not in pins or n["to"] not in pins:
            notes["near"].append(f"{n['from']} or {n['to']} is not on the board")
            continue
        d = max(gap(pins[n["from"]], pins[n["to"]]), 0)
        if d > n["max"] + SLACK:
            notes["near"].append(f"{n['from']} is {d:.2f} mm from {n['to']}, over {n['max']:g}")

    # the modules laid out alike: each instance the first one, moved and turned (not mirrored)
    for rep in case.get("replica", []) if "replica" in notes else []:
        first, bad = rep["of"][0], []
        if any(ref not in poses for inst in rep["of"] for ref in inst):
            notes["replica"].append("a part of a replica is not on the board")
            continue

        def shape(inst):
            # each part in the frame of the instance's first: where it is, and how it is turned
            (ox, oy), turn0 = poses[inst[0]][0], poses[inst[0]][1]
            return [(*geom.rotate((poses[r][0][0] - ox, poses[r][0][1] - oy), -turn0),
                     poses[r][1] - turn0, poses[r][2]) for r in inst]
        want_shape = shape(first)
        for inst in rep["of"][1:]:
            for (x, y, turn, side), (wx, wy, wturn, wside) in zip(shape(inst), want_shape):
                if (math.hypot(x - wx, y - wy) > PLACE or side != wside
                        or abs((turn - wturn + 180) % 360 - 180) > PLACE):
                    bad.append(inst[0])
                    break
        if bad:
            notes["replica"].append(f"{len(bad)} of {len(rep['of'])} instances are not laid out as "
                                    f"{first[0]}'s is: those of {', '.join(bad[:4])}{' …' if len(bad) > 4 else ''}")

    def copper_of(net):
        """Every piece of copper joined to a pin of the case's net `net`."""
        roots = {joined.find(i) for i, p in enumerate(pieces) if p["pin"] and net_of.get(p["pin"]) == net}
        return [p for i, p in enumerate(pieces) if joined.find(i) in roots]

    measures = {}
    # the loops: along the copper between pins of a net, straight through a part between its pins
    for loop in case.get("loop", []) if "loop" in notes else []:
        path, points = loop["path"], []
        for a, b in zip(path, path[1:] + path[:1]):
            if a not in pins or b not in pins:
                points = None
                notes["loop"].append(f"{loop['name']}: {a} or {b} is not on the board")
                break
            if net_of[a] == net_of[b]:
                leg = way(copper_of(net_of[a]), pins[a], pins[b])
                if leg is None:
                    points = None
                    notes["loop"].append(f"{loop['name']} is open: no copper from {a} to {b}")
                    break
                points += leg
            else:
                points += [pins[a]["at"], pins[b]["at"]]
        if points:
            size = geom.area(points)
            measures[f"loop_mm2 ({loop['name']})"] = round(size, 2)
            if size > loop["max"] + 1e-9:
                notes["loop"].append(f"{loop['name']} encloses {size:.1f} mm², over {loop['max']:g}")

    # nets that keep apart, on any layer
    for rule in case.get("apart", []) if "apart" in notes else []:
        skip = set(rule.get("except", []))
        mine = [p for p in copper_of(rule["net"]) if p.get("ref") not in skip]
        theirs = [p for p in copper_of(rule["from"]) if p.get("ref") not in skip]
        d = min((gap(a, b) for a in mine for b in theirs), default=math.inf)
        if d != math.inf:
            measures[f"apart_mm ({rule['net']} from {rule['from']})"] = round(max(d, 0), 3)
        if d < rule["min"] - SLACK:
            notes["apart"].append(f"{rule['net']} comes within {max(d, 0):.2f} mm of {rule['from']}, under {rule['min']:g}")

    # a net's copper, no more than so much, or no less, on every layer or on one
    for rule in case.get("copper", []) if "copper" in notes else []:
        size = painted(copper_of(rule["net"]), rule.get("layer"))
        where = f"{rule['net']} on {rule['layer']}" if "layer" in rule else rule["net"]
        measures[f"copper_mm2 ({where})"] = round(size, 1)
        if "max" in rule and size > rule["max"] * 1.01:
            notes["copper"].append(f"{where} is {size:.1f} mm² of copper, over {rule['max']:g}")
        if "min" in rule and size < rule["min"] * 0.99:
            notes["copper"].append(f"{where} is {size:.1f} mm² of copper, under {rule['min']:g}")

    # a way at least so wide between two pins: by tracks that wide, by pads, vias and pours, and
    # by a narrower track only within `neck` of a pad too narrow for the width
    for rule in case.get("width", []) if "width" in notes else []:
        a, b = rule["path"]
        if a not in pins or b not in pins:
            notes["width"].append(f"{a} or {b} is not on the board")
            continue
        copper = copper_of(net_of[a])
        small = [p for p in copper if p["pin"] and min(p["w"], p["h"]) < rule["min"]]
        neck = rule.get("neck", 0)

        def wide(p):
            if "width" not in p or p["width"] >= rule["min"] - SLACK:
                return True
            return any(all(math.dist(end, pad["at"]) <= neck for end in p["poly"]) for pad in small)
        narrowest = min((p["width"] for p in copper if "width" in p), default=None)
        if way([p for p in copper if wide(p)], pins[a], pins[b]) is None:
            notes["width"].append(
                f"no way from {a} to {b} is {rule['min']:g} mm wide"
                + (f": the net's narrowest track is {narrowest:g}" if narrowest is not None else ""))

    # the vias of a net, at least so many
    for rule in case.get("vias", []) if "vias" in notes else []:
        if "not_in" in rule:  # no via in a pad of the part named
            pads = [p for p in pieces if p.get("ref") == rule["not_in"] and p["drill"] is None]
            n = sum(1 for v in board["vias"] if any(v["layers"] & p["layers"] and gap(v, p) <= TOUCH for p in pads))
            if n:
                notes["vias"].append(f"{n} vias in pads of {rule['not_in']}")
            continue
        n = sum(1 for p in copper_of(rule["net"]) if "drill" in p and "size" in p)
        measures[f"vias_n ({rule['net']})"] = n
        if n < rule["min"]:
            notes["vias"].append(f"{rule['net']} has {n} vias, under {rule['min']}")

    checks = {c: {"ok": not n, "notes": n} for c, n in notes.items()}
    failed = [c for c in case["checks"] if notes[c]]
    if not failed:
        outcome, why = "pass", ""
    elif failed == ["connectivity"] and not shorts:
        outcome, why = "placed", "; ".join(opens)
    else:
        said = [n for c in failed for n in notes[c]]  # all of it is in `checks`; the summary is the first few
        outcome, why = "wrong", "; ".join(said[:6]) + (f"; and {len(said) - 6} more" if len(said) > 6 else "")
    return {"outcome": outcome, "why": why[:1].upper() + why[1:] + ("." if why else ""), "checks": checks,
            "metrics": {"track_mm": round(sum(t["length"] for t in board["tracks"]), 3),
                        "vias": len(board["vias"]), "layers": len(used), **measures}}
