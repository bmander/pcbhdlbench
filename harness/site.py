"""Renders the board: site/, static pages from cases/, toolchains.json, landscape.json and results/.

    python3 harness/site.py && python3 -m http.server -d site

Standard library only (Python 3.11+, for tomllib). Every page is written whole here; the one script
the pages carry is the cases' filter."""
import html
import json
import math
import pathlib
import shutil
import tomllib

import geom
import grade
import kicad
import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
REPO = "https://github.com/bmander/pcbhdlbench"

# the categories, in the order the board shows them, and what each asks
CATEGORIES = {
    "basics": "The first boards: can the toolchain read a design, place, route and write a board at all",
    "placement": "Parts where the design says they must be: near a pin, on an edge, out of a keepout",
    "routing": "Crossings, buses, channels, mazes and fanouts: the router alone",
    "power": "Width for current, pours and planes, loops, Kelvin and star connections",
    "highspeed": "Differential pairs, impedance, matched lengths, return paths",
    "rules": "The rules a board house and a safety standard set: clearance, creepage, rings, edges",
    "outline": "Boards that are not rectangles, and the standard shapes with parts at fixed places",
    "reuse": "A module laid out once and used many times: what an HDL's hierarchy should buy",
    "parametric": "Layouts that follow from a number: rings, grids, ladders",
    "unsatisfiable": "Boards that cannot be made. The right answer is a refusal that says why",
    "integration": "Whole real boards, from a 555 blinker to a single-board computer",
}

# what each check a case may name asks of the board the toolchain wrote
CHECKS = {
    "parts": "Every part of the case is on the board once, with its land pattern's pads, and no other part is",
    "connectivity": "The copper joins exactly the pins each net names: no net open, no two nets shorted",
    "rules": "The case's rule set holds: track width, clearance, drills, annular rings, distance from the edge",
    "outline": "The board's outline is the case's, and every part's courtyard lies inside it and overlaps no other",
    "fixed": "The parts the case places are where it places them, to 0.01 mm, at the rotation it gives",
    "side": "Each part is on the side of the board the case names",
    "layers": "Copper is only on the layers the case allows",
    "near": "The distances the case bounds between pads, parts or tracks are within their bounds",
    "keepout": "The regions the case closes to parts or copper are empty of them",
    "width": "Between the pins the case names there is a way along the copper at least as wide as it asks",
    "length": "The nets the case names have the lengths it asks, or match one another as closely as it asks",
    "pair": "Each differential pair runs coupled at the case's width and gap, its two tracks matched",
    "impedance": "A track's impedance, computed by the harness from its width and the case's stackup, is what the case asks",
    "reference": "The nets the case names run over unbroken copper of their reference net",
    "pour": "The pours and planes the case asks for are there, joined to their nets, with no dead islands",
    "vias": "The vias the case counts are there: stitching, thermal, return, or enough for a current",
    "creepage": "The shortest path over the board's surface between the conductors the case separates is long enough",
    "loop": "The loop the case names encloses no more area than it allows",
    "replica": "The instances of a module the case names are congruent, parts and tracks",
    "pattern": "The parts the case arrays are at the positions its rule gives",
    "apart": "The nets the case keeps apart come no nearer one another than it allows, on any layer",
    "copper": "The copper of a net the case names, pads, tracks and pours together, is no more than the area it allows, or no less than the area it asks",
    "refuse": "No board can satisfy the case, and the toolchain says so",
}

OUTCOMES = ["pass", "placed", "refused", "wrong", "crashed", "timeout", "missing"]

esc = html.escape


