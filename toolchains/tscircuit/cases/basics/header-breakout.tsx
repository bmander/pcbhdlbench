import { Header, std2 } from "../../lib/bench"

// The board's centre is tscircuit's origin, and a header's is its middle: the case's pin 1 at
// (3, 2.19) on a 20 × 12 board, with the pins running up, puts J1's middle at (-7, 0).
const Upright = (props: { name: string; pcbX: number }) => (
  <Header {...props} pcbY={0} pcbRotation={90} pinCount={4} />
)

export default () => (
  <board width="20mm" height="12mm" {...std2}>
    <Upright name="J1" pcbX={-7} />
    <Upright name="J2" pcbX={7} />
    {[1, 2, 3, 4].map((n) => (
      <trace key={n} from={`.J1 > .pin${n}`} to={`.J2 > .pin${n}`} />
    ))}
  </board>
)
