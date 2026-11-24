"""pcbhdl-bench's runner for fastroute, a router:
    python3 toolchains/fastroute/run.py <dir of the placed board> <out dir>

fastroute 0.1.14, a port of Freerouting to Rust with fixes of its own: the Intel Mac build of its
GitHub release, unpacked into bin/ (see the README). It is given the bench's time less a margin,
and writes the best it has when that is spent."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import dsn_router

BIN = pathlib.Path(__file__).resolve().parent / "bin" / "fastroute-0.1.14-macos-x64" / "fastroute"

if sys.argv[1] == "--version":
    print("fastroute 0.1.14")
else:
    # fastroute necks a track down to get it through, and has settings of its own for the least
    # width it may neck to and for copper's distance from the edge: they are given the board's.
    dsn_router.route("fastroute", lambda dsn, ses, rules: [
        str(BIN), "-de", dsn, "-do", ses, "-mp", "100", f"--max-time={dsn_router.LIMIT - 60}",
        f"--router.min_trace_width_um={rules['min_track_width'] * 1000:g}",
        f"--router.copper_to_edge_clearance_um={rules['min_copper_edge_clearance'] * 1000:g}"],
        sys.argv[1], sys.argv[2], edge_by_boundary=False)