def read_cases():
    """Every case, by id (`category/name`), in the categories' order then by title."""
    cases = []
    for path in sorted((ROOT / "cases").glob("*/*.md")):
        text = path.read_text()
        _, header, body = text.split("+++", 2)
        case = tomllib.loads(header)
        case["category"] = path.parent.name
        case["id"] = f"{path.parent.name}/{path.stem}"
        case["body"] = body.strip()
        for check in case["checks"]:
            if check not in CHECKS:
                raise SystemExit(f"{case['id']}: unknown check {check!r}")
        if case["category"] not in CATEGORIES:
            raise SystemExit(f"{case['id']}: unknown category")
        cases.append(case)
    patterns = tomllib.loads((ROOT / "patterns.toml").read_text())
    for case in cases:
        if case["status"] != "specified":
            continue
        outline = [tuple(p) for p in case["board"]["outline"]]
        yards = {p["ref"]: grade.courtyard(patterns[p["pattern"]], tuple(p["at"]), p.get("rotation", 0),
                                           p.get("side", "top")) for p in case["part"] if "at" in p}
        for ref, yard in yards.items():
            if not all(geom.inside(c, outline) for c in yard):
                raise SystemExit(f"{case['id']}: it places {ref} with its courtyard outside the outline")
        for a in yards:
            for b in yards:
                if a < b and geom.overlap(yards[a], yards[b]) > 1e-6:
                    raise SystemExit(f"{case['id']}: it places {a} and {b} with their courtyards overlapping")
    order = list(CATEGORIES)
    cases.sort(key=lambda c: (order.index(c["category"]), c["status"] != "specified", c["title"]))
    return cases


def read_results():
    """results/<toolchain>.json, each {"cases": {id: {"outcome": …}}}, by toolchain."""
    return {p.stem: json.loads(p.read_text()).get("cases", {})
            for p in sorted((ROOT / "results").glob("*.json"))}


def read_runs():
    """Each results file's version and date, by toolchain."""
    return {p.stem: {k: v for k, v in json.loads(p.read_text()).items() if k != "cases"}
            for p in sorted((ROOT / "results").glob("*.json"))}


def board_svg(case, path):
    """A toolchain's board, drawn from its file: the outline, the pads, the tracks and the vias,
    the top copper over the bottom, laid where the case's outline lies."""
    try:
        board = kicad.load(path)
    except kicad.Unsupported as e:
        return f"<p class=muted>The harness cannot draw this board: it has {esc(str(e))}.</p>"
    want = [tuple(p) for p in case["board"]["outline"]]
    xs, ys = [p[0] for p in want], [p[1] for p in want]
    if board["outline"]:
        bx, by = min(p[0] for p in board["outline"]), min(p[1] for p in board["outline"])
        kicad.move(board, min(xs) - bx, min(ys) - by)
    m = 2
    x0, y0, w, h = min(xs) - m, min(ys) - m, max(xs) - min(xs) + 2 * m, max(ys) - min(ys) + 2 * m
    flip = min(ys) + max(ys)

    def pts(poly):
        return " ".join(f"{x:.3f},{flip - y:.3f}" for x, y in poly)

    def piece(p, cls):
        poly, r = p["poly"], p["r"]
        if len(poly) == 1:
            return f"<circle class='{cls}' cx='{poly[0][0]:.3f}' cy='{flip - poly[0][1]:.3f}' r='{r:g}'/>"
        if len(poly) == 2:
            return f"<polyline class='{cls} line' points='{pts(poly)}' stroke-width='{2 * r:g}'/>"
        return (f"<polygon class='{cls}{' line' if r else ''}' points='{pts(poly)}'"
                f"{f' stroke-width="{2 * r:g}"' if r else ''}/>")

    out = [f"<polygon class=edge points='{pts(board['outline'] or want)}'/>"]
    pads = [pad for part in board["parts"] for pad in part["pads"]]
    for layer, cls in (("B.Cu", "bottom"), ("F.Cu", "top")):
        out += [piece(z, cls) for z in board["zones"] if layer in z["layers"]]
        out += [piece(t, cls) for t in board["tracks"] if layer in t["layers"]]
        out += [piece(p, cls + " land") for p in pads if layer in p["layers"] and len(p["layers"]) == 1]
    for p in pads:
        if len(p["layers"]) > 1:
            out.append(piece(p, "through"))
        if p["drill"]:
            out.append(f"<circle class=hole cx='{p['at'][0]:.3f}' cy='{flip - p['at'][1]:.3f}' r='{p['drill'] / 2:g}'/>")
    for v in board["vias"]:
        c = v["poly"][0]
        out.append(piece(v, "through") + f"<circle class=hole cx='{c[0]:.3f}' cy='{flip - c[1]:.3f}' r='{v['drill'] / 2:g}'/>")
    for part in board["parts"]:
        if part["pads"]:
            cx = sum(p["at"][0] for p in part["pads"]) / len(part["pads"])
            cy = sum(p["at"][1] for p in part["pads"]) / len(part["pads"])
            out.append(f"<text class=ref x='{cx:.3f}' y='{flip - cy + 0.35:.3f}'>{esc(part['ref'])}</text>")
    scale = min(24, 760 / w)
    return (f"<svg class='outline built' viewBox='{x0:g} {y0:g} {w:g} {h:g}' width='{w * scale:.0f}'"
            f" height='{h * scale:.0f}' role=img aria-label='The board as laid out'>{''.join(out)}</svg>"
            "<p class=legend><span class=key><span class=top></span>top copper</span>"
            "<span class=key><span class=bottom></span>bottom copper</span>"
            "<span class=key><span class=through></span>through both</span></p>")


