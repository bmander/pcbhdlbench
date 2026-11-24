import { Header, pattern, std2 } from "../../lib/bench"

// Each side's VDD pin, and the ground pin beside it.
const supplies = [
  { vdd: 4, gnd: 5 },
  { vdd: 12, gnd: 13 },
  { vdd: 20, gnd: 21 },
  { vdd: 28, gnd: 29 },
]

export default () => (
  <board width="25mm" height="25mm" {...std2}>
    <chip
      name="U1"
      footprint={pattern("TQFP-32")}
      connections={Object.fromEntries(
        supplies.flatMap(({ vdd, gnd }) => [
          [`pin${vdd}`, "net.VDD"],
          [`pin${gnd}`, "net.GND"],
        ]),
      )}
    />
    {supplies.map(({ vdd }, k) => (
      <capacitor
        key={vdd}
        name={`C${k + 1}`}
        capacitance="100nF"
        footprint={pattern("C_0402")}
        decouplingFor={`.U1 > .pin${vdd}`}
        decouplingTo="net.GND"
        connections={{ pin1: "net.VDD", pin2: "net.GND" }}
      />
    ))}
    <Header name="J1" pinCount={2} connections={{ pin1: "net.VDD", pin2: "net.GND" }} />
  </board>
)
