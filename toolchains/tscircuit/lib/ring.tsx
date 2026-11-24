import { Header, led0603, std2 } from "./bench"

// parametric/led-ring-*: `count` LEDs in series round a circle of `radius`, each lying along it
// with its anode leading counter-clockwise, fed from a header at the middle.  `routeRemaining`
// is what tscircuit asks for before it will route more than fifty traces in one go.
export const Ring = ({ count, radius, size }: { count: number; radius: number; size: number }) => {
  const ks = Array.from({ length: count }, (_, i) => i + 1)
  const angle = (k: number) => (360 * (k - 1)) / count
  const rad = (k: number) => (angle(k) * Math.PI) / 180
  return (
    <board width={`${size}mm`} height={`${size}mm`} routeRemaining {...std2}>
      <Header name="J1" pinCount={2} pcbX={0} pcbY={0} />
      {ks.map((k) => (
        // The pattern's anode is on the right: a quarter turn past the radius, it leads.
        <led
          key={k}
          name={`D${k}`}
          footprint={led0603}
          pcbX={radius * Math.cos(rad(k))}
          pcbY={radius * Math.sin(rad(k))}
          pcbRotation={(angle(k) + 90) % 360}
        />
      ))}
      <trace from=".J1 > .pin1" to={`.D${count} > .anode`} />
      <trace from=".J1 > .pin2" to=".D1 > .cathode" />
      {ks.slice(0, -1).map((k) => (
        <trace key={k} from={`.D${k} > .anode`} to={`.D${k + 1} > .cathode`} />
      ))}
    </board>
  )
}