def page(path, title, body, current=None, description=None):
    """Writes one page; `path` is relative to the site, and its links are made relative to it."""
    up = "../" * path.count("/")
    nav = [("index.html", "pcbhdl-bench"), ("cases.html", "Cases"), ("toolchains.html", "Toolchains"),
           ("prior.html", "Prior work"), (REPO, "Source")]
    links = "".join(
        f"<a href='{href if href.startswith('http') else up + href}'"
        f"{' aria-current=page' if href == current else ''}>{label}</a>" for href, label in nav)
    meta = f"<meta name=description content='{esc(description, quote=True)}'>\n" if description else ""
    out = SITE / path
    out.write_text(
        "<!doctype html><html lang=en><head><meta charset=utf-8>\n"
        "<meta name=viewport content='width=device-width, initial-scale=1'>\n"
        f"<title>{esc(title)}</title>\n{meta}"
        f"<link rel=stylesheet href='{up}style.css'>\n"
        f"<link rel=icon href='{up}favicon.svg' type='image/svg+xml'>\n"
        f"</head><body>\n<nav class=top>{links}</nav>\n{body}\n</body></html>\n")


def badge(status):
    return f"<span class='badge {status}'>{status}</span>"


def outcome_cell(result):
    if not result:
        return "<td class='cell missing'>·</td>"
    return (f"<td class='cell {result['outcome']}' title='{esc(result.get('why', ''), quote=True)}'>"
            f"{result['outcome']}</td>")


def checks_html(case):
    return "<div class=checks>" + "".join(
        f"<span title='{esc(CHECKS[c], quote=True)}'>{c}</span>" for c in case["checks"]) + "</div>"


def first_sentences(text, limit=220):
    """The opening of a description, for the cases' table: its first paragraph, cut at a sentence."""
    para = " ".join(text.split("\n\n")[0].split())
    if len(para) <= limit:
        return para
    cut = para.rfind(". ", 0, limit)
    return para[:cut + 1] if cut > 0 else para[:limit] + "…"


