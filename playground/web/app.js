// The autorouting playground: a board of pads and nets, edited here, routed by router.wasm (the
// Rust of playground/router), and drawn as it goes.  The page holds the board; the module holds
// the grid.  After every edit the board is written to the module again and the routing starts over.

const $ = (id) => document.getElementById(id);
const canvas = $('board');
const ctx = canvas.getContext('2d');

// by the strategy's number in the module, which is also what a link to a board keeps
const ABOUT = [
  'Lee, 1961. Each net in turn sends a wave out from its copper, one grid point further each step, until it meets the pad it wants. It finds the shortest way there is, and looks everywhere to find it.',
  'The same search, but the points nearer the pad are tried first, so the wave is a finger and not a pond. What it finds is as short; it looks at far less.',
  'A* until a net is walled in by the nets before it. Then it is routed straight through them, the nets it crossed are taken up, and they are routed again afterwards.',
  'Every net is routed where it likes, through other nets if it likes, at a price. Each round the price of a shared point goes up, and the nets are all routed again, until no point is shared.',
  'Hadlock, 1977. A step toward the pad is free and a step away is a detour; the points with the fewest detours are tried first. With nothing in the way it walks straight there, and it widens its search one detour at a time. What it finds is as short as Lee\'s.',
  'Lee\'s wave from both ends at once: one from the net\'s copper, one from the pad, each a step at a time, until they meet. Two small ponds hold less than one big one, so it looks at about half as much.',
  'A* first. Then, move after move: a net left unrouted is pushed through whatever is in its way, the nets it displaced are laid again round it, and the move is kept if the board is better for it. While the temperature is high a worse board is sometimes kept too, which is how it gets out of a corner; as it cools it settles.',
];

// the board as the page holds it, in mm, y up
let board = {
  width: 30, height: 20, track: 0.15, clearance: 0.15, via: 0.6, pitch: 0.3, edge: 0.3,
  outline: [], pads: [],
};
let net = 0;            // the net of a new pad
let selected = -1;
let tool = 'select';
let running = false;
let loaded = false;
let wasm = null;
let grid = { w: 0, h: 0 };
let stats = new Int32Array(18);
let drag = null;

const hue = (n) => (n * 67 + 200) % 360;
const colour = (n, alpha = 1) => (n < 0 ? `rgba(140,140,146,${alpha})` : `hsla(${hue(n)},72%,58%,${alpha})`);
const netCount = () => board.pads.reduce((m, p) => Math.max(m, p.net + 1), 0);

// ---- the module ----------------------------------------------------------------------------

async function boot() {
  try {
    const { instance } = await WebAssembly.instantiateStreaming(fetch('router.wasm'), {});
    wasm = instance.exports;
  } catch (e) {
    $('stats').textContent = 'The router could not be loaded: ' + e.message;
    return;
  }
  await loadPresets();
  // ?case=routing/bus-8 opens that case of the bench; otherwise the board in the link, or the first example
  const asked = new URLSearchParams(location.search).get('case');
  const found = asked ? presets.findIndex((p) => p.id === asked) : -1;
  if (found >= 0) await pick(found);
  else restore() || await pick(0);
  frame();
}

/** Writes the board to the module and builds its grid; the routing is not started. */
function send() {
  const b = board;
  const v = [b.width, b.height, b.pitch, b.track, b.clearance, b.via, b.edge, b.outline.length];
  for (const [x, y] of b.outline) v.push(x, y);
  v.push(b.pads.length);
  const poured = $('pour').checked ? b.pour ?? [] : [];
  for (const p of b.pads) v.push(p.x, p.y, p.w, p.h, p.side, p.round ? 1 : 0, poured.includes(p.net) ? -1 : p.net);
  const at = wasm.buffer(v.length);
  new Float32Array(wasm.memory.buffer, at, v.length).set(v);
  loaded = wasm.load() === 1;
  running = false;
  started = false;
  if (!loaded) {
    const why = new TextDecoder().decode(new Uint8Array(wasm.memory.buffer, wasm.error(), wasm.error_length()));
    $('stats').textContent = 'This board cannot be routed here: ' + why + '.';
    return;
  }
  grid = { w: wasm.grid_width(), h: wasm.grid_height() };
  hemmed = wasm.hemmed();
  wasm.paint();
  stats = new Int32Array(wasm.memory.buffer, wasm.stats(), 18).slice();   // how many nets there are, before any is routed
  buttons();
}

