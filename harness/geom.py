"""The geometry the grader needs: how far apart two pieces of copper are.

A piece of copper is a polygon grown by a radius: a round pad is a point and its radius, a track
two points and half its width, a rectangular pad four corners and no radius, a rounded one its
inner rectangle and its corner radius. The gap between two pieces is the distance between their
polygons less both radii; they touch where it is not positive. Standard library only."""
import math


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def point_segment(p, a, b):
    """The distance from point `p` to segment `ab`."""
    d = sub(b, a)
    n = d[0] * d[0] + d[1] * d[1]
    t = 0 if n == 0 else max(0, min(1, ((p[0] - a[0]) * d[0] + (p[1] - a[1]) * d[1]) / n))
    return math.hypot(p[0] - a[0] - t * d[0], p[1] - a[1] - t * d[1])


def segments_cross(a, b, c, d):
    """Whether segments `ab` and `cd` properly cross (touching ends are caught by distance 0)."""
    d1, d2 = cross(sub(b, a), sub(c, a)), cross(sub(b, a), sub(d, a))
    d3, d4 = cross(sub(d, c), sub(a, c)), cross(sub(d, c), sub(b, c))
    return d1 * d2 < 0 and d3 * d4 < 0


def segment_segment(a, b, c, d):
    if segments_cross(a, b, c, d):
        return 0.0
    return min(point_segment(a, c, d), point_segment(b, c, d),
               point_segment(c, a, b), point_segment(d, a, b))


def edges(poly):
    """A polygon's edges: a point's is itself twice, a segment's the one, a polygon's closed."""
    if len(poly) == 1:
        return [(poly[0], poly[0])]
    if len(poly) == 2:
        return [(poly[0], poly[1])]
    return [(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))]


def inside(p, poly):
    """Whether point `p` is inside the simple polygon `poly` (three points or more)."""
    if len(poly) < 3:
        return False
    hit = False
    for a, b in edges(poly):
        if (a[1] > p[1]) != (b[1] > p[1]):
            if p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
                hit = not hit
    return hit


def distance(p, q):
    """The distance between two polygons (points, segments or simple polygons): 0 where they
    overlap."""
    if inside(p[0], q) or inside(q[0], p):
        return 0.0
    return min(segment_segment(a, b, c, d) for a, b in edges(p) for c, d in edges(q))


def bbox(poly, r=0.0):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return (min(xs) - r, min(ys) - r, max(xs) + r, max(ys) + r)


def boxes_within(a, b, d):
    return a[0] - d <= b[2] and b[0] - d <= a[2] and a[1] - d <= b[3] and b[1] - d <= a[3]


def area(poly):
    return abs(sum(cross(a, b) for a, b in edges(poly))) / 2


def overlap(p, q):
    """How deep two convex polygons overlap: the least distance one must move to part them, by
    the separating axes; 0 or less where they only touch or are apart."""
    depth = math.inf
    for poly in (p, q):
        for a, b in edges(poly):
            n = (b[1] - a[1], a[0] - b[0])
            length = math.hypot(*n)
            if length == 0:
                continue
            n = (n[0] / length, n[1] / length)
            ps = [v[0] * n[0] + v[1] * n[1] for v in p]
            qs = [v[0] * n[0] + v[1] * n[1] for v in q]
            depth = min(depth, min(max(ps), max(qs)) - max(min(ps), min(qs)))
    return depth


def rotate(p, degrees):
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def rect(cx, cy, w, h, degrees=0.0):
    """A w × h rectangle's corners, turned counter-clockwise about its centre (cx, cy)."""
    return [(cx + x, cy + y) for x, y in
            (rotate(c, degrees) for c in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)))]


def simplify(poly, eps=1e-6):
    """A closed polygon less its repeated and collinear points."""
    out = [p for i, p in enumerate(poly) if math.dist(p, poly[i - 1]) > eps]
    keep = []
    for i, p in enumerate(out):
        a, b = out[i - 1], out[(i + 1) % len(out)]
        if abs(cross(sub(p, a), sub(b, p))) > eps:
            keep.append(p)
    return keep