def index(cases, toolchains, results, runs):
    specified = sum(c["status"] == "specified" for c in cases)
    rows = []
    for cat, about in CATEGORIES.items():
        mine = [c for c in cases if c["category"] == cat]
        cells = ""
        for t in toolchains:
            got = results.get(t["name"], {})
            n = sum(got.get(c["id"], {}).get("outcome") == "pass" for c in mine)
            ran = sum(c["id"] in got for c in mine)
            cells += (f"<td class='num{' pass' if ran and n == ran else ''}'>"
                      f"{f'{n} / {ran}' if ran else '<span class=muted>–</span>'}</td>"
                      if t["name"] in results else "<td class='num missing'>·</td>")
        ready = sum(c["status"] == "specified" for c in mine)
        rows.append(f"<tr><td class=name><a href='cases.html#{cat}'>{cat}</a></td>"
                    f"<td class=num>{len(mine)}</td><td class=num>{ready}</td>"
                    f"<td class=desc>{esc(about)}</td>{cells}</tr>")
    heads = "".join(f"<th class='num k'>{esc(t['name'])}</th>" for t in toolchains)
    ran_words = " ".join(
        f"{esc(name)} has run {len(got)} and passes {sum(r['outcome'] == 'pass' for r in got.values())}"
        f" ({esc(runs[name].get('version', ''))}, {runs[name].get('ran', '')})." for name, got in results.items())
    if not results:
        ran_words = "No toolchain has run yet."
    body = f"""<h1>pcbhdl-bench</h1>
<p class=lede>Rosetta Code for PCB HDLs. Each case describes a circuit board in words: its parts,
its nets, its outline and what its layout must respect. Each toolchain writes the board in its own
language and lays it out, and every result is graded the same way, from the copper it drew. A
refusal ranks above a wrong board, and no toolchain ranks above another.</p>

<h2>What is a PCB HDL?</h2>
<p class=prose>A hardware description language for circuit boards states a design as text: parts,
the nets that join their pins, modules built of both and used again, and constraints. It takes the
place of the drawn schematic. Several now exist (tscircuit, atopile, Zener, SKiDL, JITX and
others), in TypeScript, Python, Starlark and languages of their own.</p>
<p class=prose>A netlist is not a board. Between them is the layout: where each part sits and where
each track runs, under the rules of the board house and of physics. Most of these languages stop
at the netlist and hand the layout to a person in KiCad. A few place and route by themselves, and
more and more an LLM agent is asked to. This bench asks each of them the same thing: here is a
board, described; lay it out.</p>

<h2>The board</h2>
<p class=prose><b>Early days.</b> This is the first slate of cases:
{len(cases)} in {len(CATEGORIES)} categories, {specified} of them <span class='badge specified'>specified</span>
down to the netlist, and the rest each a <span class='badge sketch'>sketch</span> of a paragraph, to
be argued over before it is pinned down. Only a specified case can be run. {ran_words} Under each
toolchain is how many of the cases it ran it passes. The <a href='toolchains.html'>toolchains not yet
entered</a> are listed with what each can do.</p>
<div class=scroll><table>
<thead><tr><th>Category</th><th class=num>Cases</th><th class=num>Specified</th><th>What it asks</th>{heads}</tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>

<h2>How a board is graded</h2>
<p class=prose>A runner reads nothing but its own implementation of the case and writes a board, as
a KiCad <code>.kicad_pcb</code> file. The harness reads the file's geometry (pads, tracks, vias,
zones, the outline) and trusts nothing else in it: not its net names, not a DRC report. From the
copper alone it works out what is joined to what, and checks what the case asks. Every case asks
at least these four:</p>
<ul class=prose>
{''.join(f"<li><b>{c}.</b> {esc(CHECKS[c])}.</li>" for c in ['parts', 'connectivity', 'rules', 'outline'])}
</ul>
<p class=prose>A board <b>passes</b> when every check its case names holds. One whose parts are
legally placed but whose nets are not all routed is <b>placed</b>, which is something. A toolchain
that says it cannot lay the board out has <b>refused</b>; one that writes a board with a short, a
wrong part or a broken rule is <b>wrong</b>, which ranks below refusing. For the
<a href='cases.html#unsatisfiable'>unsatisfiable</a> cases, refusing is passing. Track length, via
count and time are reported and not graded. The rules in full are in
<a href='{REPO}/blob/main/SPEC.md'>SPEC.md</a>.</p>

<h2>How it differs from what exists</h2>
<p class=prose>The benchmarks of PCB layout so far give one canonical file (a KiCad board, an EAGLE
netlist, a Zener design) to an agent or a router. Here a case is a description, not a file, so the
language is under test with the layout: whether a design's hierarchy carries into replicated
layout, whether a ring of sixty LEDs is one number away from a ring of twelve, whether a constraint
can be said at all. And the cases are small and made to isolate one difficulty each, with
<a href='prior.html'>the real boards</a> left to the benchmarks that have hundreds of them.</p>"""
    page("index.html", "pcbhdl-bench", body, "index.html",
         "A neutral conformance suite for PCB HDLs: the same boards, described in words, laid out by every toolchain, graded from the copper.")


