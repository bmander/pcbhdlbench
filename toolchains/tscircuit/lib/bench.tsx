// What the implementations share: the bench's std-2 rule set as tscircuit's board props, a pin
// header with the pads the bench's land pattern has (1.7 mm round a 1.0 mm hole), and the
// footprint strings for its SOIC-8 (1.95 × 0.6 mm pads, 4.95 mm between the two rows' centres)
// and its SOT-23 (1.475 × 0.6 mm pads, 1.875 mm between the two columns' centres).
export const std2 = {
  minTraceWidth: "0.15mm",
  minTraceToPadEdgeClearance: "0.15mm",
  minPadEdgeToPadEdgeClearance: "0.15mm",
  minViaEdgeToPadEdgeClearance: "0.15mm",
  minBoardEdgeClearance: "0.3mm",
  minViaHoleDiameter: "0.3mm",
  minViaPadDiameter: "0.6mm",
} as const

export const Header = (props: { name: string; pinCount: number; [prop: string]: any }) => (
  <pinheader pitch="2.54mm" platedDiameter="1.7mm" holeDiameter="1mm" {...props} />
)

export const soic8 = "soic8_w6.9mm_pl1.95mm_pw0.6mm"
export const sot23 = "sot23_w1.875mm_pl1.475mm"

// A land pattern of the bench's (patterns.toml, exported to patterns.json by
// `python3 -c ...` in the README) as a tscircuit footprint, for parts whose pattern tscircuit's
// own footprint strings do not give.
import patterns from "./patterns.json"

// `as` gives a pad the names a tscircuit part knows its pins by (an LED's anode is its pin 1).
export const pattern = (name: keyof typeof patterns, as: Record<string, string[]> = {}) => (
  <footprint>
    {(patterns[name].pads as (string | number)[][]).map(([pad, x, y, w, h, drill], i) => {
      const hints = as[pad] ?? [`${pad}`]
      const pin = hints[0]
      return drill ? (
        <platedhole key={i} portHints={hints} pcbX={x} pcbY={y} shape="circle" holeDiameter={drill} outerDiameter={w} />
      ) : (
        <smtpad key={i} portHints={hints} pcbX={x} pcbY={y} shape="rect" width={w} height={h} />
      )
    })}
    {/* the pattern's courtyard, so that the placer keeps other parts off the body, not just the pads */}
    {(([x0, y0, x1, y1]) => (
      <courtyardrect pcbX={(x0 + x1) / 2} pcbY={(y0 + y1) / 2} width={x1 - x0} height={y1 - y0} />
    ))(patterns[name].courtyard)}
  </footprint>
)

// tscircuit's "0603" is one pattern for every chip part; the bench's capacitor and LED have
// KiCad's, whose pads differ from a resistor's.
export const c0603 = pattern("C_0603")
export const led0603 = pattern("LED_0603", { A: ["1", "anode"], K: ["2", "cathode"] })

// The board's centre is tscircuit's origin; the cases put a corner there.
export const from = (width: number, height: number) => (x: number, y: number) => ({
  pcbX: x - width / 2,
  pcbY: y - height / 2,
})
