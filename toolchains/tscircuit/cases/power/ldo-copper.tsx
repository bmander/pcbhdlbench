import { Header, pattern, std2 } from "../../lib/bench"

const c0805 = pattern("C_0805")

export default () => (
  <board width="30mm" height="25mm" enableViaStitching viaStitchPitch="4mm" {...std2}>
    <chip
      name="U1"
      footprint={pattern("SOT-223")}
      pinLabels={{ pin1: "GND", pin2: "VOUT", pin3: "VIN" }}
      connections={{ GND: "net.GND", VOUT: "net.VOUT", VIN: "net.VIN" }}
    />
    <capacitor name="C1" capacitance="10uF" footprint={c0805} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C2" capacitance="22uF" footprint={c0805} connections={{ pin1: "net.VOUT", pin2: "net.GND" }} />
    <Header name="J1" pinCount={2} connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <Header name="J2" pinCount={2} connections={{ pin1: "net.VOUT", pin2: "net.GND" }} />
    {/* The tab's heat goes into the output net: poured on both layers, and stitched. */}
    <copperpour connectsTo="net.VOUT" layer="top" boardEdgeMargin="0.3mm" />
    <copperpour connectsTo="net.VOUT" layer="bottom" boardEdgeMargin="0.3mm" />
  </board>
)
