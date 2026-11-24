"""pcbhdl-bench's runner for netsmith:  python3 toolchains/netsmith/run.py <case id> <out dir>

Runs `netsmith board fab` on src/<case id>.nsm, the id's hyphens as underscores (and the physical file beside it), which checks
the design, picks its parts, places, routes and runs netsmith's own design rules check, and
writes <out dir>/board.kicad_pcb and <out dir>/result.json. Where netsmith stops (a design it
will not build, a board it cannot place, connections it leaves unrouted, a rule its own check
finds broken) the runner refuses, in netsmith's words; a board it wrote all the same is kept.
`--offline`: no supplier is asked for stock or price, and nothing here needs the network. The
router is given 540 seconds, most of the bench's 600, where its own default is 300.

netsmith is built from source into target/ (see the README); it has no binary for an Intel Mac."""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tomllib

HERE = pathlib.Path(__file__).resolve().parent
NETSMITH = HERE / "target" / "release" / "netsmith"
# the chips of src/bench.nsm are drawn with KiCad's own footprints, read from an installed KiCad
KICAD = pathlib.Path(os.environ.get("KICAD_SHARE", "/Applications/KiCad/KiCad.app/Contents/SharedSupport"))
# a line of what `fab` prints for each part: its designator, and its path in the design
PLACED = re.compile(r"^\s+([A-Z]+\d+) \(`([^`]+)`\) (?:top|bottom), turned")


def refs(log, source):
    """Which of the board's designators is which part of the case: netsmith numbers its parts
    itself (R1, R2, …, in the order of their paths), so each is named by its path in the design,
    in capitals (`.j1` is J1), or as `<name>.refs.toml` beside the source says, a pattern of the
    path to the case's name (`'ch(\\d)\\.rs' = 'RS\\1'`)."""
    rules = source.with_suffix(".refs.toml")
    rules = tomllib.loads(rules.read_text()) if rules.exists() else {}
    out = {}
    for line in log.splitlines():
        m = PLACED.match(line)
        if m:
            ref, path = m.groups()
            for pattern, name in rules.items():
                if re.fullmatch(pattern, path):
                    out[ref] = re.sub(pattern, name, path)
                    break
            else:
                out[ref] = re.sub(r"[^A-Za-z0-9]", "", path).upper()
    return out


def main():
    if sys.argv[1] == "--version":
        rev = subprocess.run(["git", "-C", str(HERE / "upstream"), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        print(subprocess.run([NETSMITH, "--version"], capture_output=True, text=True).stdout.strip(), f"({rev})")
        return
    case, out = sys.argv[1], pathlib.Path(sys.argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)

    def finish(result):
        (out / "result.json").write_text(json.dumps(result, indent=1) + "\n")
        sys.exit(0)

    source = HERE / "src" / f"{case.replace('-', '_')}.nsm"  # a file under src/ is a module: no hyphens
    if not source.exists():
        finish({"outcome": "missing"})
    # the pick lock netsmith writes beside a source would hold the next run to this one's parts
    source.with_suffix(".lock.toml").unlink(missing_ok=True)
    fab = out / "fab"
    env = {**os.environ, "NETSMITH_KICAD_FOOTPRINTS": str(KICAD / "footprints"),
           "NETSMITH_KICAD_SYMBOLS": str(KICAD / "symbols")}
    done = subprocess.run([NETSMITH, "board", "fab", str(source), "--offline", "--out", str(fab), "--route-timeout", "540"],
                          cwd=HERE, capture_output=True, text=True, env=env)
    # what netsmith printed, with paths from the repository's root, not the machine's
    root = str(HERE.parent.parent) + "/"
    done.stdout, done.stderr = done.stdout.replace(root, ""), done.stderr.replace(root, "")
    (out / "netsmith.log").write_text(done.stdout + done.stderr)
    source.with_suffix(".lock.toml").unlink(missing_ok=True)
    boards = sorted(fab.glob("*/*.kicad_pcb"))
    if boards:
        shutil.copy(boards[0], out / "board.kicad_pcb")
    shutil.rmtree(fab, ignore_errors=True)  # the Gerbers, the libraries and the 3D scene are not kept
    if done.returncode != 0 or not boards:
        said = [l.strip() for l in (done.stderr + done.stdout).splitlines()
                if re.match(r"\s*(error|INCOMPLETE|refused)", l) or "connections left" in l or "not routed" in l]
        said = said or (done.stderr + done.stdout).strip().splitlines()[-3:]
        finish({"outcome": "refused", "why": "; ".join(dict.fromkeys(said))[:900],
                "refs": refs(done.stdout + done.stderr, source)})
    finish({"outcome": "built", "refs": refs(done.stdout + done.stderr, source)})


main()
