import { Header, std2 } from "../../lib/bench"

export default () => (
  <board width="20mm" height="10mm" {...std2}>
    <Header name="J1" pinCount={4} />
    <resistor name="R1" resistance="1k" footprint="0603" />
    <trace from=".J1 > .pin1" to=".R1 > .pin1" />
    <trace from=".J1 > .pin5" to=".R1 > .pin2" />
  </board>
)