def cases_page(cases, results):
    cats = "".join(f"<button type=button class=chip aria-pressed=false data-cat='{c}'>{c}</button>"
                   for c in CATEGORIES)
    rows = []
    last = None
    for c in cases:
        anchor = f" id='{c['category']}'" if c["category"] != last else ""
        last = c["category"]
        hay = " ".join([c["id"], c["title"], *c["tags"], *c["checks"], c["status"]]).lower()
        rows.append(
            f"<tr{anchor} data-cat='{c['category']}' data-hay='{esc(hay, quote=True)}'>"
            f"<td class=case><a href='cases/{c['id']}.html'>{esc(c['title'])}</a>"
            f"<small>{c['id']}</small></td>"
            f"<td>{badge(c['status'])}</td><td class=num>{c['layers']}</td>"
            f"<td>{checks_html(c)}</td><td class=desc>{esc(first_sentences(c['body']))}</td>"
            + "".join(outcome_cell(got.get(c["id"])) for got in results.values()) + "</tr>")
    body = f"""<h1>Cases</h1>
<p class=lede>Every case: a board described in words. A <span class='badge specified'>specified</span>
case has its parts, nets and outline in its header, ready to grade; a
<span class='badge sketch'>sketch</span> is a proposal still to be pinned down.</p>
<div class=controls><input type=search id=q placeholder='Search titles, ids, tags and checks'
 aria-label='Search the cases'></div>
<div class=pick id=cats>{cats}</div>
<p class=found id=found>{len(cases)} cases</p>
<div class=scroll><table id=cases>
<thead><tr><th>Case</th><th>Status</th><th class=num>Layers</th><th>Checks</th><th>The board</th>{''.join(f'<th class=k>{esc(n)}</th>' for n in results)}</tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<script>
const q = document.getElementById('q'), found = document.getElementById('found');
const rows = [...document.querySelectorAll('#cases tbody tr')];
const chips = [...document.querySelectorAll('#cats .chip')];
function filter() {{
  const words = q.value.toLowerCase().split(/\\s+/).filter(Boolean);
  const cats = chips.filter((c) => c.getAttribute('aria-pressed') === 'true').map((c) => c.dataset.cat);
  let n = 0;
  for (const r of rows) {{
    const show = (!cats.length || cats.includes(r.dataset.cat)) && words.every((w) => r.dataset.hay.includes(w));
    r.hidden = !show; n += show;
  }}
  found.textContent = n + (n === 1 ? ' case' : ' cases');
}}
function press(cat) {{
  for (const c of chips) c.setAttribute('aria-pressed', String(c.dataset.cat === cat));
  filter();
}}
for (const c of chips) c.onclick = () => {{
  c.setAttribute('aria-pressed', String(c.getAttribute('aria-pressed') !== 'true')); filter();
}};
q.oninput = filter;
if (location.hash && chips.some((c) => c.dataset.cat === location.hash.slice(1))) press(location.hash.slice(1));
</script>"""
    page("cases.html", "Cases · pcbhdl-bench", body, "cases.html")


