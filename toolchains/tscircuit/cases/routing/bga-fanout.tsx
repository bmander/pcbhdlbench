import { Header, from, pattern } from "../../lib/bench"

// The bench's four-layer rule set.
const std4 = {
  minTraceWidth: "0.127mm",
  minTraceToPadEdgeClearance: "0.127mm",
  minPadEdgeToPadEdgeClearance: "0.127mm",
  minViaEdgeToPadEdgeClearance: "0.127mm",
  minBoardEdgeClearance: "0.3mm",
  minViaHoleDiameter: "0.3mm",
  minViaPadDiameter: "0.5mm",
} as const

const ROWS = "ABCDEFGHJKLMNPRT"
const cells = Array.from({ length: 256 }, (_, i) => ({ r: Math.floor(i / 16), c: i % 16 }))
const ball = ({ r, c }: { r: number; c: number }) => `${ROWS[r]}${c + 1}`
const ring = ({ r, c }: { r: number; c: number }) => Math.min(r, c, 15 - r, 15 - c)

// The side a ball of the outer two rings leaves by: each side takes a ring's row less its last
// corner, going round clockwise from the top left.
const side = (b: { r: number; c: number }) => {
  const lo = ring(b)
  const hi = 15 - lo
  if (b.r === lo && b.c < hi) return "N"
  if (b.c === hi && b.r < hi) return "E"
  if (b.r === hi && b.c > lo) return "S"
  return "W"
}
// Each side's header, and the order of its balls along it from pin 1.
const sides = {
  N: { header: "J1", along: (b: { r: number; c: number }) => b.c },
  E: { header: "J2", along: (b: { r: number; c: number }) => b.r },
  S: { header: "J3", along: (b: { r: number; c: number }) => -b.c },
  W: { header: "J4", along: (b: { r: number; c: number }) => -b.r },
}
const signals = Object.entries(sides).flatMap(([s, { header, along }]) =>
  cells
    .filter((b) => ring(b) < 2 && side(b) === s)
    .sort((a, b) => along(a) - along(b) || ring(a) - ring(b))
    .map((b, k) => ({ from: `.U1 > .${ball(b)}`, to: `.${header} > .pin${k + 1}` })),
)
// The inner twelve by twelve: a chessboard of ground and supply.
const power = Object.fromEntries(
  cells.filter((b) => ring(b) >= 2).map((b) => [ball(b), (b.r + b.c) % 2 === 0 ? "net.GND" : "net.VCC"]),
)

const at = from(60, 60)
const header = pattern("HDR_2x14_2.54")

export default () => (
  <board width="60mm" height="60mm" layers={4} routeRemaining {...std4}>
    <chip name="U1" footprint={pattern("BGA-256")} {...at(30, 30)} connections={power} />
    {/* Each header's pin 1 is its pattern's origin. */}
    <chip name="J1" footprint={header} {...at(13.49, 52)} pcbRotation={90} />
    <chip name="J2" footprint={header} {...at(52, 46.51)} pcbRotation={0} />
    <chip name="J3" footprint={header} {...at(46.51, 8)} pcbRotation={270} />
    <chip name="J4" footprint={header} {...at(8, 13.49)} pcbRotation={180} />
    <Header name="J5" pinCount={2} {...at(5.27, 4)} connections={{ pin1: "net.VCC", pin2: "net.GND" }} />
    {signals.map((s) => (
      <trace key={s.from} {...s} />
    ))}
    {/* The second layer is the ground plane, the third the supply's. */}
    <copperpour connectsTo="net.GND" layer="inner1" boardEdgeMargin="0.3mm" />
    <copperpour connectsTo="net.VCC" layer="inner2" boardEdgeMargin="0.3mm" />
  </board>
)
