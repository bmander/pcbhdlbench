"""Makes a board for the playground of a KiCad board: its outline, its pads and their nets.

    python3 playground/boards/import.py board.kicad_pcb out.json --title … --maker … \\
        --license … --license-url … --source … [--pour GND] [--note …] [--pitch 0.3]

Nothing of the board's own routing is kept: the tracks, vias and pours are left out, and the
playground's routers start from the pads. A pad is kept as a rectangle or a circle of its size
(one at an odd angle as a circle of its lesser size), on the top, the bottom or through; a hole
with no copper as a pad of no net; a net of one pad as no net. The outline is the largest closed
loop of the edge cuts, its arcs and curves as short straight pieces. `--pour` names the net the
real board joins with a pour or a plane, which the playground can leave unrouted.

An Eagle board (.brd, XML) goes through KiCad first:  kicad-cli pcb import --format eagle -o b.kicad_pcb b.brd

Standard library only, with the harness's reader of KiCad's files."""
import argparse
import collections
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "harness"))
import geom
import kicad
from kicad import all_of, one


def bezier(p, n=8):
    def at(t):
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        return (a * p[0][0] + b * p[1][0] + c * p[2][0] + d * p[3][0], a * p[0][1] + b * p[1][1] + c * p[2][1] + d * p[3][1])
    return [at(i / n) for i in range(n + 1)]


def edge_pieces(node, place=lambda p: p, prefix="gr"):
    """The edge cuts of a board (or of a footprint, placed): straight pieces, and the circles."""
    pieces, circles = [], []
    for kind in ("line", "arc", "rect", "poly", "curve", "circle"):
        for g in all_of(node, f"{prefix}_{kind}"):
            if one(g, "layer")[1] != "Edge.Cuts":
                continue
            pt = lambda key: place((float(one(g, key)[1]), float(one(g, key)[2])))
            if kind == "line":
                pieces.append((pt("start"), pt("end")))
            elif kind == "arc":
                pts = kicad.arc_points(pt("start"), pt("mid"), pt("end"), 8.0)
                pieces += list(zip(pts, pts[1:]))
            elif kind == "rect":
                (x0, y0), (x1, y1) = pt("start"), pt("end")
                c = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
                pieces += [(c[i], c[(i + 1) % 4]) for i in range(4)]
            elif kind in ("poly", "curve"):
                pts = [place((float(q[1]), float(q[2]))) for q in all_of(one(g, "pts"), "xy")]
                pts = bezier(pts) if kind == "curve" else pts + pts[:1]
                pieces += list(zip(pts, pts[1:]))
            else:
                c, e = pt("center"), pt("end")
                circles.append((c, math.dist(c, e)))
    return pieces, circles