def drawing(case, patterns):
    """A specified case's outline, and the pads of the parts it places, as SVG (y up, in mm)."""
    outline = case["board"]["outline"]
    xs, ys = [p[0] for p in outline], [p[1] for p in outline]
    m = 2
    x0, y0, w, h = min(xs) - m, min(ys) - m, max(xs) - min(xs) + 2 * m, max(ys) - min(ys) + 2 * m
    flip = min(ys) + max(ys)  # y up: mirror about the outline's middle
    pts = " ".join(f"{x:g},{flip - y:g}" for x, y in outline)
    marks = ""
    for part in case.get("part", []):
        if "at" not in part:
            continue
        a = math.radians(part.get("rotation", 0))
        px, py = part["at"]
        for name, x, y, pw, ph, *drill in patterns[part["pattern"]]["pads"]:
            cx = px + x * math.cos(a) - y * math.sin(a)
            cy = flip - (py + x * math.sin(a) + y * math.cos(a))
            if drill and pw == ph:
                marks += (f"<circle class=pad cx='{cx:.3f}' cy='{cy:.3f}' r='{pw / 2:g}'/>"
                          f"<circle class=hole cx='{cx:.3f}' cy='{cy:.3f}' r='{drill[0] / 2:g}'/>")
            else:
                marks += (f"<rect class=pad x='{-pw / 2:g}' y='{-ph / 2:g}' width='{pw:g}' height='{ph:g}'"
                          f" transform='translate({cx:.3f} {cy:.3f}) rotate({-part.get('rotation', 0):g})'/>")
        pads = patterns[part["pattern"]]["pads"]
        mx, my = sum(q[1] for q in pads) / len(pads), sum(q[2] for q in pads) / len(pads)
        lx = px + mx * math.cos(a) - my * math.sin(a) + 1.4
        ly = flip - (py + mx * math.sin(a) + my * math.cos(a)) + 0.4
        marks += f"<text x='{lx:.3f}' y='{ly:.3f}'>{esc(part['ref'])}</text>"
    scale = min(24, 640 / w)
    return (f"<svg class=outline viewBox='{x0:g} {y0:g} {w:g} {h:g}' width='{w * scale:.0f}'"
            f" height='{h * scale:.0f}' role=img aria-label='The board outline and the parts the case places'>"
            f"<polygon class=edge points='{pts}'/>{marks}</svg>")


