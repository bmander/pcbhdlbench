"""What the runners of the routers that speak Specctra share: the placed board out as a design by
KiCad's exporter, the router run on it, and its session back into the board by KiCad's importer,
which also fills the planes (toolchains/specctra.py, run with KiCad's Python)."""
import json
import math
import os
import pathlib
import re
import shutil
import subprocess
import sys

KICAD_PYTHON = os.environ.get(
    "KICAD_PYTHON", "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3")
SPECCTRA = pathlib.Path(__file__).resolve().parent / "specctra.py"
LIMIT = int(os.environ.get("ROUTE_SECONDS", "540"))  # what a router has; the bench gives a case 600


def inset(points, d):
    """A simple polygon moved in by `d` on every side (its corners mitred)."""
    n = len(points)
    area = sum(points[i][0] * points[(i + 1) % n][1] - points[(i + 1) % n][0] * points[i][1] for i in range(n))
    sign = 1 if area > 0 else -1  # counter-clockwise: the inside is to the left
    out = []
    for i in range(n):
        (ax, ay), (bx, by), (cx, cy) = points[i - 1], points[i], points[(i + 1) % n]
        u, v = (bx - ax, by - ay), (cx - bx, cy - by)
        lu, lv = math.hypot(*u), math.hypot(*v)
        n1, n2 = (-u[1] / lu * sign, u[0] / lu * sign), (-v[1] / lv * sign, v[0] / lv * sign)
        k = 1 + n1[0] * n2[0] + n1[1] * n2[1]
        out.append((bx + d * (n1[0] + n2[0]) / k, by + d * (n1[1] + n2[1]) / k))
    return out


def keep_from_edge(dsn, project):
    """Specctra has no rule for copper's distance from the board's edge, and KiCad's exporter gives
    the router the edge itself: a router keeps its ordinary clearance from it. The bench's rule is
    wider, so the boundary the router is given is drawn in by the difference."""
    rules = json.loads(project.read_text())["board"]["design_settings"]["rules"]
    extra = rules["min_copper_edge_clearance"] - rules["min_clearance"]
    text = dsn.read_text()
    m = re.search(r"\(boundary\s*\(path pcb 0((?:\s+-?[\d.]+)+)\s*\)", text)
    if extra <= 0 or not m:
        return
    unit = {"um": 1000, "mm": 1, "mil": 39.37, "inch": 0.03937}[re.search(r"\(unit (\w+)\)", text).group(1)]
    v = [float(x) for x in m.group(1).split()]
    points = list(zip(v[::2], v[1::2]))
    if points[0] == points[-1]:
        points = points[:-1]
    moved = inset(points, (extra + 0.01) * unit)
    moved.append(moved[0])
    path = "  ".join(f"{x:.1f} {y:.1f}" for x, y in moved)
    dsn.write_text(text[:m.start()] + f"(boundary\n      (path pcb 0  {path})" + text[m.end():])


def route(name, command, placed, out, limit=LIMIT, edge_by_boundary=True):
    """Routes the board in `placed` into `out`. `command(dsn, ses, rules)` is the router's command
    line; `rules` is the board's least sizes, in mm, as its project file has them. A router with
    no setting for copper's distance from the edge is given a boundary drawn in (`edge_by_boundary`).
    A router does not say when it leaves a connection: the board is graded as it stands."""
    placed, out = pathlib.Path(placed).resolve(), pathlib.Path(out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    def finish(result):
        (out / "result.json").write_text(json.dumps(result, indent=1) + "\n")
        sys.exit(0)

    work = out / "work"
    shutil.copytree(placed, work, dirs_exist_ok=True)
    made = subprocess.run([KICAD_PYTHON, str(SPECCTRA), "export", str(work / "board.kicad_pcb"), str(work / "board.dsn")],
                          capture_output=True, text=True)
    if not (work / "board.dsn").exists():
        finish({"outcome": "refused", "why": "KiCad wrote no Specctra design: " + made.stderr.strip()[-300:]})
    if edge_by_boundary:
        keep_from_edge(work / "board.dsn", work / "board.kicad_pro")
    rules = json.loads((work / "board.kicad_pro").read_text())["board"]["design_settings"]["rules"]
    try:
        done = subprocess.run(command(str(work / "board.dsn"), str(work / "board.ses"), rules), cwd=work,
                              capture_output=True, text=True, timeout=limit)
        said = done.stdout + done.stderr
    except subprocess.TimeoutExpired as e:
        said = (e.stdout or b"").decode(errors="replace") + f"\nstopped after {limit} s"
    (out / f"{name.lower()}.log").write_text(said.replace(str(out) + "/", "")[-200000:])
    if not (work / "board.ses").exists():
        shutil.rmtree(work, ignore_errors=True)
        finish({"outcome": "refused", "why": f"{name} wrote no session in {limit} s"
                if "stopped after" in said else f"{name} wrote no session: " + said.strip()[-300:]})
    subprocess.run([KICAD_PYTHON, str(SPECCTRA), "import", str(work / "board.kicad_pcb"), str(work / "board.ses"),
                    str(out / "board.kicad_pcb")], capture_output=True, text=True)
    shutil.rmtree(work, ignore_errors=True)
    if not (out / "board.kicad_pcb").exists():
        finish({"outcome": "refused", "why": f"KiCad could not read {name}'s session"})
    finish({"outcome": "built"})
