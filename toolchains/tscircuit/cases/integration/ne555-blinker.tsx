import { c0603, Header, led0603, soic8, std2 } from "../../lib/bench"

export default () => (
  <board width="20mm" height="15mm" {...std2}>
    <chip
      name="U1"
      footprint={soic8}
      pinLabels={{
        pin1: "GND", pin2: "TRIG", pin3: "OUT", pin4: "RESET",
        pin5: "CONT", pin6: "THRES", pin7: "DISCH", pin8: "VCC",
      }}
      connections={{
        GND: "net.GND", VCC: "net.VCC", RESET: "net.VCC",
        TRIG: "net.TRIG", THRES: "net.TRIG", DISCH: "net.DISCH", OUT: "net.OUT",
      }}
    />
    <resistor name="R1" resistance="1k" footprint="0603" connections={{ pin1: "net.VCC", pin2: "net.DISCH" }} />
    <resistor name="R2" resistance="470k" footprint="0603" connections={{ pin1: "net.DISCH", pin2: "net.TRIG" }} />
    <capacitor name="C1" capacitance="1uF" footprint={c0603} connections={{ pin1: "net.TRIG", pin2: "net.GND" }} />
    <capacitor name="C2" capacitance="100nF" footprint={c0603} connections={{ pin1: "net.VCC", pin2: "net.GND" }} />
    <resistor name="R3" resistance="330" footprint="0603" connections={{ pin1: "net.OUT", pin2: "net.LED_A" }} />
    <led name="D1" footprint={led0603} connections={{ anode: "net.LED_A", cathode: "net.GND" }} />
    <Header name="J1" pinCount={2} connections={{ pin1: "net.VCC", pin2: "net.GND" }} />
  </board>
)