let started = false;
let hemmed = 0;      // pads with no way out on this grid
function begin() {
  if (!loaded) return;
  wasm.start(+$('strategy').value, +$('order').value, $('diagonal').checked ? 1 : 0,
             $('improve').checked ? 1 : 0, +$('viaweight').value || 0, +$('turnweight').value || 0);
  started = true;
}

const perFrame = () => Math.round(Math.pow(10, ($('speed').value / 100) * 5.3));  // 1 to 200,000

function advance(n) {
  if (!loaded) return;
  if (!started) begin();
  // a frame's worth: the steps asked for, or as many of them as fit in a sixtieth of a second
  // (at the top of the slider, most of a twentieth: a big board is worth a slower picture)
  const until = performance.now() + (+$('speed').value >= 95 ? 45 : 14);
  let over = false;
  for (let left = n; left > 0 && !over; left -= 2000) {
    over = wasm.step(Math.min(left, 2000)) === 1;
    if (performance.now() > until) break;
  }
  if (over) running = false;
  wasm.paint();
  stats = new Int32Array(wasm.memory.buffer, wasm.stats(), 18).slice();
  buttons();
}

// ---- drawing -------------------------------------------------------------------------------

let view = { s: 1, ox: 0, oy: 0 };
const px = (x) => view.ox + x * view.s;
const py = (y) => view.oy - y * view.s;
const mm = (e) => {
  const r = canvas.getBoundingClientRect();
  const k = canvas.width / r.width;
  return { x: ((e.clientX - r.left) * k - view.ox) / view.s, y: (view.oy - (e.clientY - r.top) * k) / view.s };
};

