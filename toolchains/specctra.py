"""A board to and from Specctra's formats, with KiCad's own code: run with KiCad's Python.

    <kicad python> toolchains/specctra.py export board.kicad_pcb board.dsn
    <kicad python> toolchains/specctra.py import board.kicad_pcb board.ses routed.kicad_pcb

`import` takes the tracks and vias a router wrote as a session, fills the board's zones, and
saves the result. A router that speaks only Specctra (Freerouting, and its ports) is run between
the two. KiCad's Python is the one inside the application: on a Mac,
/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3."""
import sys

import pcbnew


def main():
    if sys.argv[1] == "export":
        board = pcbnew.LoadBoard(sys.argv[2])
        if not pcbnew.ExportSpecctraDSN(board, sys.argv[3]):
            raise SystemExit("KiCad could not write the board as a Specctra design")
    elif sys.argv[1] == "import":
        board = pcbnew.LoadBoard(sys.argv[2])
        if not pcbnew.ImportSpecctraSES(board, sys.argv[3]):
            raise SystemExit("KiCad could not read the router's session")
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(sys.argv[4], board)
    elif sys.argv[1] == "fill":  # for a router that writes a KiCad board itself: fill its zones
        board = pcbnew.LoadBoard(sys.argv[2])
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(sys.argv[3], board)


main()
