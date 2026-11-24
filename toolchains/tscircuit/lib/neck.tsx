import { Header, from, std2 } from "./bench"

// routing/channel and unsatisfiable/channel-overfull: two halves joined by a neck, a header of
// `pins` on each, pin for pin.  `lo` and `hi` are the neck's edges.
export const Neck = ({ pins, height, lo, hi }: { pins: number; height: number; lo: number; hi: number }) => {
  const at = from(30, height)
  const corners = [
    [0, 0], [13, 0], [13, lo], [17, lo], [17, 0], [30, 0],
    [30, height], [17, height], [17, hi], [13, hi], [13, height], [0, height],
  ]
  const ns = Array.from({ length: pins }, (_, i) => i + 1)
  return (
    <board outline={corners.map(([x, y]) => ({ x: at(x, y).pcbX, y: at(x, y).pcbY }))} {...std2}>
      <Header name="J1" pinCount={pins} {...at(3, height / 2)} pcbRotation={90} />
      <Header name="J2" pinCount={pins} {...at(27, height / 2)} pcbRotation={90} />
      {ns.map((n) => (
        <trace key={n} from={`.J1 > .pin${n}`} to={`.J2 > .pin${n}`} />
      ))}
    </board>
  )
}