def loops(pieces, tol=0.01):
    """The pieces chained end to end into closed loops; what does not close is dropped."""
    left, out = [p for p in pieces if math.dist(*p) > 1e-6], []
    while left:
        loop = list(left.pop())
        grew = True
        while grew and (len(loop) < 3 or math.dist(loop[0], loop[-1]) > tol):  # a piece may be shorter than the tolerance
            grew = False
            for i, (a, b) in enumerate(left):
                if math.dist(a, loop[-1]) < tol:
                    loop.append(b)
                elif math.dist(b, loop[-1]) < tol:
                    loop.append(a)
                else:
                    continue
                left.pop(i)
                grew = True
                break
        if len(loop) > 3 and math.dist(loop[0], loop[-1]) <= tol:
            out.append(loop[:-1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("out")
    for name in ("title", "maker", "license", "license-url", "source", "note", "pour"):
        ap.add_argument(f"--{name}", default="")
    ap.add_argument("--pitch", type=float, default=0.15, help="the grid: 0.15 for a board with fine-pitch parts, 0.3 for a large one without")
    args = ap.parse_args()
    root = kicad.parse(pathlib.Path(args.board).read_text())

    pieces, circles = edge_pieces(root)
    pads = []   # (x, y, w, h, side, round, net name or None), in KiCad's frame, y down
    for fp in all_of(root, "footprint"):
        at = one(fp, "at")
        fx, fy, rot = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0

        def place(p, fx=fx, fy=fy, rot=rot):
            x, y = geom.rotate((p[0], -p[1]), rot)   # KiCad turns counter-clockwise as drawn, y down
            return (fx + x, fy - y)
        more, rings = edge_pieces(fp, place, "fp")
        pieces += more
        circles += rings
        for pad in all_of(fp, "pad"):
            layers = [l for l in one(pad, "layers")[1:]] if one(pad, "layers") else []
            top = any(l in ("F.Cu", "*.Cu", "F&B.Cu") for l in layers)
            bottom = any(l in ("B.Cu", "*.Cu", "F&B.Cu") for l in layers)
            drill = one(pad, "drill")
            hole = max([float(v) for v in drill[1:] if v.replace(".", "").isdigit()], default=0.0) if drill else 0.0
            pat = one(pad, "at")
            x, y = place((float(pat[1]), float(pat[2])))
            size = one(pad, "size")
            w, h = float(size[1]), float(size[2])
            if pad[2] == "np_thru_hole" or not (top or bottom):
                if hole > 0:
                    pads.append((x, y, hole, hole, 2, True, None))
                continue
            turn = (float(pat[3]) if len(pat) > 3 else 0.0) % 180
            round_ = pad[3] == "circle" or (pad[3] == "oval" and abs(w - h) < 1e-6)
            if abs(turn - 90) < 1:
                w, h = h, w
            elif 1 < turn < 179:
                w = h = min(w, h)
                round_ = True
            net = one(pad, "net")
            name = net[-1] if net and net[-1] not in ("", "0") else None
            pads.append((x, y, w, h, 2 if top and bottom else 0 if top else 1, round_, name))

    closed = loops(pieces)
    if closed:
        outline = max(closed, key=geom.area)
    else:   # no edge that closes: a box round the pads
        xs, ys = [p[0] for p in pads], [p[1] for p in pads]
        outline = [(min(xs) - 3, min(ys) - 3), (max(xs) + 3, min(ys) - 3), (max(xs) + 3, max(ys) + 3), (min(xs) - 3, max(ys) + 3)]
    for inner in closed:   # a cutout, as a hole of its size
        if inner is not outline:
            b = geom.bbox(inner)
            if b[2] - b[0] < 20 and b[3] - b[1] < 20 and geom.inside(inner[0], outline):
                pads.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b[2] - b[0], b[3] - b[1], 2, False, None))
    for c, r in circles:
        if geom.inside(c, outline):
            pads.append((c[0], c[1], 2 * r, 2 * r, 2, True, None))

    raw = outline
    x0, y0, x1, y1 = geom.bbox(outline)
    r = lambda v: round(v, 3)
    move = lambda p: [r(p[0] - x0), r(y1 - p[1])]   # the playground's frame: the origin lower left, y up
    outline = geom.simplify([tuple(move(p)) for p in outline], 1e-4)
    count = collections.Counter(p[6] for p in pads if p[6])
    names = sorted((n for n, k in count.items() if k > 1), key=lambda n: (-count[n], n))
    index = {n: i for i, n in enumerate(names)}
    # a file may hold several boards (a keyboard's two halves): the pads of the outline's alone
    inside = [p for p in pads if geom.inside((p[0], p[1]), raw)]
    board = {
        "title": args.title, "maker": args.maker, "license": args.license, "license_url": args.license_url,
        "source": args.source, "note": args.note,
        "width": r(x1 - x0), "height": r(y1 - y0),
        "outline": [list(p) for p in outline] if len(outline) != 4 else [],
        "track": 0.15, "clearance": 0.15, "via": 0.6, "edge": 0.3, "pitch": args.pitch,
        "nets": names, "pour": index.get(args.pour) if args.pour else None,
        "pads": [{"x": move(p)[0], "y": move(p)[1], "w": r(p[2]), "h": r(p[3]), "side": p[4], "round": p[5],
                  "net": index.get(p[6], -1)} for p in inside],
    }
    pathlib.Path(args.out).write_text(json.dumps(board, separators=(",", ":")) + "\n")
    print(f"{args.out}: {board['width']} x {board['height']} mm, {len(board['pads'])} pads, {len(names)} nets, "
          f"an outline of {len(outline)} corners" + (f", {args.pour} is net {board['pour']}" if args.pour else ""))


main()
