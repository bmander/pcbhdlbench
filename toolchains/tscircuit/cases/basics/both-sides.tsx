import { Header, std2 } from "../../lib/bench"

export default () => (
  <board width="20mm" height="10mm" {...std2}>
    <Header
      name="J1"
      pinCount={5}
      connections={{ pin1: "net.S1", pin2: "net.S2", pin3: "net.S3", pin4: "net.S4", pin5: "net.VCC" }}
    />
    {[1, 2, 3, 4].map((n) => (
      <resistor
        key={n}
        name={`R${n}`}
        resistance="10k"
        footprint="0603"
        layer="bottom"
        connections={{ pin1: `net.S${n}`, pin2: "net.VCC" }}
      />
    ))}
  </board>
)