function draw() {
  const css = getComputedStyle(document.body);
  const [fg, bg, line] = ['--fg', '--bg', '--line'].map((v) => css.getPropertyValue(v).trim());
  // the canvas has as many pixels as it is shown at, so that tracks are sharp
  const shown = canvas.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
  if (canvas.width !== Math.round(shown.width * dpr) || canvas.height !== Math.round(shown.height * dpr)) {
    canvas.width = Math.round(shown.width * dpr);
    canvas.height = Math.round(shown.height * dpr);
  }
  const W = canvas.width, H = canvas.height, m = 24 * dpr;
  view.s = Math.min((W - 2 * m) / board.width, (H - 2 * m) / board.height);
  view.ox = (W - board.width * view.s) / 2;
  view.oy = H - (H - board.height * view.s) / 2;
  ctx.clearRect(0, 0, W, H);

  // the board
  const outline = board.outline.length >= 3 ? board.outline : [[0, 0], [board.width, 0], [board.width, board.height], [0, board.height]];
  ctx.beginPath();
  outline.forEach(([x, y], i) => (i ? ctx.lineTo(px(x), py(y)) : ctx.moveTo(px(x), py(y))));
  ctx.closePath();
  ctx.fillStyle = bg;
  ctx.fill();
  ctx.strokeStyle = fg;
  ctx.lineWidth = 1.5;
  ctx.stroke();

  if (loaded) {
    const n = 2 * grid.w * grid.h;
    const nets = new Int16Array(wasm.memory.buffer, wasm.nets(), n);
    const flags = new Uint8Array(wasm.memory.buffer, wasm.flags(), n);
    const links = new Uint8Array(wasm.memory.buffer, wasm.links(), n);
    const show = $('view').value;
    const layers = show === 'top' ? [0] : show === 'bottom' ? [1] : [1, 0];
    const g = board.pitch * view.s;          // a grid step in pixels
    const half = Math.max(g / 2, 0.5);
    const idx = (l, x, y) => (l * grid.h + y) * grid.w + x;
    if (grid.w * grid.h > 45000) {
      paintGrid(nets, flags, layers);
    } else {

    // what is closed to tracks, and the search's wave
    for (const l of layers) {
      for (let y = 0; y < grid.h; y++) {
        for (let x = 0; x < grid.w; x++) {
          const c = idx(l, x, y), f = flags[c];
          let fill = null;
          if (f & 8) fill = l === 0 ? 'rgba(110,150,255,0.40)' : 'rgba(110,150,255,0.22)';
          else if (f & 64) fill = l === 0 ? 'rgba(60,200,170,0.40)' : 'rgba(60,200,170,0.22)';
          else if (f & 4) fill = 'rgba(240,190,40,0.75)';
          else if (nets[c] === -2 && l === layers[layers.length - 1]) fill = 'rgba(140,140,146,0.16)';
          if (fill) {
            ctx.fillStyle = fill;
            ctx.fillRect(px(x * board.pitch) - half, py(y * board.pitch) - half, 2 * half, 2 * half);
          }
        }
      }
    }
    // the tracks, piece by piece as the router laid them: from each point east, north, north-east and north-west
    const w = Math.max(board.track * view.s, 1.5);
    for (const l of layers) {
      const byNet = new Map();
      for (let y = 0; y < grid.h; y++) {
        for (let x = 0; x < grid.w; x++) {
          const c = idx(l, x, y), k = links[c];
          if (!k) continue;
          const id = nets[c] >= 0 ? nets[c] : 0;
          const path = byNet.get(id) ?? byNet.set(id, new Path2D()).get(id);
          const X = px(x * board.pitch), Y = py(y * board.pitch);
          if (k & 1) { path.moveTo(X, Y); path.lineTo(X + g, Y); }
          if (k & 2) { path.moveTo(X, Y); path.lineTo(X, Y - g); }
          if (k & 4) { path.moveTo(X, Y); path.lineTo(X + g, Y - g); }
          if (k & 8) { path.moveTo(X, Y); path.lineTo(X - g, Y - g); }
        }
      }
      ctx.lineCap = 'round';
      for (const [id, path] of byNet) {
        if (l === 0) {
          ctx.strokeStyle = colour(id);
          ctx.lineWidth = w;
          ctx.stroke(path);
        } else {                                  // the bottom layer: hollow
          ctx.strokeStyle = colour(id, 0.9);
          ctx.lineWidth = w + 2;
          ctx.stroke(path);
          ctx.strokeStyle = bg;
          ctx.lineWidth = Math.max(w - 1.5, 0.5);
          ctx.stroke(path);
        }
      }
    }
    }
    // tracks through what another net keeps, and the vias
    if (grid.w * grid.h <= 45000)
    for (let y = 0; y < grid.h; y++) {
      for (let x = 0; x < grid.w; x++) {
        for (const l of layers) {
          const f = flags[idx(l, x, y)];
          if (f & 2) {
            ctx.fillStyle = '#e34948';
            ctx.beginPath();
            ctx.arc(px(x * board.pitch), py(y * board.pitch), Math.max(half * 0.7, 2), 0, 7);
            ctx.fill();
          }
        }
        const c = idx(0, x, y);
        if (flags[c] & 16) {
          const r = Math.max((board.via / 2) * view.s, 2.5);
          ctx.beginPath();
          ctx.arc(px(x * board.pitch), py(y * board.pitch), r, 0, 7);
          ctx.fillStyle = colour(nets[c] >= 0 ? nets[c] : nets[idx(1, x, y)]);
          ctx.fill();
          ctx.beginPath();
          ctx.arc(px(x * board.pitch), py(y * board.pitch), r * 0.45, 0, 7);
          ctx.fillStyle = bg;
          ctx.fill();
        }
      }
    }
  }

  // the pads
  board.pads.forEach((p, i) => {
    const hidden = ($('view').value === 'top' && p.side === 1) || ($('view').value === 'bottom' && p.side === 0);
    const x = px(p.x - p.w / 2), y = py(p.y + p.h / 2), w = p.w * view.s, h = p.h * view.s;
    ctx.globalAlpha = hidden ? 0.25 : 1;
    ctx.beginPath();
    if (p.round) ctx.arc(px(p.x), py(p.y), w / 2, 0, 7); else ctx.rect(x, y, w, h);
    ctx.fillStyle = p.side === 1 ? bg : colour(p.net, 0.92);
    ctx.fill();
    ctx.lineWidth = i === selected ? 3 : p.side === 1 ? 2 : 1;
    ctx.strokeStyle = i === selected ? fg : p.side === 1 ? colour(p.net) : line;
    ctx.stroke();
    if (p.side === 2) {
      ctx.beginPath();
      ctx.arc(px(p.x), py(p.y), Math.min(w, h) * 0.28, 0, 7);
      ctx.fillStyle = bg;
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  });
}

// a net's colour as the four bytes of a pixel, and the same dimmed for the bottom layer
const rgba = new Map();
function pixel(n, dim) {
  const key = n * 2 + (dim ? 1 : 0);
  if (!rgba.has(key)) {
    const h = hue(n) / 60, s = 0.72, l = dim ? 0.36 : 0.58;
    const c = (1 - Math.abs(2 * l - 1)) * s, x = c * (1 - Math.abs((h % 2) - 1)), m = l - c / 2;
    const [r, g, b] = [[c, x, 0], [x, c, 0], [0, c, x], [0, x, c], [x, 0, c], [c, 0, x]][Math.floor(h) % 6];
    rgba.set(key, (255 << 24) | (Math.round((b + m) * 255) << 16) | (Math.round((g + m) * 255) << 8) | Math.round((r + m) * 255));
  }
  return rgba.get(key);
}

let raster = null;
/** A big board: every point a pixel, the tracks, the wave and the vias in one pass, scaled up to the board. */
function paintGrid(nets, flags, layers) {
  const { w, h } = grid;
  if (!raster || raster.canvas.width !== w || raster.canvas.height !== h) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    raster = { canvas: c, ctx: c.getContext('2d'), image: new ImageData(w, h) };
  }
  const out = new Uint32Array(raster.image.data.buffer);
  const OPEN = 0xc028bef0, CLOSED = 0x66ff966e, BACK = 0x66aac83c, WALL = 0x2992928c, SHARED = 0xff4849e3, VIA = 0xffffffff;
  const per = w * h, top = layers.includes(0), bottom = layers.includes(1);
  for (let y = 0; y < h; y++) {
    const row = (h - 1 - y) * w;                    // the picture's rows run down, the board's up
    for (let x = 0; x < w; x++) {
      const a = y * w + x, b = per + a;
      const fa = top ? flags[a] : 0, fb = bottom ? flags[b] : 0;
      let px = 0;
      if ((fa | fb) & 2) px = SHARED;
      else if ((fa | fb) & 16) px = VIA;
      else if (top && nets[a] >= 0 && !(fa & 1)) px = pixel(nets[a], false);
      else if (bottom && nets[b] >= 0 && !(fb & 1)) px = pixel(nets[b], true);
      else if ((fa | fb) & 4) px = OPEN;
      else if ((fa | fb) & 8) px = CLOSED;
      else if ((fa | fb) & 64) px = BACK;
      else if ((top ? nets[a] : nets[b]) === -2) px = WALL;
      out[row + x] = px;
    }
  }
  raster.ctx.putImageData(raster.image, 0, 0);
  const g = board.pitch * view.s;
  ctx.imageSmoothingEnabled = g < 1.5;              // smoothed only where a point is under a pixel or so
  ctx.drawImage(raster.canvas, px0() - g / 2, py((h - 1) * board.pitch) - g / 2, w * g, h * g);
  ctx.imageSmoothingEnabled = true;
}
const px0 = () => view.ox;

