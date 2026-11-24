import { Header, from, std2 } from "../../lib/bench"

// The L's corners, and the middle of each header: J1's pins run from x = 20 to 37.78 at y = 5,
// J2's from y = 10 to 27.78 at x = 5.  tscircuit's origin is the middle of the outline's box.
const at = from(40, 30)
const corners = [[0, 0], [40, 0], [40, 10], [10, 10], [10, 30], [0, 30]]

export default () => (
  <board outline={corners.map(([x, y]) => ({ x: at(x, y).pcbX, y: at(x, y).pcbY }))} {...std2}>
    <Header name="J1" pinCount={8} {...at(28.89, 5)} />
    <Header name="J2" pinCount={8} {...at(5, 18.89)} pcbRotation={90} />
    {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
      <trace key={n} from={`.J1 > .pin${n}`} to={`.J2 > .pin${n}`} />
    ))}
  </board>
)
