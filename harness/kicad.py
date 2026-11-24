"""Reads a KiCad board file (.kicad_pcb, KiCad 6 and later) as the grader wants it: its outline,
its parts' pads, its tracks, vias and filled zones, as geometry, in millimetres with y up.

KiCad's y runs down the page and its angles turn counter-clockwise as drawn, so with y negated an
angle here is counter-clockwise too. Net names and numbers in the file are not read: the grader
works out what is joined from the copper. Standard library only."""
import math
import re

import geom

TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


class Unsupported(Exception):
    """The file holds geometry this reader does not read yet. A fault of the harness's, not of
    the board's."""


def parse(text):
    """An S-expression as nested lists of strings."""
    stack, top = [], []
    for tok in TOKEN.findall(text):
        if tok == "(":
            stack.append(top)
            top = []
        elif tok == ")":
            done, top = top, stack.pop()
            top.append(done)
        else:
            top.append(re.sub(r"\\(.)", r"\1", tok[1:-1]) if tok.startswith('"') else tok)
    return top[0]


def all_of(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def one(node, key):
    found = all_of(node, key)
    return found[0] if found else None


def xy(node):
    """A (start x y) or (at x y [angle]) node's point, y up."""
    return (float(node[1]), -float(node[2]))


def copper(layers, every):
    """The copper layers a pad's or via's (layers …) names, of the board's `every`."""
    out = set()
    for name in layers[1:]:
        if name == "*.Cu":
            out |= set(every)
        elif name == "F&B.Cu":
            out |= {"F.Cu", "B.Cu"}
        elif name.endswith(".Cu"):
            out.add(name)
    return frozenset(out)


def pad_shape(shape, centre, w, h, angle, ratio):
    """A pad as (polygon, radius)."""
    if shape == "circle":
        return [centre], w / 2
    if shape == "oval":
        r = min(w, h) / 2
        half = geom.rotate(((w - h) / 2, 0) if w >= h else (0, (h - w) / 2), angle)
        if max(w, h) - 2 * r < 1e-9:
            return [centre], r
        return [(centre[0] - half[0], centre[1] - half[1]), (centre[0] + half[0], centre[1] + half[1])], r
    if shape == "roundrect":
        r = ratio * min(w, h)
        return geom.rect(centre[0], centre[1], w - 2 * r, h - 2 * r, angle), r
    if shape == "rect":
        return geom.rect(centre[0], centre[1], w, h, angle), 0.0
    raise Unsupported(f"a pad of shape {shape}")


def arc_points(start, mid, end, step=4.0):
    """An arc through three points as a run of points no more than `step` degrees apart: its
    chords lie within a thousandth of the radius of it."""
    (ax, ay), (bx, by), (cx, cy) = start, mid, end
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return [start, end]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0, a1, a2 = (math.atan2(y - uy, x - ux) for x, y in (start, mid, end))
    sweep = (a2 - a0) % (2 * math.pi)
    if (a1 - a0) % (2 * math.pi) > sweep:  # the middle is the other way round
        sweep -= 2 * math.pi
    n = max(2, math.ceil(abs(math.degrees(sweep)) / step))
    return [start] + [(ux + r * math.cos(a0 + sweep * i / n), uy + r * math.sin(a0 + sweep * i / n))
                      for i in range(1, n)] + [end]


def outline_loop(segments):
    """The Edge.Cuts segments chained into one closed loop of points."""
    if not segments:
        return None
    segments = list(segments)
    loop = list(segments.pop(0))
    while segments:
        for i, (a, b) in enumerate(segments):
            if math.dist(a, loop[-1]) < 1e-3:
                loop.append(b)
            elif math.dist(b, loop[-1]) < 1e-3:
                loop.append(a)
            else:
                continue
            segments.pop(i)
            break
        else:
            raise Unsupported("an outline of more than one loop, or an open one")
    if math.dist(loop[0], loop[-1]) > 1e-3:
        raise Unsupported("an outline that does not close")
    return geom.simplify(loop[:-1])


def load(path):
    """The board at `path`: {"layers", "outline", "parts", "tracks", "vias", "zones"}.

    A part is {"ref", "side", "rotation", "pads"}; a pad {"name", "at", "w", "h", "angle", "drill",
    "poly", "r", "layers"}. A track, via or zone is a piece of copper: {"poly", "r", "layers"}, a
    track with its "width" and "length", a via with its "size" and "drill"."""
    with open(path, encoding="utf-8") as f:
        root = parse(f.read())
    if root[0] != "kicad_pcb":
        raise Unsupported("a file that is not a KiCad board")
    every = [l[1] for l in one(root, "layers")[1:] if isinstance(l, list) and l[1].endswith(".Cu")]

    edge = []
    for kind in ("gr_line", "gr_rect", "gr_poly", "gr_arc", "gr_circle", "gr_curve"):
        for g in all_of(root, kind):
            if one(g, "layer")[1] != "Edge.Cuts":
                continue
            if kind == "gr_line":
                edge.append((xy(one(g, "start")), xy(one(g, "end"))))
            elif kind == "gr_rect":
                (x0, y0), (x1, y1) = xy(one(g, "start")), xy(one(g, "end"))
                c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
                edge += [(c[i], c[(i + 1) % 4]) for i in range(4)]
            elif kind == "gr_poly":
                pts = [xy(p) for p in all_of(one(g, "pts"), "xy")]
                edge += [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
            elif kind == "gr_arc":
                pts = arc_points(xy(one(g, "start")), xy(one(g, "mid")), xy(one(g, "end")))
                edge += list(zip(pts, pts[1:]))
            else:
                raise Unsupported(f"an outline with a {kind[3:]}")

    parts = []
    for fp in all_of(root, "footprint"):
        at = one(fp, "at")
        origin, rot = xy(at), float(at[3]) if len(at) > 3 else 0.0
        ref = next((p[2] for p in all_of(fp, "property") if p[1] == "Reference"), None)
        if ref is None:
            ref = next((t[2] for t in all_of(fp, "fp_text") if t[1] == "reference"), "?")
        pads = []
        for pad in all_of(fp, "pad"):
            layers = copper(one(pad, "layers"), every)
            if not layers:
                continue  # paste or mask alone
            pat = one(pad, "at")
            local = (float(pat[1]), -float(pat[2]))
            angle = float(pat[3]) if len(pat) > 3 else 0.0  # absolute: the part's turn is in it
            turned = geom.rotate(local, rot)
            centre = (origin[0] + turned[0], origin[1] + turned[1])
            size = one(pad, "size")
            w, h = float(size[1]), float(size[2])
            drill = one(pad, "drill")
            if drill and drill[1] == "oval":
                raise Unsupported("a slotted hole")
            ratio = one(pad, "roundrect_rratio")
            poly, r = pad_shape(pad[3], centre, w, h, angle, float(ratio[1]) if ratio else 0.25)
            pads.append({"name": pad[1], "kind": pad[2], "at": centre, "w": w, "h": h, "angle": angle,
                         "drill": float(drill[1]) if drill and len(drill) > 1 else None,
                         "poly": poly, "r": r, "layers": layers})
        parts.append({"ref": ref, "footprint": fp[1], "rotation": rot,
                      "side": "bottom" if one(fp, "layer")[1] == "B.Cu" else "top", "pads": pads})

    tracks = []
    for s in all_of(root, "segment"):
        a, b, w = xy(one(s, "start")), xy(one(s, "end")), float(one(s, "width")[1])
        tracks.append({"poly": [a, b], "r": w / 2, "width": w, "length": math.dist(a, b),
                       "layers": frozenset([one(s, "layer")[1]])})
    for s in all_of(root, "arc"):  # a track that is an arc, as its chords
        pts, w = arc_points(xy(one(s, "start")), xy(one(s, "mid")), xy(one(s, "end"))), float(one(s, "width")[1])
        for a, b in zip(pts, pts[1:]):
            tracks.append({"poly": [a, b], "r": w / 2, "width": w, "length": math.dist(a, b),
                           "layers": frozenset([one(s, "layer")[1]])})
    vias = []
    for v in all_of(root, "via"):
        size = float(one(v, "size")[1])
        vias.append({"poly": [xy(one(v, "at"))], "r": size / 2, "size": size,
                     "drill": float(one(v, "drill")[1]), "layers": copper(one(v, "layers"), every)})
    zones = []
    for z in all_of(root, "zone"):
        for f in all_of(z, "filled_polygon"):
            zones.append({"poly": [xy(p) for p in all_of(one(f, "pts"), "xy")], "r": 0.0,
                          "layers": frozenset([one(f, "layer")[1]])})
    return {"layers": every, "outline": outline_loop(edge), "parts": parts, "tracks": tracks,
            "vias": vias, "zones": zones}


def move(board, dx, dy):
    """The board moved by (dx, dy), in place."""
    def m(p):
        return (p[0] + dx, p[1] + dy)
    if board["outline"]:
        board["outline"] = [m(p) for p in board["outline"]]
    for part in board["parts"]:
        for pad in part["pads"]:
            pad["at"], pad["poly"] = m(pad["at"]), [m(p) for p in pad["poly"]]
    for piece in board["tracks"] + board["vias"] + board["zones"]:
        piece["poly"] = [m(p) for p in piece["poly"]]
