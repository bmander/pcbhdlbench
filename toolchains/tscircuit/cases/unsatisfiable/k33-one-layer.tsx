import { sot23, std2 } from "../../lib/bench"

const three = [1, 2, 3]

export default () => (
  <board width="30mm" height="30mm" layers={1} {...std2}>
    {three.map((i) => (
      <chip key={`H${i}`} name={`H${i}`} footprint={sot23} />
    ))}
    {three.map((j) => (
      <chip key={`U${j}`} name={`U${j}`} footprint={sot23} />
    ))}
    {three.flatMap((i) =>
      three.map((j) => <trace key={`${i}${j}`} from={`.H${i} > .pin${j}`} to={`.U${j} > .pin${i}`} />),
    )}
  </board>
)