function say() {
  if (!loaded) return;
  const [done, round, nets, routed, failed, expansions, length, vias, shared, current, rips, ripping, heat, kept, pass, turns, , bettered] = stats;
  const strategy = +$('strategy').value;
  const bits = [];
  if (!started) {
    bits.push(`${nets} net${nets === 1 ? '' : 's'} to route on a grid of ${grid.w} by ${grid.h} points, two layers.`);
    if (hemmed) bits.push(`${hemmed} pad${hemmed === 1 ? ' has' : 's have'} no way out on this grid, hemmed in by the pads beside ${hemmed === 1 ? 'it' : 'them'}: a finer grid or less clearance lets ${hemmed === 1 ? 'it' : 'them'} out.`);
  }
  else {
    if (!done) bits.push(pass ? `Routed; now improving, pass ${pass}: ${bettered} route${bettered === 1 ? '' : 's'} bettered so far…`
      : current >= 0 ? `Routing net ${current + 1}${ripping ? ', through the nets in its way' : ''}…` : 'Working…');
    bits.push(`${routed} of ${nets} nets routed${failed ? `, ${failed} given up` : ''}.`);
    if (strategy === 3) bits.push(`Round ${round}: ${shared} point${shared === 1 ? '' : 's'} shared.`);
    if (strategy === 2 && rips) bits.push(`${rips} net${rips === 1 ? '' : 's'} taken up and routed again.`);
    if (strategy === 6 && round) bits.push(`${round} move${round === 1 ? '' : 's'}, ${kept} kept, at temperature ${(heat / 10).toFixed(0)}.`);
    if (done && pass) bits.push(`Improved in ${pass} pass${pass === 1 ? '' : 'es'}: ${bettered} route${bettered === 1 ? '' : 's'} bettered.`);
    bits.push(`${(length / 100).toFixed(1)} mm of track, ${vias} via${vias === 1 ? '' : 's'}, ${turns} turn${turns === 1 ? '' : 's'}, ${expansions.toLocaleString()} search steps.`);
  }
  // when the attempt is over, the line is its verdict: routed, not finished (nets given up), or
  // not clean (tracks still through one another)
  const verdict = !(started && done && nets) ? null
    : shared ? ['bad', 'Not clean'] : failed ? ['part', 'Not finished'] : ['ok', 'Routed'];
  const line = $('stats');
  line.className = verdict ? `verdict ${verdict[0]}` : 'legend';
  const said = (verdict ? verdict[1] + '|' : '') + bits.join(' ');
  if (line.dataset.said !== said) {              // written only when it changes, for a screen reader's sake
    line.dataset.said = said;
    line.replaceChildren();
    if (verdict) line.append(Object.assign(document.createElement('strong'), { textContent: verdict[1] }));
    line.append(Object.assign(document.createElement('span'), { textContent: bits.join(' ') }));
  }
}

