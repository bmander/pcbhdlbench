import { Header, std2 } from "../../lib/bench"

// The board's centre is the origin and a header's is its middle: J1's pins run from x = 10 to
// 27.78 at y = 3 on a 31 × 31 board, so its middle is at (3.39, -12.5); J2 is the same, turned.
export default () => (
  <board width="31mm" height="31mm" layers={1} {...std2}>
    <Header name="J1" pinCount={8} pcbX={3.39} pcbY={-12.5} />
    <Header name="J2" pinCount={8} pcbX={-12.5} pcbY={3.39} pcbRotation={90} />
    {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
      <trace key={n} from={`.J1 > .pin${n}`} to={`.J2 > .pin${n}`} />
    ))}
  </board>
)
