"""pcbhdl-bench's runner for Freerouting, a router:
    python3 toolchains/freerouting/run.py <dir of the placed board> <out dir>

Freerouting 2.1.0, the jar of its GitHub release (see the README), on Java 21: the releases since
need Java 25, and the self-contained command-line build of 2.5.0 dies in the middle of a board on
an Intel Mac. It is told to send no usage data, and is stopped where it has not finished in its
time."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import dsn_router

JAR = pathlib.Path(__file__).resolve().parent / "freerouting-2.1.0.jar"

if sys.argv[1] == "--version":
    print("Freerouting 2.1.0")
else:
    dsn_router.route("Freerouting", lambda dsn, ses, rules: [
        "java", "-jar", str(JAR), "-de", dsn, "-do", ses, "-mp", "100", "--gui.enabled=false",
        "--usage_and_diagnostic_data.disable_analytics=true", "--api_server.enabled=false"], sys.argv[1], sys.argv[2])