def case_page(case, patterns, rules, toolchains, results):
    c = case
    (SITE / "cases" / c["category"]).mkdir(parents=True, exist_ok=True)
    facts = (f"<tr><th>Status</th><td>{badge(c['status'])}</td></tr>"
             f"<tr><th>Copper layers</th><td>{c['layers']}</td></tr>"
             f"<tr><th>Rule set</th><td><code>{esc(c['rules'])}</code>: {esc(rules[c['rules']]['about'])}</td></tr>"
             f"<tr><th>Tags</th><td>{esc(', '.join(c['tags']))}</td></tr>")
    checks = "".join(f"<tr><td class=name><code>{k}</code></td><td>{esc(CHECKS[k])}.</td></tr>"
                     for k in c["checks"])
    body = (f"<h1>{esc(c['title'])}</h1>\n<p class=lede><a href='../../cases.html#{c['category']}'>"
            f"{c['category']}</a> / {c['id'].split('/')[1]}</p>\n"
            f"<div class=description>{markdown.render(c['body'])}</div>\n")
    if c["status"] == "specified":
        body += f"<h2>The board</h2>\n{drawing(c, patterns)}\n"
        parts = "".join(
            f"<tr><td>{esc(p['ref'])}</td><td><code>{esc(p['pattern'])}</code></td>"
            f"<td>{esc(p.get('value', ''))}</td>"
            f"<td>{'({:g}, {:g}), {:g}°'.format(*p['at'], p.get('rotation', 0)) if 'at' in p else 'free'}</td></tr>"
            for p in c["part"])
        nets = "".join(f"<tr><td>{esc(n['name'])}</td><td>{esc(', '.join(n['pins']))}</td></tr>"
                       for n in c["net"])
        body += ("<h2>Parts</h2>\n<table><thead><tr><th>Part</th><th>Land pattern</th><th>Value</th>"
                 f"<th>Placed</th></tr></thead><tbody>{parts}</tbody></table>\n"
                 "<h2>Nets</h2>\n<table><thead><tr><th>Net</th><th>Pins</th></tr></thead>"
                 f"<tbody>{nets}</tbody></table>\n")
    else:
        body += ("<p class='prose muted'>A sketch: its parts, nets and numbers are not yet in its header, "
                 "so it cannot be graded. Pin it down, or argue with it, in "
                 f"<a href='{REPO}/blob/main/cases/{c['id']}.md'>its file</a>.</p>\n")
    body += (f"<h2>What is checked</h2>\n<table class=prose><tbody>{checks}</tbody></table>\n"
             f"<h2>The case</h2>\n<table class=facts><tbody>{facts}</tbody></table>\n<h2>Results</h2>\n")
    got = [(t, results[t["name"]][c["id"]]) for t in toolchains if c["id"] in results.get(t["name"], {})]
    if not got:
        body += "<p class=muted>No toolchain has laid this board out yet.</p>"
    for tool, r in got:
        name = tool["name"]
        body += (f"<section class=entry><h3>{esc(name)} <span class='badge {esc(r['outcome'])}'>{esc(r['outcome'])}"
                 f"</span></h3>\n")
        if r.get("refused"):
            body += f"<p><b>It refused</b>, in its own words: {esc(r.get('why', ''))}</p>\n"
            if r.get("control"):
                ctl = r["control"]
                body += (f"<p>Its control, <a href='../../cases/{ctl['case']}.html'>{ctl['case']}</a>, the board beside "
                         f"this one that can be made, is <b>{esc(ctl['outcome'])}</b>: "
                         + ("so the refusal counts." if ctl["outcome"] == "pass" else
                            "so the refusal shows nothing, and is not a pass.") + "</p>\n")
        elif r.get("why"):
            body += f"<p>{esc(r['why'])}</p>\n"
        facts = []
        if "seconds" in r:
            facts.append(f"<tr><th>Time</th><td>{r['seconds']:g} s</td></tr>")
        if r.get("metrics"):
            mm = r["metrics"]
            facts.append(f"<tr><th>Track</th><td>{mm['track_mm']:g} mm on {mm['layers']} layer{'s' if mm['layers'] != 1 else ''}</td></tr>"
                         f"<tr><th>Vias</th><td>{mm['vias']}</td></tr>")
            facts += [f"<tr><th>{esc(k.split(' (')[1][:-1])}</th><td>{v:g} "
                      f"{k.split('_')[1].split(' ')[0].replace('mm2', 'mm²').replace('n', 'vias')}</td></tr>"
                      for k, v in mm.items() if " (" in k]
        for k, v in (r.get("checks") or {}).items():
            facts.append(f"<tr><th><code>{k}</code></th><td>{'holds' if v['ok'] else esc('; '.join(v['notes']))}</td></tr>")
        body += f"<table class=facts><tbody>{''.join(facts)}</tbody></table>\n"
        made = ROOT / "results" / name / c["id"] / "board.kicad_pcb"
        if made.exists():
            if r.get("refused"):
                ab = r.get("as_built")
                body += ("<p class=muted>What it had made when it refused"
                         + (f", which the harness would grade <b>{ab['outcome']}</b>"
                            f"{': ' + esc(ab['why']) if ab['why'] else ''}" if ab else ":") + "</p>\n")
            body += board_svg(c, made) + "\n"
            shutil.copy(made, SITE / "cases" / f"{c['id']}.{name}.kicad_pcb")
            body += f"<p><a href='{c['id'].split('/')[1]}.{name}.kicad_pcb' download>The board as a KiCad file</a></p>\n"
        source = (ROOT / tool["source"].format(id=c["id"], id_snake=c["id"].replace("-", "_"))
                  if tool.get("source") else None)
        if source and source.exists():
            body += (f"<details open><summary>{esc(str(source.relative_to(ROOT)))}</summary>"
                     f"<pre class=code>{esc(source.read_text())}</pre></details>\n")
        body += "</section>\n"
    page(f"cases/{c['id']}.html", f"{c['title']} · pcbhdl-bench", body)


def link(name, url):
    return f"<a href='{esc(url, quote=True)}'>{esc(name)}</a>" if url else esc(name)


