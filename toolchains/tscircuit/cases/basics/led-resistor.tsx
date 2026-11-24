import { Header, led0603, std2 } from "../../lib/bench"

export default () => (
  <board width="20mm" height="10mm" {...std2}>
    <Header name="J1" pinCount={2} />
    <resistor name="R1" resistance="330" footprint="0603" />
    <led name="D1" footprint={led0603} />
    <trace from=".J1 > .pin1" to=".R1 > .pin1" />
    <trace from=".R1 > .pin2" to=".D1 > .anode" />
    <trace from=".D1 > .cathode" to=".J1 > .pin2" />
  </board>
)
