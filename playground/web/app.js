// The autorouting playground: a board of pads and nets, edited here, routed by router.wasm (the
// Rust of playground/router), and drawn as it goes.  The page holds the board; the module holds
// the grid.  After every edit the board is written to the module again and the routing starts over.

const $ = (id) => document.getElementById(id);
const canvas = $('board');
const ctx = canvas.getContext('2d');

const ABOUT = [
  'Each net in turn sends a wave out from its copper, one grid point further each step, until it meets the pad it wants. It finds the shortest way there is, and looks everywhere to find it.',
  'The same search, but the points nearer the pad are tried first, so the wave is a finger and not a pond. What it finds is as short; it looks at far less.',
  'A* until a net is walled in by the nets before it. Then it is routed straight through them, the nets it crossed are taken up, and they are routed again afterwards.',
  'Every net is routed where it likes, through other nets if it likes, at a price. Each round the price of a shared point goes up, and the nets are all routed again, until no point is shared.',
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
let stats = new Int32Array(12);
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
  restore() || pick(0);
  frame();
}

/** Writes the board to the module and builds its grid; the routing is not started. */
function send() {
  const b = board;
  const v = [b.width, b.height, b.pitch, b.track, b.clearance, b.via, b.edge, b.outline.length];
  for (const [x, y] of b.outline) v.push(x, y);
  v.push(b.pads.length);
  for (const p of b.pads) v.push(p.x, p.y, p.w, p.h, p.side, p.round ? 1 : 0, p.net);
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
  wasm.paint();
  stats = new Int32Array(12);
  buttons();
}

let started = false;
function begin() {
  if (!loaded) return;
  wasm.start(+$('strategy').value, +$('order').value);
  started = true;
}

const perFrame = () => Math.round(Math.pow(10, ($('speed').value / 100) * 4.6));  // 1 to 40,000