function buttons() {
  $('run').textContent = running ? 'Pause' : stats[0] ? 'Run again' : started ? 'Resume' : 'Run';
  $('run').classList.toggle('primary', !running);
}

function frame() {
  if (running) advance(perFrame());
  draw();
  say();
  requestAnimationFrame(frame);
}

// ---- the controls --------------------------------------------------------------------------

$('run').onclick = () => {
  if (!loaded) return;
  if (running) running = false;
  else {
    if (stats[0]) { send(); }
    running = true;
  }
  buttons();
};
$('step').onclick = () => { running = false; if (stats[0]) send(); advance(Math.max(1, Math.round(perFrame() / 4))); };
$('reset').onclick = () => send();
$('strategy').onchange = () => { $('about').textContent = ABOUT[+$('strategy').value]; send(); save(); };
$('order').onchange = () => { send(); save(); };
for (const id of ['diagonal', 'improve', 'viaweight', 'turnweight']) $(id).onchange = () => { send(); save(); };
$('speed').oninput = () => { $('speedout').textContent = `${perFrame().toLocaleString()} steps a frame`; };

for (const id of ['width', 'height', 'track', 'clearance', 'via', 'pitch']) {
  $(id).onchange = () => {
    const v = +$(id).value;
    if (!(v > 0)) return;
    board[id] = v;
    if (id === 'width' || id === 'height') board.outline = [];
    if (id === 'track' || id === 'clearance') { board.pitch = +(board.track + board.clearance).toFixed(3); board.edge = Math.max(board.edge, board.clearance); }
    fields();
    send();
    save();
  };
}

