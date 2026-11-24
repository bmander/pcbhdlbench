import { c0603, Header, std2 } from "../../lib/bench"

export default () => (
  <board width="15mm" height="10mm" {...std2}>
    <Header name="J1" pinCount={3}
      connections={{ pin1: "net.IN", pin2: "net.GND", pin3: "net.OUT" }}
    />
    <resistor
      name="R1"
      resistance="10k"
      footprint="0603"
      connections={{ pin1: "net.IN", pin2: "net.OUT" }}
    />
    <capacitor
      name="C1"
      capacitance="100nF"
      footprint={c0603}
      connections={{ pin1: "net.OUT", pin2: "net.GND" }}
    />
  </board>
)
