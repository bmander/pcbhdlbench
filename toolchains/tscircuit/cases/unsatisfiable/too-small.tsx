import { Header, std2 } from "../../lib/bench"

export default () => (
  <board width="10mm" height="10mm" {...std2}>
    {[1, 2, 3].map((n) => (
      <Header
        key={n}
        name={`J${n}`}
        pinCount={4}
        connections={{ pin1: "net.N1", pin2: "net.N2", pin3: "net.N3", pin4: "net.N4" }}
      />
    ))}
  </board>
)
