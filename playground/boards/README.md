# Boards of open hardware, for the playground

Each `.json` here is a real board with its routing taken away: its outline, its pads and the nets
they are on, made by `import.py` from the board's own file. The playground's routers start from
there. Each is its maker's design and under its maker's licence, which the file names and the
playground shows beside the board; the derived files here are under the same licences.

| Board | Maker | Licence | From |
| --- | --- | --- | --- |
| Arduino Uno R3 | Arduino | CC BY-SA 2.5 | [the reference design](https://content.arduino.cc/assets/UNO-TH_Rev3e-reference.zip), an Eagle board, through `kicad-cli pcb import` |
| Corne keyboard (crkbd) | foostan | CC BY 4.0 | [corne-cherry.kicad_pcb](https://github.com/foostan/crkbd/blob/1747b2623b/pcbs/corne-cherry/hotswap/corne-cherry.kicad_pcb) |
| Castor & Pollux mainboard | Winterbloom / Alethea Katherine Flowers | CERN-OHL-P v2 | [mainboard.kicad_pcb](https://github.com/wntrblm/Castor_and_Pollux/blob/652b28c950/hardware/mainboard/mainboard.kicad_pcb) |

Castor & Pollux is (c) 2020 by Winterbloom / Alethea Katherine Flowers.

What is changed from each original: the tracks, vias, pours, silkscreen and parts' bodies are left
out; a pad is kept as a plain rectangle or circle of its size; a net of one pad is no net; the
board is moved to the origin. The Castor & Pollux board has four layers and the playground two.
"Arduino" is a trademark of Arduino; the board is named for what it is.

To add one: `python3 playground/boards/import.py board.kicad_pcb playground/boards/name.json --title … --maker …
--license … --license-url … --source … --pour GND`, and its licence must allow it.