function advance(n) {
  if (!loaded) return;
  if (!started) begin();
  if (wasm.step(n)) running = false;
  wasm.paint();
  stats = new Int32Array(wasm.memory.buffer, wasm.stats(), 12).slice();
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
    const show = $('view').value;
    const layers = show === 'top' ? [0] : show === 'bottom' ? [1] : [1, 0];
    const g = board.pitch * view.s;          // a grid step in pixels
    const half = Math.max(g / 2, 0.5);
    const idx = (l, x, y) => (l * grid.h + y) * grid.w + x;

    // what is closed to tracks, and the search's wave
    for (const l of layers) {
      for (let y = 0; y < grid.h; y++) {
        for (let x = 0; x < grid.w; x++) {
          const c = idx(l, x, y), f = flags[c];
          let fill = null;
          if (f & 8) fill = l === 0 ? 'rgba(110,150,255,0.40)' : 'rgba(110,150,255,0.22)';
          else if (f & 4) fill = 'rgba(240,190,40,0.75)';
          else if (nets[c] === -2 && l === layers[layers.length - 1]) fill = 'rgba(140,140,146,0.16)';
          if (fill) {
            ctx.fillStyle = fill;
            ctx.fillRect(px(x * board.pitch) - half, py(y * board.pitch) - half, 2 * half, 2 * half);
          }
        }
      }
    }
    // the tracks: a line from each point of a net's track to the same net's point to its right and above
    const w = Math.max(board.track * view.s, 1.5);
    for (const l of layers) {
      const byNet = new Map();
      const isTrack = (c) => nets[c] >= 0;
      for (let y = 0; y < grid.h; y++) {
        for (let x = 0; x < grid.w; x++) {
          const c = idx(l, x, y);
          if (!isTrack(c) || (flags[c] & 1 && !(flags[c] & 32) && !touches(nets, flags, l, x, y))) continue;
          const path = byNet.get(nets[c]) ?? byNet.set(nets[c], new Path2D()).get(nets[c]);
          const X = px(x * board.pitch), Y = py(y * board.pitch);
          if (x + 1 < grid.w && nets[idx(l, x + 1, y)] === nets[c]) { path.moveTo(X, Y); path.lineTo(X + g, Y); }
          if (y + 1 < grid.h && nets[idx(l, x, y + 1)] === nets[c]) { path.moveTo(X, Y); path.lineTo(X, Y - g); }
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
    // tracks through what another net keeps, and the vias
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

/** Whether a pad's point has a track of its own net beside it, so that the track is drawn into the pad. */
function touches(nets, flags, l, x, y) {
  const at = (X, Y) => (X >= 0 && Y >= 0 && X < grid.w && Y < grid.h ? (l * grid.h + Y) * grid.w + X : -1);
  const me = nets[at(x, y)];
  return [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dx, dy]) => {
    const c = at(x + dx, y + dy);
    return c >= 0 && nets[c] === me && !(flags[c] & 1);
  });
}

function say() {
  if (!loaded) return;
  const [done, round, nets, routed, failed, expansions, length, vias, shared, current, rips, ripping] = stats;
  const strategy = +$('strategy').value;
  const bits = [];
  if (!started) bits.push(`${nets} net${nets === 1 ? '' : 's'} to route on a grid of ${grid.w} by ${grid.h} points, two layers.`);
  else {
    bits.push(done ? (failed || shared ? 'Finished, not clean.' : 'Routed.') : current >= 0 ? `Routing net ${current + 1}${ripping ? ', through the nets in its way' : ''}…` : 'Working…');
    bits.push(`${routed} of ${nets} nets routed${failed ? `, ${failed} given up` : ''}.`);
    if (strategy === 3) bits.push(`Round ${round}: ${shared} point${shared === 1 ? '' : 's'} shared.`);
    if (strategy === 2 && rips) bits.push(`${rips} net${rips === 1 ? '' : 's'} taken up and routed again.`);
    bits.push(`${(length / 100).toFixed(1)} mm of track, ${vias} via${vias === 1 ? '' : 's'}, ${expansions.toLocaleString()} search steps.`);
  }
  $('stats').textContent = bits.join(' ');
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
  for (let n = 0; n < Math.max(netCount(), net + 1); n++) {
    chips.push(`<button type=button class=chip data-net=${n} aria-pressed=${n === current}><i style='background:${colour(n)}'></i>net ${n + 1}</button>`);
  }
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
$('share').onclick = async () => {
  save();
  try { await navigator.clipboard.writeText(location.href); $('share').textContent = 'Copied'; }
  catch { $('share').textContent = 'The link is in the address bar'; }
  setTimeout(() => ($('share').textContent = 'Copy a link to this board'), 1800);
};

function remove() {
  if (!board.pads[selected]) return;
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
  if (x !== p.x || y !== p.y) { p.x = x; p.y = y; drag.moved = true; send(); }
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
    presets = presets.concat(more.map((p) => ({ ...p, title: `${p.title} (${p.id})` })));
  } catch { /* the page stands without the bench's cases */ }
  $('preset').innerHTML = presets.map((p, i) => `<option value=${i}>${p.title.replace(/</g, '&lt;')}</option>`).join('');
  $('preset').onchange = () => pick(+$('preset').value);
}

function pick(i) {
  const p = presets[i];
  board = { width: p.width, height: p.height, track: p.track ?? 0.15, clearance: p.clearance ?? 0.15, via: p.via ?? 0.6,
            edge: p.edge ?? 0.3, pitch: +((p.track ?? 0.15) + (p.clearance ?? 0.15)).toFixed(3),
            outline: p.outline ?? [], pads: p.pads.map((q) => ({ ...q })) };
  for (const [x, y] of p.walls ?? []) board.pads.push({ x, y, w: 1.2, h: 4.2, side: 2, round: false, net: -1 });
  selected = -1;
  net = 0;
  $('preset').value = i;
  fields();
  send();
  save();
}

function save() {
  const s = { b: board, s: +$('strategy').value, o: +$('order').value };
  history.replaceState(null, '', '#' + btoa(unescape(encodeURIComponent(JSON.stringify(s)))));
}

function restore() {
  if (location.hash.length < 8) return false;
  try {
    const s = JSON.parse(decodeURIComponent(escape(atob(location.hash.slice(1)))));
    if (!Array.isArray(s.b.pads)) return false;
    board = s.b;
    $('strategy').value = s.s ?? 1;
    $('order').value = s.o ?? 0;
    $('about').textContent = ABOUT[+$('strategy').value];
    fields();
    send();
    return true;
  } catch { return false; }
}

$('about').textContent = ABOUT[1];
$('speed').oninput();
boot();
