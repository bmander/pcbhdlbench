import { c0603, Header, pattern, std2 } from "../../lib/bench"

const c0805 = pattern("C_0805")

export default () => (
  <board width="25mm" height="20mm" {...std2}>
    <chip
      name="U1"
      footprint={pattern("SOT-23-6")}
      pinLabels={{ pin1: "GND", pin2: "SW", pin3: "VIN", pin4: "FB", pin5: "EN", pin6: "BST" }}
      connections={{
        GND: "net.GND", SW: "net.SW", VIN: "net.VIN", FB: "net.FB", EN: "net.VIN", BST: "net.BST",
      }}
    />
    {/* The input capacitor: tscircuit has a word for a capacitor that belongs to a supply pin. Its
        track may be 1 mm long unless told otherwise, which an 0805 beside a SOT-23 cannot meet. */}
    <capacitor
      name="C1"
      capacitance="10uF"
      footprint={c0805}
      decouplingFor=".U1 > .VIN"
      decouplingTo="net.GND"
      maxDecouplingTraceLength="4mm"
      connections={{ pin1: "net.VIN", pin2: "net.GND" }}
    />
    <capacitor name="C2" capacitance="100nF" footprint={c0603} connections={{ pin1: "net.BST", pin2: "net.SW" }} />
    <inductor name="L1" inductance="2.2uH" footprint={pattern("L_4x4")} connections={{ pin1: "net.SW", pin2: "net.VOUT" }} />
    <capacitor name="C3" capacitance="22uF" footprint={c0805} connections={{ pin1: "net.VOUT", pin2: "net.GND" }} />
    <resistor name="R1" resistance="33k" footprint="0603" connections={{ pin1: "net.VOUT", pin2: "net.FB" }} />
    <resistor name="R2" resistance="10k" footprint="0603" connections={{ pin1: "net.FB", pin2: "net.GND" }} />
    <Header name="J1" pinCount={2} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <Header name="J2" pinCount={2} connections={{ pin1: "net.VOUT", pin2: "net.GND" }} />
  </board>
)