function fields() {
  for (const id of ['width', 'height', 'track', 'clearance', 'via', 'pitch']) $(id).value = board[id];
  const p = board.pads[selected];
  $('padw').value = (p ?? last).w;
  $('padh').value = (p ?? last).h;
  $('kind').value = (p ?? last).side;
  $('delete').disabled = !p;
  $('hint').textContent = tool === 'pad'
    ? 'Click the board to put a pad there, on the net picked below.'
    : p ? 'Drag the pad to move it. Its net, kind and size are below.' : 'Click a pad to select it; drag it to move it.';
  const list = $('netlist');
  const current = p ? p.net : net;
  const chips = [];
  const all = Math.max(netCount(), net + 1);
  const name = (n) => (board.names?.[n] ?? `net ${n + 1}`).replace(/[<>&]/g, '');
  for (let n = 0; n < all; n++) {
    if (all > 24 && n !== current) continue;       // a board of a hundred nets shows the one in hand
    chips.push(`<button type=button class=chip data-net=${n} aria-pressed=${n === current}><i style='background:${colour(n)}'></i>${name(n)}</button>`);
  }
  if (all > 24) chips.push(`<span class=muted>one of ${all} nets</span>`);
  chips.push(`<button type=button class=chip data-net=new aria-pressed=false>+ a new net</button>`);
  chips.push(`<button type=button class=chip data-net=-1 aria-pressed=${current === -1}><i style='background:${colour(-1)}'></i>no net</button>`);
  list.innerHTML = chips.join('');
  for (const b of $('tools').children) b.setAttribute('aria-pressed', String(b.dataset.tool === tool));
}

// the size and kind of the next pad: those of the last one touched
let last = { w: 1.7, h: 1.7, side: 2 };

$('netlist').onclick = (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  const n = b.dataset.net === 'new' ? Math.max(netCount(), net + 1) : +b.dataset.net;
  if (board.pads[selected]) { board.pads[selected].net = n; send(); save(); }
  net = n;
  fields();
};
$('tools').onclick = (e) => {
  const b = e.target.closest('button');
  if (!b) return;
  tool = b.dataset.tool;
  if (tool === 'pad') selected = -1;
  fields();
};
for (const id of ['padw', 'padh', 'kind']) {
  $(id).onchange = () => {
    const w = +$('padw').value, h = +$('padh').value, side = +$('kind').value;
    if (!(w > 0 && h > 0)) return;
    last = { w, h, side };
    const p = board.pads[selected];
    if (p) { Object.assign(p, { w, h, side, round: side === 2 && w === h }); send(); save(); }
  };
}
$('delete').onclick = () => remove();
$('clear').onclick = () => { board.pads = []; board.outline = []; selected = -1; net = 0; fields(); send(); save(); };
$('view').onchange = () => {};
$('pour').onchange = () => send();
$('share').onclick = async () => {
  save();
  try { await navigator.clipboard.writeText(location.href); $('share').textContent = 'Copied'; }
  catch { $('share').textContent = 'The link is in the address bar'; }
  setTimeout(() => ($('share').textContent = 'Copy a link to this board'), 1800);
};

function remove() {
  if (!board.pads[selected]) return;
  opened = null;
  board.pads.splice(selected, 1);
  selected = -1;
  fields();
  send();
  save();
}
addEventListener('keydown', (e) => {
  if ((e.key === 'Delete' || e.key === 'Backspace') && !/INPUT|SELECT/.test(document.activeElement.tagName)) { e.preventDefault(); remove(); }
});

