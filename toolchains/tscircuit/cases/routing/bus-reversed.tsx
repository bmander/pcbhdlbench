import { Header, std2 } from "../../lib/bench"

export default () => (
  <board width="20mm" height="24mm" {...std2}>
    <Header name="J1" pinCount={8} pcbX={-7} pcbY={0} pcbRotation={90} />
    <Header name="J2" pinCount={8} pcbX={7} pcbY={0} pcbRotation={270} />
    {[1, 2, 3, 4, 5, 6, 7, 8].map((n) => (
      <trace key={n} from={`.J1 > .pin${n}`} to={`.J2 > .pin${n}`} />
    ))}
  </board>
)
