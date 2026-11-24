import { std2 } from "../../lib/bench"

// The board's centre is the origin: the case's (3, 3) is (-4.5, -4.5).
export default () => (
  <board width="15mm" height="15mm" {...std2}>
    <resistor name="R1" resistance="1k" footprint="0603" pcbX={-4.5} pcbY={-4.5} />
    <resistor name="R2" resistance="1k" footprint="0603" pcbX={4.5} pcbY={-4.5} />
    <resistor name="R3" resistance="1k" footprint="0603" pcbX={4.5} pcbY={4.5} />
    <resistor name="R4" resistance="1k" footprint="0603" pcbX={-4.5} pcbY={4.5} />
    <trace from=".R1 > .pin2" to=".R3 > .pin1" />
    <trace from=".R2 > .pin1" to=".R4 > .pin2" />
  </board>
)
