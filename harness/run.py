"""Runs the bench: each toolchain's runner on each specified case, each board graded.

    python3 harness/run.py [--toolchain NAME] [--case ID]

Writes results/<toolchain>.json, and keeps each board at results/<toolchain>/<case id>/. A case
left out with --case keeps the result it had. Standard library only."""
import argparse
import os
import datetime
import json
import pathlib
import shutil
import subprocess
import time
import tomllib

import grade
import kicad
import place

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIMIT = 600  # seconds a runner has for a case that gives no limit of its own


def read_case(path):
    _, header, _ = path.read_text().split("+++", 2)
    case = tomllib.loads(header)
    case["id"] = f"{path.parent.name}/{path.stem}"
    return case


def named(board, said):
    """The board with its parts called what the case calls them, where the runner's result says
    which is which (`refs`: the board's reference to the case's). A toolchain that numbers its
    own parts cannot be told to call one RS3."""
    refs = said.get("refs") or {}
    for part in board["parts"]:
        part["ref"] = refs.get(part["ref"], part["ref"])
    return board


def run_case(tool, case, patterns, rules):
    out = ROOT / "results" / tool["name"] / case["id"]
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    given = case["id"]
    if tool.get("kind") == "router":  # a router is given the case as a placed board, not its id
        place.write(case, out / "placed")
        given = str(out / "placed")
    start = time.monotonic()
    try:
        limit = case.get("timeout", LIMIT)
        done = subprocess.run([*tool["command"], given, str(out)], cwd=ROOT, capture_output=True, text=True,
                              timeout=limit, env={**os.environ, "ROUTE_SECONDS": str(limit - 60)})  # a router's share of it
    except subprocess.TimeoutExpired:
        return {"outcome": "timeout", "why": f"Ran past {case.get('timeout', LIMIT)} s."}
    seconds = round(time.monotonic() - start, 2)
    said = out / "result.json"
    if done.returncode != 0 or not said.exists():
        return {"outcome": "crashed", "why": (done.stderr or done.stdout).strip()[-400:], "seconds": seconds}
    said = json.loads(said.read_text())
    if said["outcome"] == "missing":
        shutil.rmtree(out)
        return None
    if said["outcome"] == "refused":
        owed = "refuse" in case["checks"]
        result = {"outcome": "pass" if owed else "refused", "why": said.get("why", ""), "seconds": seconds,
                  "refused": True}
        if (out / "board.kicad_pcb").exists() and not owed:
            # what it had made is graded too, for the record: it changes nothing above
            built = grade.grade(case, named(kicad.load(out / "board.kicad_pcb"), said), patterns, rules,
                                tool.get("pads", {}))
            result["as_built"] = {k: built[k] for k in ("outcome", "why", "metrics")}
        return result
    board = named(kicad.load(out / "board.kicad_pcb"), said)
    if tool.get("kind") == "router" and "refuse" in case["checks"]:
        # a router is not asked to refuse: of a board that cannot be made, one it leaves unfinished
        # and otherwise sound is its refusal, and one with a fault is wrong
        asked = ["parts", "connectivity", "rules", "outline"] + (["fixed"] if any("at" in p for p in case["part"]) else [])
        built = grade.grade({**case, "checks": asked}, board, patterns, rules, tool.get("pads", {}))
        if built["outcome"] == "pass":
            raise AssertionError(f"{case['id']} is not unsatisfiable: this board passes")
        if built["outcome"] == "placed":
            left = sum(n.endswith("is open") for n in built["checks"]["connectivity"]["notes"])
            return {"outcome": "refused", "refused": True, "seconds": seconds, "metrics": built["metrics"],
                    "why": f"It left {left} of the {len(case['net'])} nets open, on a board with no other fault."}
        return {**built, "outcome": "wrong", "seconds": seconds,
                "why": "A board was written for a case that has none. " + built["why"]}
    result = grade.grade(case, board, patterns, rules, tool.get("pads", {}))
    result["seconds"] = seconds
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--toolchain")
    ap.add_argument("--case")
    args = ap.parse_args()
    patterns = tomllib.loads((ROOT / "patterns.toml").read_text())
    rules = tomllib.loads((ROOT / "rules.toml").read_text())
    cases = [read_case(p) for p in sorted((ROOT / "cases").glob("*/*.md"))]
    every = cases
    entered = json.loads((ROOT / "toolchains.json").read_text())
    for tool in entered["toolchains"] + [dict(r, kind="router") for r in entered.get("routers", [])]:
        if not tool.get("command") or args.toolchain not in (None, tool["name"]):
            continue
        all_cases = [c for c in every if c["status"] == "specified"
                     and (tool.get("kind") != "router" or place.placeable(c))]
        cases = [c for c in all_cases if args.case in (None, c["id"])]
        path = ROOT / "results" / f"{tool['name']}.json"
        kept = json.loads(path.read_text())["cases"] if path.exists() and args.case else {}
        if not cases:  # nothing to run: the results there are judged again
            kept = json.loads(path.read_text())["cases"] if path.exists() else {}
        version = subprocess.run(tool["version"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        for case in cases:
            result = run_case(tool, case, patterns, rules)
            if result is None:
                kept.pop(case["id"], None)
                continue
            kept[case["id"]] = result
            print(f"{tool['name']:12} {case['id']:34} {result['outcome']:8} {result.get('why', '')[:90]}")
        # a refusal of a case that has no board is a pass only from a toolchain that passes the
        # case's control: the board beside it that can be made
        for case in all_cases:
            got = kept.get(case["id"])
            if got and got.get("refused") and "refuse" in case["checks"]:
                control = kept.get(case["control"], {}).get("outcome")  # a router's is placed for it too
                got["outcome"] = "pass" if control == "pass" else "refused"
                got["control"] = {"case": case["control"], "outcome": control or "missing"}
        path.write_text(json.dumps({"toolchain": tool["name"], "kind": tool.get("kind", "toolchain"), "version": version,
                                    "ran": datetime.date.today().isoformat(),
                                    "cases": dict(sorted(kept.items()))}, indent=1, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