const snap = (v) => Math.round(v / board.pitch) * board.pitch;
const hit = ({ x, y }) => {
  for (let i = board.pads.length - 1; i >= 0; i--) {
    const p = board.pads[i];
    if (Math.abs(x - p.x) <= Math.max(p.w / 2, 0.4) && Math.abs(y - p.y) <= Math.max(p.h / 2, 0.4)) return i;
  }
  return -1;
};
canvas.onpointerdown = (e) => {
  const at = mm(e);
  if (tool === 'pad') {
    if (at.x < 0 || at.y < 0 || at.x > board.width || at.y > board.height) return;
    opened = null;
    board.pads.push({ x: +snap(at.x).toFixed(3), y: +snap(at.y).toFixed(3), w: last.w, h: last.h, side: last.side, round: last.side === 2 && last.w === last.h, net });
    send();
    save();
    fields();
    return;
  }
  selected = hit(at);
  const p = board.pads[selected];
  if (p) {
    net = p.net;
    last = { w: p.w, h: p.h, side: p.side };
    drag = { dx: p.x - at.x, dy: p.y - at.y, moved: false };
    canvas.setPointerCapture(e.pointerId);
  }
  fields();
};
canvas.onpointermove = (e) => {
  const p = board.pads[selected];
  if (!drag || !p) return;
  const at = mm(e);
  const x = +Math.min(board.width, Math.max(0, snap(at.x + drag.dx))).toFixed(3);
  const y = +Math.min(board.height, Math.max(0, snap(at.y + drag.dy))).toFixed(3);
  if (x !== p.x || y !== p.y) { p.x = x; p.y = y; drag.moved = true; opened = null; send(); }
};
canvas.onpointerup = () => { if (drag?.moved) save(); drag = null; };

// ---- boards to start from, and the link to this one ------------------------------------------

const through = (x, y, n) => ({ x, y, w: 1.7, h: 1.7, side: 2, round: true, net: n });
const chip = (x, y, n) => ({ x, y, w: 0.9, h: 0.9, side: 0, round: false, net: n });
let presets = [
  { title: 'Two nets that cross', width: 18, height: 12, pads: [chip(3, 3, 0), chip(15, 9, 0), chip(15, 3, 1), chip(3, 9, 1)] },
  { title: 'A bus that must turn over', width: 20, height: 24,
    pads: Array.from({ length: 8 }, (_, n) => [through(3, 3 + 2.4 * n, n), through(17, 19.8 - 2.4 * n, n)]).flat() },
  { title: 'Three nets through a gap', width: 20, height: 12,
    pads: [chip(2.4, 3, 0), chip(17.4, 9, 0), chip(2.4, 6, 1), chip(17.4, 6, 1), chip(2.4, 9, 2), chip(17.4, 3, 2)],
    walls: [[9.9, 2.1], [9.9, 9.9]] },
  { title: 'A star of five pads on one net', width: 20, height: 16,
    pads: [chip(10.2, 8.1, 0), chip(3, 3, 0), chip(17.1, 3, 0), chip(3, 13.2, 0), chip(17.1, 13.2, 0), chip(10.2, 3, 1), chip(10.2, 13.2, 1), chip(3, 8.1, 2), chip(17.1, 8.1, 2)] },
];

async function loadPresets() {
  try {
    const more = await (await fetch('presets.json')).json();
    presets = presets.concat(more);
  } catch { /* the page stands without the bench's cases */ }
  const option = (p, i) => `<option value=${i}>${p.title.replace(/</g, '&lt;')}</option>`;
  const of = (label, test) => {
    const mine = presets.map((p, i) => [p, i]).filter(([p]) => test(p)).map(([p, i]) => option(p, i)).join('');
    return mine ? `<optgroup label='${label}'>${mine}</optgroup>` : '';
  };
  $('preset').innerHTML = of('Examples', (p) => !p.id) + of('Cases of the bench', (p) => p.id && !p.file)
    + of('Open hardware, to be routed again', (p) => Boolean(p.file));
  $('preset').onchange = () => pick(+$('preset').value);
}

