import { pattern, std2 } from "../../lib/bench"

// Three amps on 1 oz copper want 1.37 mm; every track of the current's way is drawn at 1.4.
const wide = { thickness: "1.4mm" }

const Terminal = (props: { name: string }) => <chip {...props} footprint={pattern("TERM_1x2_5.00")} />

export default () => (
  <board width="40mm" height="20mm" {...std2}>
    <Terminal name="J1" />
    <chip name="F1" footprint={pattern("FUSE_1206")} />
    <chip name="Q1" footprint={pattern("SOT-23")} pinLabels={{ pin1: "G", pin2: "S", pin3: "D" }} />
    <resistor name="R1" resistance="100k" footprint="0603" />
    <Terminal name="J2" />

    <trace from=".J1 > .pin1" to=".F1 > .pin1" {...wide} />
    <trace from=".F1 > .pin2" to=".Q1 > .D" {...wide} />
    <trace from=".Q1 > .S" to=".J2 > .pin1" {...wide} />
    <trace from=".J2 > .pin2" to=".J1 > .pin2" {...wide} />
    {/* The gate and its pull-down carry nothing. */}
    <trace from=".Q1 > .G" to=".R1 > .pin1" />
    <trace from=".R1 > .pin2" to=".J1 > .pin2" />
  </board>
)
