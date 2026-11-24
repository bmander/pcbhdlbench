import { Header, std2 } from "../../lib/bench"

export default () => (
  <board width="15mm" height="10mm" {...std2}>
    <Header name="J1" pinCount={3} connections={{ pin1: "net.VIN", pin2: "net.VOUT", pin3: "net.GND" }} />
    <resistor name="R1" resistance="10k" footprint="0603" connections={{ pin1: "net.VIN", pin2: "net.VOUT" }} />
    <resistor name="R2" resistance="10k" footprint="0603" connections={{ pin1: "net.VOUT", pin2: "net.GND" }} />
  </board>
)
