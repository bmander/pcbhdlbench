import { c0603, Header, std2 } from "../../lib/bench"

// One channel: a group of three parts, laid out in a row.  Written once.
const Channel = ({ k }: { k: number }) => (
  <group name={`CH${k}`} pcbFlex pcbFlexDirection="row" pcbFlexGap="1mm">
    <resistor name={`RS${k}`} resistance="1k" footprint="0603" connections={{ pin1: `net.IN${k}`, pin2: `net.OUT${k}` }} />
    <capacitor name={`C${k}`} capacitance="100nF" footprint={c0603} connections={{ pin1: `net.OUT${k}`, pin2: "net.GND" }} />
    <resistor name={`RL${k}`} resistance="100k" footprint="0603" connections={{ pin1: `net.OUT${k}`, pin2: "net.GND" }} />
  </group>
)

const ks = [1, 2, 3, 4, 5, 6, 7, 8]
const pins = (net: string) => Object.fromEntries(ks.map((k) => [`pin${k}`, `net.${net}${k}`]))

export default () => (
  <board width="40mm" height="30mm" {...std2}>
    <Header name="J1" pinCount={8} connections={pins("IN")} />
    <Header name="J2" pinCount={8} connections={pins("OUT")} />
    <Header name="J3" pinCount={2} connections={{ pin1: "net.GND", pin2: "net.GND" }} />
    {ks.map((k) => (
      <Channel key={k} k={k} />
    ))}
  </board>
)