let opened = null;   // the id of the case or the board that is open, while it is as it was opened

async function pick(i) {
  let p = presets[i];
  if (p.file && !p.pads) {                         // a board of open hardware is fetched when it is asked for
    $('stats').textContent = `Fetching ${p.title}…`;
    try { p = presets[i] = { ...(await (await fetch(p.file)).json()), ...p }; }
    catch (e) { $('stats').textContent = `${p.title} could not be fetched: ${e.message}`; return; }
  }
  board = { width: p.width, height: p.height, track: p.track ?? 0.15, clearance: p.clearance ?? 0.15, via: p.via ?? 0.6,
            edge: p.edge ?? 0.3, pitch: p.pitch ?? +((p.track ?? 0.15) + (p.clearance ?? 0.15)).toFixed(3),
            outline: p.outline ?? [], pads: p.pads.map((q) => ({ ...q })), pour: p.pour == null ? null : [p.pour].flat(), names: p.nets ?? null };
  opened = p.id ?? null;
  for (const [x, y] of p.walls ?? []) board.pads.push({ x, y, w: 1.2, h: 4.2, side: 2, round: false, net: -1 });
  selected = -1;
  net = 0;
  $('preset').value = i;
  const text = (s) => String(s).replace(/[<>&'"]/g, (c) => `&#${c.charCodeAt(0)};`);
  $('case').innerHTML = p.maker
    ? `<a href='${text(p.source)}'>${text(p.title)}</a>, by ${text(p.maker)}, under <a href='${text(p.license_url)}'>${text(p.license)}</a>. `
      + `Its pads and nets alone: the routing is taken away, and a pad is a plain rectangle or circle. ${text(p.note ?? '')}`
    : p.id
    ? `This is <a href='../cases/${p.id}.html'>${p.id}</a> of the bench, as its parts are placed: see how the routers and the toolchains do on it there.`
    : '';
  $('pourline').hidden = board.pour == null;
  if (board.pour != null) {
    const on = board.pads.filter((q) => board.pour.includes(q.net)).length;
    const names = board.pour.map((n) => board.names?.[n] ?? 'the ground').join(' and ');
    $('pourname').textContent = `Leave ${names} unrouted (${on} pads): the real board joins ${board.pour.length > 1 ? 'them' : 'it'} with a pour or a plane`;
  }
  fields();
  send();
  save();
}

function save() {
  if (board.pads.length > 150) {
    // too big for a link to hold: the link names the board, while it is as it was opened
    history.replaceState(null, '', location.pathname + (opened ? `?case=${opened}` : ''));
    return;
  }
  const s = { b: board, s: +$('strategy').value, o: +$('order').value, d: $('diagonal').checked ? 1 : 0,
              i: $('improve').checked ? 1 : 0, vw: +$('viaweight').value, tw: +$('turnweight').value };
  // the board is in the link's fragment; a ?case= it was opened by is dropped, so that a reload keeps the edits
  history.replaceState(null, '', location.pathname + '#' + btoa(unescape(encodeURIComponent(JSON.stringify(s)))));
}

function restore() {
  if (location.hash.length < 8) return false;
  try {
    const s = JSON.parse(decodeURIComponent(escape(atob(location.hash.slice(1)))));
    if (!Array.isArray(s.b.pads)) return false;
    board = s.b;
    $('strategy').value = s.s ?? 1;
    $('order').value = s.o ?? 0;
    $('diagonal').checked = (s.d ?? 0) === 1;      // a link from before there were diagonals keeps its square tracks
    $('improve').checked = s.i === 1;
    if (s.vw != null) $('viaweight').value = s.vw;
    if (s.tw != null) $('turnweight').value = s.tw;
    if (!Array.isArray(board.pour)) board.pour = board.pour == null ? null : [board.pour];
    $('about').textContent = ABOUT[+$('strategy').value];
    fields();
    send();
    return true;
  } catch { return false; }
}

$('about').textContent = ABOUT[1];
$('speed').oninput();
boot();
