import { Header, std2 } from "../../lib/bench"

// Each header's pins 1 to 3 go to the other three headers, in their order.
const others = (n: number) => [1, 2, 3, 4].filter((m) => m !== n)
const net = (a: number, b: number) => `net.N${Math.min(a, b)}${Math.max(a, b)}`

export default () => (
  <board width="30mm" height="30mm" layers={1} {...std2}>
    {[1, 2, 3, 4].map((n) => (
      <Header
        key={n}
        name={`J${n}`}
        pinCount={4}
        connections={Object.fromEntries(others(n).map((m, i) => [`pin${i + 1}`, net(n, m)]))}
      />
    ))}
  </board>
)
