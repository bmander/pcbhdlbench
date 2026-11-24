"""pcbhdl-bench's runner for KiCadRoutingTools, a router:
    python3 toolchains/krt/run.py <dir of the placed board> <out dir>

Its `autoroute.py` plans and routes a KiCad board as it is, to the board's own rules
(`--board-rules`) and with the parts left where they are (`--keep-placement`). Where it says it
has left nets open, the runner refuses in its words; the board is kept all the same, its planes
filled by KiCad.

KiCadRoutingTools is cloned into upstream/, with its dependencies in venv/ and its Rust module
fetched by its own build_router.py (see the README)."""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
KICAD_PYTHON = os.environ.get(
    "KICAD_PYTHON", "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3")
LIMIT = int(os.environ.get("ROUTE_SECONDS", "540"))


def main():
    if sys.argv[1] == "--version":
        print("KiCadRoutingTools", (HERE / "upstream" / "VERSION").read_text().strip())
        return
    placed, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)

    def finish(result):
        (out / "result.json").write_text(json.dumps(result, indent=1) + "\n")
        sys.exit(0)

    work = out / "work"
    shutil.copytree(placed, work, dirs_exist_ok=True)
    try:
        done = subprocess.run([str(HERE / "venv" / "bin" / "python"), "py_router/autoroute.py", str(work / "board.kicad_pcb"),
                               str(work / "routed.kicad_pcb"), "--board-rules", "--keep-placement"],
                              cwd=HERE / "upstream", capture_output=True, text=True, timeout=LIMIT)
        said = done.stdout + done.stderr
    except subprocess.TimeoutExpired as e:
        said = (e.stdout or b"").decode(errors="replace") + f"\nstopped after {LIMIT} s"
    (out / "krt.log").write_text(said.replace(str(out) + "/", "")[-200000:])
    routed = work / "routed.kicad_pcb"
    if not routed.exists():  # stopped in the middle: the last step it finished is a board too
        steps = sorted((work / "routed.kicad_pcb.autoroute").glob("step*.kicad_pcb"))
        routed = steps[-1] if steps else routed
    if routed.exists():
        shutil.copy(work / "board.kicad_pro", routed.with_suffix(".kicad_pro"))
        subprocess.run([KICAD_PYTHON, str(HERE.parent / "specctra.py"), "fill", str(routed), str(out / "board.kicad_pcb")],
                       capture_output=True, text=True)
    shutil.rmtree(work, ignore_errors=True)
    if not (out / "board.kicad_pcb").exists():
        finish({"outcome": "refused", "why": f"KiCadRoutingTools wrote no board in {LIMIT} s"
                if "stopped after" in said else "KiCadRoutingTools wrote no board: " + said.strip()[-300:]})
    left = re.findall(r"(\S+\.kicad_pcb): (\d+) open, (\d+) DRC", said)
    if "stopped after" in said:
        finish({"outcome": "refused", "why": f"KiCadRoutingTools had not finished in {LIMIT} s"
                + (f"; its last step had {left[-1][1]} nets open" if left else "")})
    if left and int(left[-1][1]) > 0:
        finish({"outcome": "refused", "why": f"KiCadRoutingTools left {left[-1][1]} nets open, and says so"
                + (f", with {left[-1][2]} of its own DRC findings" if int(left[-1][2]) else "")})
    finish({"outcome": "built"})


main()