def toolchains_page(data):
    rows = "".join(
        f"<tr><td class=name>{link(t['name'], t['url'])}</td><td>{esc(t['language'])}</td>"
        f"<td>{esc(t['license'] or '–')}</td><td>{esc(t['places'])}</td><td>{esc(t['routes'])}</td>"
        f"<td>{esc(t['writes'])}</td><td>{esc(t['note'])}</td>"
        f"<td>{'yes' if t['command'] else '<span class=muted>none yet</span>'}</td></tr>"
        for t in data["toolchains"])
    engines = "".join(
        f"<tr><td class=name>{link(e['name'], e['url'])}</td><td>{esc(e['license'] or '–')}</td>"
        f"<td>{esc(e['does'])}</td><td>{esc(e['note'])}</td></tr>" for e in data["engines"])
    body = f"""<h1>Toolchains</h1>
<p class=lede>What might be entered. A toolchain is whatever turns a design in text into a board:
a language, and something that places and routes. Where a language stops at the netlist, it is
entered with an engine that carries on, and the pair is named for both.</p>
<h2>Languages</h2>
<p class='prose muted'>"Places" and "routes" say what each does with no person at the mouse, as
its own documentation had it in November 2026.</p>
<div class=scroll><table class=prose><thead><tr><th>Toolchain</th><th>Language</th><th>License</th>
<th>Places</th><th>Routes</th><th>Writes</th><th></th><th>Runner</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<h2>Engines to pair them with</h2>
<div class=scroll><table class=prose><thead><tr><th>Engine</th><th>License</th><th>Does</th><th></th></tr></thead>
<tbody>{engines}</tbody></table></div>"""
    page("toolchains.html", "Toolchains · pcbhdl-bench", body, "toolchains.html")


def prior_page(data):
    rows = "".join(
        f"<tr><td class=name>{link(b['name'], b['url'])}<small class=muted><br>{esc(b['where'])}</small></td>"
        f"<td>{esc(b['given'])}</td><td>{esc(b['asked'])}</td><td>{esc(b['graded'])}</td>"
        f"<td>{esc(b['who'])}</td><td>{esc(b['differs'])}</td></tr>" for b in data["benchmarks"])
    body = f"""<h1>Prior work</h1>
<p class=lede>The benchmarks of PCB design that exist, what each gives and asks, and where this one
stands beside them. Numbers are as their authors report them.</p>
<div class=scroll><table class=prose><thead><tr><th>Benchmark</th><th>Given</th><th>Asked for</th>
<th>Graded by</th><th>Tested, and found</th><th>Beside this bench</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class=prose>Taken together: routing a placed board is well measured (PCBWorld), placing an
unplaced one is measured without design rules (OmniLayout), and the whole step from a design to a
routed board is measured once, for agents, from one language (PCB Gym). None compares the
languages, none separates the difficulties into cases that test one thing, and none has boards
that cannot be made.</p>"""
    page("prior.html", "Prior work · pcbhdl-bench", body, "prior.html")


def main():
    cases = read_cases()
    results = read_results()
    tools = json.loads((ROOT / "toolchains.json").read_text())
    patterns = tomllib.loads((ROOT / "patterns.toml").read_text())
    rules = tomllib.loads((ROOT / "rules.toml").read_text())
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir()
    for f in (ROOT / "harness" / "web").iterdir():
        shutil.copy(f, SITE / f.name)
    entered = [t for t in tools["toolchains"] if t.get("command")]  # a column each; the rest are on their page
    index(cases, entered, results, read_runs())
    cases_page(cases, results)
    for case in cases:
        case_page(case, patterns, rules, tools["toolchains"], results)
    toolchains_page(tools)
    prior_page(json.loads((ROOT / "landscape.json").read_text()))
    public = [{k: v for k, v in c.items() if k != "body"} for c in cases]
    (SITE / "board.json").write_text(json.dumps({"cases": public, "results": results}, ensure_ascii=False))
    print(f"{len(cases)} cases, {sum(c['status'] == 'specified' for c in cases)} specified: {SITE}")


if __name__ == "__main__":
    main()
