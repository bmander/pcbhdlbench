// pcbhdl-bench's runner for tscircuit:  node toolchains/tscircuit/run.mjs <case id> <out dir>
//
// Evaluates cases/<case id>.tsx with tscircuit's own CLI (which places and routes), and writes
// <out dir>/board.kicad_pcb, converted by the same CLI from the circuit JSON it made, and
// <out dir>/result.json.  Where tscircuit itself reports an error in what it made (a net it
// could not route, parts it could not place apart), the runner refuses, in tscircuit's words;
// the board is written all the same, to be looked at.  The parts engine, which asks a supplier's
// API for part numbers, is off: nothing here needs the network.
import { spawnSync } from "node:child_process"
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const bin = join(here, "node_modules", ".bin")
const env = { ...process.env, PATH: `${bin}:${process.env.PATH}` }
const tsci = (...args) => spawnSync(join(bin, "tsci"), args, { cwd: here, env, encoding: "utf8" })

if (process.argv[2] === "--version") {
  const pkg = (name) => JSON.parse(readFileSync(join(here, "node_modules", name, "package.json"))).version
  console.log(`tscircuit ${pkg("tscircuit")} (core ${pkg("@tscircuit/core")})`)
  process.exit(0)
}

const [id, outArg] = process.argv.slice(2)
const out = resolve(outArg)
mkdirSync(out, { recursive: true })
const finish = (result) => {
  writeFileSync(join(out, "result.json"), JSON.stringify(result, null, 1) + "\n")
  process.exit(0)
}

const source = join(here, "cases", `${id}.tsx`)
if (!existsSync(source)) finish({ outcome: "missing" })

// tscircuit keeps the routes it has found in .tscircuit/, and would answer from there: every run
// starts without them, so that it is timed doing the work.
rmSync(join(here, ".tscircuit"), { recursive: true, force: true })
const json = join(out, "board.circuit.json")
const made = tsci("export", source, "-f", "circuit-json", "-o", json, "--disable-parts-engine")
if (made.status !== 0 || !existsSync(json)) {
  const said = (made.stderr || made.stdout || "").trim().split("\n").slice(-6).join("\n")
  finish({ outcome: "refused", why: said || "tscircuit wrote no circuit" })
}
const errors = JSON.parse(readFileSync(json, "utf8")).filter((e) => e.type.endsWith("_error"))
const board = tsci("export", json, "-f", "kicad_pcb", "-o", join(out, "board.kicad_pcb"))
if (errors.length) {
  const said = [...new Set(errors.map((e) => `${e.type}: ${e.message ?? ""}`.trim()))]
  finish({ outcome: "refused", why: said.slice(0, 4).join("; ") + (said.length > 4 ? `; and ${said.length - 4} more` : "") })
}
if (board.status !== 0) finish({ outcome: "refused", why: "tscircuit could not write the board as KiCad" })
finish({ outcome: "built" })
