//! Grid autorouters that can be watched: each is a state machine advanced a few search
//! expansions at a time, so that a page can draw the wave as it spreads.
//!
//! The board is a grid of points `pitch` apart on each of two copper layers. A track runs from
//! point to point, up, down, left or right, and changes layer by a via. A net's copper keeps other
//! nets' track centres out of a halo round it: the pads' is worked out from their shapes, a
//! track's and a via's from the rules. With the pitch at track width plus clearance, the default,
//! a track's halo is its own points and two nets may run side by side.
//!
//! Four strategies share one search:
//!
//! - **Lee**: a breadth-first wave from the net's copper to its next pad, the nets one after another.
//! - **A\***: the same search, pulled toward the pad by its distance.
//! - **Rip-up and reroute**: A\*, and where a net is walled in, it is routed through the nets in
//!   its way, which are taken up and routed again after it.
//! - **Negotiated congestion** (PathFinder): every net is routed where it likes, sharing points
//!   at a price; the price of a shared point rises each round, and the rounds go on until none
//!   is shared.
//!
//! `ffi` is the C ABI the page calls; nothing here depends on any crate.

use std::cmp::Ordering;
use std::collections::{BinaryHeap, VecDeque};

pub mod ffi;

const FREE: i16 = -1;
const WALL: i16 = -2;
const NONE: u32 = u32::MAX;
const VIA_COST: f32 = 8.0;
const RIP_COST: f32 = 30.0;
const MAX_RIPS: u32 = 6;
const MAX_ROUNDS: u32 = 60;

/// Where a pad's copper is.
#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Side {
    Top,
    Bottom,
    Through,
}

#[derive(Clone, Debug)]
pub struct Pad {
    pub x: f32,
    pub y: f32,
    pub w: f32,
    pub h: f32,
    pub side: Side,
    pub round: bool,
    /// The pad's net, or negative for a pad that is on none: copper in the way.
    pub net: i32,
}

/// A board to route, in millimetres, the origin at its lower left.
#[derive(Clone, Debug)]
pub struct Problem {
    pub width: f32,
    pub height: f32,
    pub pitch: f32,
    pub track: f32,
    pub clearance: f32,
    pub via: f32,
    pub edge: f32,
    /// The outline's corners; empty for the whole rectangle.
    pub outline: Vec<(f32, f32)>,
    pub pads: Vec<Pad>,
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Strategy {
    Lee,
    AStar,
    RipUp,
    Negotiated,
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Order {
    AsGiven,
    ShortestFirst,
    LongestFirst,
}

struct Net {
    pads: Vec<usize>,
    connected: Vec<bool>,
    /// The points its tracks run through, and those of its vias on the top layer.
    centres: Vec<u32>,
    vias: Vec<u32>,
    /// Every point its tracks and vias keep others out of, once for each time it is kept.
    halo: Vec<u32>,
    routed: bool,
    failed: bool,
    rips: u32,
}

#[derive(PartialEq)]
struct Open(f32, u32);
impl Eq for Open {}
impl Ord for Open {
    fn cmp(&self, o: &Self) -> Ordering {
        o.0.total_cmp(&self.0).then(o.1.cmp(&self.1)) // the least cost first
    }
}
impl PartialOrd for Open {
    fn partial_cmp(&self, o: &Self) -> Option<Ordering> {
        Some(self.cmp(o))
    }
}

#[derive(PartialEq, Clone, Copy)]
enum Phase {
    /// Pick the next net, or end the round.
    Next,
    /// Start the search for the current net's next pad.
    Begin,
    Searching,
    Done,
}

pub struct Router {
    pub gw: usize,
    pub gh: usize,
    pitch: f32,
    /// By point: the net whose pad or pad's halo it is, FREE, or WALL.
    fixed: Vec<i16>,
    /// By point: the net of the pad it is copper of, or FREE; and which pad.
    pad_net: Vec<i16>,
    pad_at: Vec<u32>,
    pad_cells: Vec<Vec<u32>>,
    nets: Vec<Net>,
    /// By point: how many nets' tracks and vias keep it; and how many of those are the net's
    /// now being routed.
    usage: Vec<u16>,
    own: Vec<u16>,
    /// By point: the net whose track runs through it, the last to if several do.
    centre: Vec<i16>,
    /// The halo of a track and of a via, in points, as a square's half side.
    rt: i32,
    rv: i32,

    strategy: Strategy,
    queue: VecDeque<usize>,
    cur: usize,
    phase: Phase,
    ripping: bool,
    round: u32,
    present: f32,
    history: Vec<f32>,

    // the search
    sid: u32,
    g: Vec<f32>,
    seen: Vec<u32>,
    closed: Vec<u32>,
    parent: Vec<u32>,
    target: Vec<u32>,
    heap: BinaryHeap<Open>,
    tbox: (i32, i32, i32, i32),
    mark: Vec<u32>,
    mark_id: u32,

    pub expansions: u64,
    total_rips: u32,
    last_path: Vec<u32>,
}

fn point_segment(px: f32, py: f32, a: (f32, f32), b: (f32, f32)) -> f32 {
    let (dx, dy) = (b.0 - a.0, b.1 - a.1);
    let n = dx * dx + dy * dy;
    let t = if n == 0.0 { 0.0 } else { (((px - a.0) * dx + (py - a.1) * dy) / n).clamp(0.0, 1.0) };
    ((px - a.0 - t * dx).powi(2) + (py - a.1 - t * dy).powi(2)).sqrt()
}

fn inside(px: f32, py: f32, poly: &[(f32, f32)]) -> bool {
    let mut hit = false;
    for i in 0..poly.len() {
        let (a, b) = (poly[i], poly[(i + 1) % poly.len()]);
        if (a.1 > py) != (b.1 > py) && px < a.0 + (py - a.1) * (b.0 - a.0) / (b.1 - a.1) {
            hit = !hit;
        }
    }
    hit
}

impl Pad {
    /// How far a point is from the pad's copper: nothing, or less, inside it.
    fn distance(&self, px: f32, py: f32) -> f32 {
        let (dx, dy) = ((px - self.x).abs(), (py - self.y).abs());
        if self.round {
            (dx * dx + dy * dy).sqrt() - self.w.min(self.h) / 2.0
        } else {
            let (ox, oy) = (dx - self.w / 2.0, dy - self.h / 2.0);
            if ox <= 0.0 && oy <= 0.0 {
                ox.max(oy)
            } else {
                (ox.max(0.0).powi(2) + oy.max(0.0).powi(2)).sqrt()
            }
        }
    }
}

impl Router {
    /// The board as a grid, its pads and their halos marked. `Err` says why it cannot be made.
    pub fn new(p: &Problem) -> Result<Router, &'static str> {
        if !(p.pitch > 0.0 && p.width > 0.0 && p.height > 0.0) {
            return Err("the board and the pitch must have a size");
        }
        let gw = (p.width / p.pitch + 1e-4).floor() as usize + 1;
        let gh = (p.height / p.pitch + 1e-4).floor() as usize + 1;
        if gw * gh > 640 * 640 {
            return Err("the grid is over 640 by 640 points: widen the pitch or shrink the board");
        }
        let n = 2 * gw * gh;
        let eps = 1e-4;
        let outline: Vec<(f32, f32)> = if p.outline.len() >= 3 {
            p.outline.clone()
        } else {
            vec![(0.0, 0.0), (p.width, 0.0), (p.width, p.height), (0.0, p.height)]
        };
        let mut r = Router {
            gw, gh, pitch: p.pitch,
            fixed: vec![FREE; n], pad_net: vec![FREE; n], pad_at: vec![NONE; n], pad_cells: vec![Vec::new(); p.pads.len()],
            nets: Vec::new(), usage: vec![0; n], own: vec![0; n], centre: vec![FREE; n],
            rt: (((p.track + p.clearance) / p.pitch - eps).ceil() as i32 - 1).max(0),
            rv: (((p.via / 2.0 + p.clearance + p.track / 2.0) / p.pitch - eps).ceil() as i32 - 1).max(0),
            strategy: Strategy::AStar, queue: VecDeque::new(), cur: 0, phase: Phase::Done, ripping: false,
            round: 0, present: 0.5, history: vec![0.0; n],
            sid: 0, g: vec![0.0; n], seen: vec![0; n], closed: vec![0; n], parent: vec![NONE; n], target: vec![0; n],
            heap: BinaryHeap::new(), tbox: (0, 0, 0, 0), mark: vec![0; n], mark_id: 0,
            expansions: 0, total_rips: 0, last_path: Vec::new(),
        };
        // the edge: a track's centre keeps half its width and the edge clearance inside the outline
        let keep = p.edge + p.track / 2.0 - eps;
        for y in 0..gh {
            for x in 0..gw {
                let (px, py) = (x as f32 * p.pitch, y as f32 * p.pitch);
                let d = (0..outline.len()).map(|i| point_segment(px, py, outline[i], outline[(i + 1) % outline.len()]))
                    .fold(f32::INFINITY, f32::min);
                if d < keep || !inside(px, py, &outline) {
                    r.fixed[y * gw + x] = WALL;
                    r.fixed[(gh + y) * gw + x] = WALL;
                }
            }
        }
        // the pads' copper first, then their halos, so that copper is never lost to a neighbour's halo
        let nets = p.pads.iter().map(|q| q.net + 1).max().unwrap_or(0).max(0) as usize;
        let halo = p.clearance + p.track / 2.0 - eps;
        let layers = |s: Side| match s { Side::Top => 0..1, Side::Bottom => 1..2, Side::Through => 0..2 };
        let span = |c: f32, half: f32, max: usize| {
            let lo = ((c - half) / p.pitch).floor().max(0.0) as usize;
            let hi = (((c + half) / p.pitch).ceil().max(0.0) as usize).min(max - 1);
            lo..=hi
        };
        for (i, q) in p.pads.iter().enumerate() {
            let own = if q.net >= 0 { q.net as i16 } else { WALL };
            let mut cells = Vec::new();
            for l in layers(q.side) {
                for y in span(q.y, q.h / 2.0, gh) {
                    for x in span(q.x, q.w / 2.0, gw) {
                        if q.distance(x as f32 * p.pitch, y as f32 * p.pitch) <= eps {
                            cells.push(((l * gh + y) * gw + x) as u32);
                        }
                    }
                }
                if cells.iter().all(|&c| c as usize / (gw * gh) != l) {
                    // a pad that falls between the points has the point nearest its middle
                    let x = ((q.x / p.pitch).round().max(0.0) as usize).min(gw - 1);
                    let y = ((q.y / p.pitch).round().max(0.0) as usize).min(gh - 1);
                    cells.push(((l * gh + y) * gw + x) as u32);
                }
            }
            for &c in &cells {
                r.fixed[c as usize] = own;
                r.pad_net[c as usize] = own;
                r.pad_at[c as usize] = i as u32;
            }
            r.pad_cells[i] = cells;
        }
        for q in &p.pads {
            let own = if q.net >= 0 { q.net as i16 } else { WALL };
            for l in layers(q.side) {
                for y in span(q.y, q.h / 2.0 + halo, gh) {
                    for x in span(q.x, q.w / 2.0 + halo, gw) {
                        let c = (l * gh + y) * gw + x;
                        if r.pad_net[c] != FREE || q.distance(x as f32 * p.pitch, y as f32 * p.pitch) >= halo {
                            continue;
                        }
                        r.fixed[c] = if r.fixed[c] == FREE || r.fixed[c] == own { own } else { WALL };
                    }
                }
            }
        }
        for net in 0..nets {
            let pads: Vec<usize> = (0..p.pads.len()).filter(|&i| p.pads[i].net == net as i32).collect();
            r.nets.push(Net { connected: vec![false; pads.len()], pads, centres: Vec::new(), vias: Vec::new(),
                              halo: Vec::new(), routed: false, failed: false, rips: 0 });
        }
        Ok(r)
    }

    /// Begins routing afresh by `strategy`, the nets in `order`.
    pub fn start(&mut self, strategy: Strategy, order: Order, pads: &[Pad]) {
        for i in 0..self.nets.len() {
            self.rip(i);
            self.nets[i].failed = false;
            self.nets[i].rips = 0;
        }
        self.history.iter_mut().for_each(|h| *h = 0.0);
        self.strategy = strategy;
        let mut order_of: Vec<usize> = (0..self.nets.len()).filter(|&i| self.nets[i].pads.len() > 1).collect();
        let size = |net: &Net| {
            let (xs, ys): (Vec<f32>, Vec<f32>) = net.pads.iter().map(|&i| (pads[i].x, pads[i].y)).unzip();
            let span = |v: &[f32]| v.iter().cloned().fold(f32::MIN, f32::max) - v.iter().cloned().fold(f32::MAX, f32::min);
            span(&xs) + span(&ys)
        };
        match order {
            Order::AsGiven => {}
            Order::ShortestFirst => order_of.sort_by(|&a, &b| size(&self.nets[a]).total_cmp(&size(&self.nets[b]))),
            Order::LongestFirst => order_of.sort_by(|&a, &b| size(&self.nets[b]).total_cmp(&size(&self.nets[a]))),
        }
        for (i, net) in self.nets.iter_mut().enumerate() {
            net.routed = net.pads.len() <= 1 && !order_of.contains(&i);
        }
        self.queue = order_of.into();
        self.round = 1;
        self.present = 0.5;
        self.expansions = 0;
        self.total_rips = 0;
        self.phase = Phase::Next;
        self.heap.clear();
        self.last_path.clear();
    }

    fn xy(&self, c: u32) -> (i32, i32, usize) {
        let per = self.gw * self.gh;
        let (l, rest) = (c as usize / per, c as usize % per);
        ((rest % self.gw) as i32, (rest / self.gw) as i32, l)
    }

    fn at(&self, x: i32, y: i32, l: usize) -> Option<usize> {
        (x >= 0 && y >= 0 && (x as usize) < self.gw && (y as usize) < self.gh).then(|| (l * self.gh + y as usize) * self.gw + x as usize)
    }

    /// Takes a net's tracks and vias up.
    fn rip(&mut self, i: usize) {
        let net = &mut self.nets[i];
        for &c in &net.halo {
            self.usage[c as usize] -= 1;
        }
        for &c in &net.centres {
            if self.centre[c as usize] == i as i16 {
                self.centre[c as usize] = FREE;
            }
        }
        net.halo.clear();
        net.centres.clear();
        net.vias.clear();
        net.routed = false;
        net.connected.iter_mut().for_each(|c| *c = false);
    }

    /// Keeps the points within `r` of (x, y) on layer `l` for the net now being routed.
    fn keep(&mut self, x: i32, y: i32, l: usize, r: i32) {
        for dy in -r..=r {
            for dx in -r..=r {
                if let Some(c) = self.at(x + dx, y + dy, l) {
                    self.usage[c] += 1;
                    self.own[c] += 1;
                    self.nets[self.cur].halo.push(c as u32);
                }
            }
        }
    }

    /// How many other nets keep a point.
    fn others(&self, c: usize) -> u16 {
        self.usage[c] - self.own[c]
    }

    /// What it costs the current net to run a track through a point, or None where it may not.
    fn enter(&self, c: usize) -> Option<f32> {
        let f = self.fixed[c];
        if f == WALL || (f >= 0 && f as usize != self.cur) {
            return None;
        }
        let others = self.others(c) as f32;
        match self.strategy {
            Strategy::Negotiated => Some((1.0 + self.history[c]) * (1.0 + self.present * others)),
            _ if others == 0.0 => Some(1.0),
            _ if self.ripping => Some(1.0 + RIP_COST * others),
            _ => None,
        }
    }

    /// What a via at (x, y) costs the current net beyond its two points, or None where none fits.
    fn via(&self, x: i32, y: i32) -> Option<f32> {
        let mut cost = VIA_COST;
        for l in 0..2 {
            for dy in -self.rv..=self.rv {
                for dx in -self.rv..=self.rv {
                    let c = self.at(x + dx, y + dy, l)?;
                    if dx == 0 && dy == 0 {
                        continue;
                    }
                    let f = self.fixed[c];
                    if f == WALL || (f >= 0 && f as usize != self.cur) {
                        return None;
                    }
                    let others = self.others(c) as f32;
                    cost += match self.strategy {
                        Strategy::Negotiated => self.present * others,
                        _ if others == 0.0 => 0.0,
                        _ if self.ripping => RIP_COST * others,
                        _ => return None,
                    };
                }
            }
        }
        Some(cost)
    }

    fn heuristic(&self, c: u32) -> f32 {
        if self.strategy == Strategy::Lee {
            return 0.0;
        }
        let (x, y, _) = self.xy(c);
        let (x0, y0, x1, y1) = self.tbox;
        ((x0 - x).max(x - x1).max(0) + (y0 - y).max(y - y1).max(0)) as f32
    }

    /// Opens the search from the net's copper so far to the pads it has yet to reach.
    fn begin(&mut self) {
        self.sid += 1;
        self.heap.clear();
        let sid = self.sid;
        let net = &self.nets[self.cur];
        let mut tbox = (i32::MAX, i32::MAX, i32::MIN, i32::MIN);
        let (mut sources, mut targets) = (net.centres.clone(), Vec::new());
        for (k, &pad) in net.pads.iter().enumerate() {
            if net.connected[k] { sources.extend(&self.pad_cells[pad]) } else { targets.extend(&self.pad_cells[pad]) }
        }
        for &c in &targets {
            self.target[c as usize] = sid;
            let (x, y, _) = self.xy(c);
            tbox = (tbox.0.min(x), tbox.1.min(y), tbox.2.max(x), tbox.3.max(y));
        }
        self.tbox = tbox;
        for &c in &sources {
            self.g[c as usize] = 0.0;
            self.seen[c as usize] = sid;
            self.parent[c as usize] = NONE;
            let h = self.heuristic(c);
            self.heap.push(Open(h, c));
        }
        self.phase = Phase::Searching;
    }

    fn relax(&mut self, from: u32, to: usize, cost: f32) {
        let g = self.g[from as usize] + cost;
        if self.closed[to] != self.sid && (self.seen[to] != self.sid || g < self.g[to]) {
            self.g[to] = g;
            self.seen[to] = self.sid;
            self.parent[to] = from;
            let f = g + self.heuristic(to as u32);
            self.heap.push(Open(f, to as u32));
        }
    }

    /// One expansion of the search. True when the search is over, with a path or without.
    fn expand(&mut self) -> bool {
        let Some(Open(_, c)) = self.heap.pop() else {
            self.dead_end();
            return true;
        };
        if self.closed[c as usize] == self.sid {
            return false;
        }
        self.closed[c as usize] = self.sid;
        self.expansions += 1;
        if self.target[c as usize] == self.sid {
            self.arrive(c);
            return true;
        }
        let (x, y, l) = self.xy(c);
        for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
            if let Some(to) = self.at(x + dx, y + dy, l) {
                if let Some(cost) = self.enter(to) {
                    self.relax(c, to, cost);
                }
            }
        }
        let to = self.at(x, y, 1 - l).unwrap();
        let me = self.cur as i16;
        if self.pad_net[c as usize] == me && self.pad_net[to] == me {
            self.relax(c, to, 0.0); // a through-hole pad of the net's own is a way through for nothing
        } else if let (Some(step), Some(via)) = (self.enter(to), self.via(x, y)) {
            self.relax(c, to, step + via);
        }
        false
    }

    /// The search has run out: route through other nets if the strategy allows, or give the net up.
    fn dead_end(&mut self) {
        if self.strategy == Strategy::RipUp && !self.ripping && self.total_rips < 20 * self.nets.len() as u32 {
            self.ripping = true;
            self.phase = Phase::Begin;
            return;
        }
        self.ripping = false;
        self.nets[self.cur].failed = true;
        self.finish_net();
    }

    /// The search has reached a pad: the path is laid, and what it runs through is taken up.
    fn arrive(&mut self, end: u32) {
        let mut path = vec![end];
        while self.parent[*path.last().unwrap() as usize] != NONE {
            path.push(self.parent[*path.last().unwrap() as usize]);
        }
        let me = self.cur as i16;
        let mut vias = Vec::new();
        for w in path.windows(2) {
            let ((x, y, l0), (_, _, l1)) = (self.xy(w[0]), self.xy(w[1]));
            if l0 != l1 && !(self.pad_net[w[0] as usize] == me && self.pad_net[w[1] as usize] == me) {
                vias.push((x, y));
            }
        }
        if self.ripping {
            // every net that keeps a point the path needs is in its way
            self.mark_id += 1;
            for &c in &path {
                self.mark[c as usize] = self.mark_id;
            }
            for &(x, y) in &vias {
                for l in 0..2 {
                    for dy in -self.rv..=self.rv {
                        for dx in -self.rv..=self.rv {
                            if let Some(c) = self.at(x + dx, y + dy, l) {
                                self.mark[c] = self.mark_id;
                            }
                        }
                    }
                }
            }
            let blockers: Vec<usize> = (0..self.nets.len())
                .filter(|&i| i != self.cur && self.nets[i].halo.iter().any(|&c| self.mark[c as usize] == self.mark_id))
                .collect();
            self.ripping = false;
            if blockers.iter().any(|&i| self.nets[i].rips >= MAX_RIPS) {
                self.nets[self.cur].failed = true;
                self.finish_net();
                return;
            }
            for i in blockers {
                self.rip(i);
                self.nets[i].rips += 1;
                self.total_rips += 1;
                self.queue.push_back(i);
            }
        }
        for &c in &path {
            let (x, y, l) = self.xy(c);
            self.keep(x, y, l, self.rt);
            if self.pad_net[c as usize] == FREE {
                self.centre[c as usize] = me;
            }
            self.nets[self.cur].centres.push(c);
        }
        for &(x, y) in &vias {
            self.keep(x, y, 0, self.rv);
            self.keep(x, y, 1, self.rv);
            let c = self.at(x, y, 0).unwrap() as u32;
            self.nets[self.cur].vias.push(c);
        }
        let pad = self.pad_at[end as usize] as usize;
        let k = self.nets[self.cur].pads.iter().position(|&p| p == pad).unwrap();
        self.nets[self.cur].connected[k] = true;
        self.last_path = path;
        if self.nets[self.cur].connected.iter().all(|&c| c) {
            self.nets[self.cur].routed = true;
            self.finish_net();
        } else {
            self.phase = Phase::Begin;
        }
    }

    fn finish_net(&mut self) {
        for i in 0..self.nets[self.cur].halo.len() {
            let c = self.nets[self.cur].halo[i] as usize;
            self.own[c] = 0;
        }
        self.phase = Phase::Next;
    }

    /// The points where a net's track runs through what another net keeps.
    fn shared(&mut self) -> Vec<u32> {
        let mut out = Vec::new();
        for i in 0..self.nets.len() {
            for k in 0..self.nets[i].halo.len() {
                self.own[self.nets[i].halo[k] as usize] += 1;
            }
            for &c in &self.nets[i].centres {
                if self.usage[c as usize] > self.own[c as usize] {
                    out.push(c);
                }
            }
            for k in 0..self.nets[i].halo.len() {
                self.own[self.nets[i].halo[k] as usize] = 0;
            }
        }
        out
    }

    fn next(&mut self) {
        if let Some(i) = self.queue.pop_front() {
            self.cur = i;
            if self.strategy == Strategy::Negotiated {
                self.rip(i);
                self.nets[i].failed = false;
            }
            self.nets[i].connected[0] = true;
            self.phase = Phase::Begin;
            return;
        }
        if self.strategy == Strategy::Negotiated {
            let shared = self.shared();
            if !shared.is_empty() && self.round < MAX_ROUNDS {
                for c in shared {
                    self.history[c as usize] += 0.4;
                }
                self.present *= 1.6;
                self.round += 1;
                self.queue = (0..self.nets.len()).filter(|&i| self.nets[i].pads.len() > 1).collect();
                return;
            }
        }
        self.phase = Phase::Done;
    }

    /// Advances the routing by up to `budget` search expansions. True when it is over.
    pub fn step(&mut self, budget: u32) -> bool {
        let mut left = budget;
        while left > 0 {
            match self.phase {
                Phase::Done => return true,
                Phase::Next => self.next(),
                Phase::Begin => self.begin(),
                Phase::Searching => {
                    self.expand();
                    left -= 1;
                }
            }
        }
        self.phase == Phase::Done
    }

    pub fn done(&self) -> bool {
        self.phase == Phase::Done
    }

    /// What there is to say of the routing so far: see `ffi::stats` for the order.
    pub fn stats(&mut self) -> [i32; 12] {
        let shared = if self.strategy == Strategy::Negotiated { self.shared().len() } else { 0 };
        let wired = self.nets.iter().filter(|n| n.pads.len() > 1);
        [
            self.done() as i32,
            self.round as i32,
            wired.clone().count() as i32,
            wired.clone().filter(|n| n.routed).count() as i32,
            wired.filter(|n| n.failed).count() as i32,
            self.expansions.min(i32::MAX as u64) as i32,
            (self.nets.iter().map(|n| n.centres.len()).sum::<usize>() as f32 * self.pitch * 100.0) as i32,
            self.nets.iter().map(|n| n.vias.len()).sum::<usize>() as i32,
            shared as i32,
            if self.phase == Phase::Searching || self.phase == Phase::Begin { self.cur as i32 } else { -1 },
            self.total_rips as i32,
            self.ripping as i32,
        ]
    }

    /// The board as a page draws it: by point, the net whose copper is there (a track's, else a
    /// pad's), FREE or WALL; and flags, bit 0 a pad's copper, bit 1 a track through what another
    /// net keeps, bit 2 a point the search has open, bit 3 one it has closed, bit 4 a via, bit 5
    /// the path laid last.
    pub fn paint(&mut self, net: &mut [i16], flags: &mut [u8]) {
        let live = self.phase == Phase::Searching;
        for c in 0..net.len() {
            net[c] = if self.pad_net[c] != FREE { self.pad_net[c] } else if self.centre[c] != FREE { self.centre[c] }
                     else if self.fixed[c] == WALL { WALL } else { FREE };
            flags[c] = (self.pad_net[c] != FREE) as u8
                | if live && self.closed[c] == self.sid { 8 } else if live && self.seen[c] == self.sid { 4 } else { 0 };
        }
        for c in self.shared() {
            flags[c as usize] |= 2;
        }
        let per = self.gw * self.gh;
        for n in &self.nets {
            for &c in &n.vias {
                flags[c as usize] |= 16;
                flags[c as usize + per] |= 16;
            }
        }
        for &c in &self.last_path {
            flags[c as usize] |= 32;
        }
    }

    /// Whether every net is whole and no track runs through what another net keeps: for the tests.
    pub fn sound(&mut self) -> bool {
        let whole = self.nets.iter().all(|n| n.pads.len() <= 1 || (n.routed && !n.failed));
        whole && self.shared().is_empty()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn pad(x: f32, y: f32, net: i32, side: Side) -> Pad {
        Pad { x, y, w: 0.8, h: 0.95, side, round: false, net }
    }

    fn board(pads: Vec<Pad>, width: f32, height: f32) -> Problem {
        Problem { width, height, pitch: 0.3, track: 0.15, clearance: 0.15, via: 0.6, edge: 0.3, outline: vec![], pads }
    }

    fn solve(p: &Problem, s: Strategy) -> Router {
        let mut r = Router::new(p).unwrap();
        r.start(s, Order::AsGiven, &p.pads);
        let mut steps = 0;
        while !r.step(10_000) {
            steps += 1;
            assert!(steps < 10_000, "the router does not end");
        }
        r
    }

    /// Two nets on a board's diagonals: their straight routes cross.
    fn crossing() -> Problem {
        board(vec![pad(3.0, 3.0, 0, Side::Top), pad(12.0, 12.0, 0, Side::Top),
                   pad(12.0, 3.0, 1, Side::Top), pad(3.0, 12.0, 1, Side::Top)], 15.0, 15.0)
    }

    /// Eight nets from one column of through-hole pads to another, in the opposite order.
    fn reversed() -> Problem {
        let mut pads = Vec::new();
        for n in 0..8 {
            let round = |x: f32, y: f32| Pad { x, y, w: 1.7, h: 1.7, side: Side::Through, round: true, net: n };
            pads.push(round(3.0, 3.11 + 2.54 * n as f32));
            pads.push(round(17.0, 20.89 - 2.54 * n as f32));
        }
        board(pads, 20.0, 24.0)
    }

    #[test]
    fn every_strategy_routes_a_crossing() {
        for s in [Strategy::Lee, Strategy::AStar, Strategy::RipUp, Strategy::Negotiated] {
            let mut r = solve(&crossing(), s);
            // one net changes layer or goes round the end of the other: either is sound
            assert!(r.sound(), "{s:?} leaves the crossing unrouted or shared");
        }
    }

    #[test]
    fn a_star_expands_less_than_lee() {
        let (lee, star) = (solve(&crossing(), Strategy::Lee), solve(&crossing(), Strategy::AStar));
        assert!(star.expansions < lee.expansions);
    }

    #[test]
    fn the_reversed_bus_is_routed_by_the_strategies_that_take_nets_up() {
        for s in [Strategy::RipUp, Strategy::Negotiated] {
            let mut r = solve(&reversed(), s);
            assert!(r.sound(), "{s:?} leaves the reversed bus unrouted or shared: {:?}", r.stats());
        }
    }

    #[test]
    fn a_net_walled_in_fails_and_the_rest_are_routed() {
        // net 0's second pad is ringed by pads of no net
        let mut pads = vec![pad(2.0, 2.0, 0, Side::Through), pad(8.0, 8.0, 0, Side::Through),
                            pad(2.0, 8.0, 1, Side::Top), pad(2.0, 5.0, 1, Side::Top)];
        for (dx, dy) in [(-1.5, 0.0), (1.5, 0.0), (0.0, -1.5), (0.0, 1.5), (-1.2, -1.2), (1.2, 1.2), (-1.2, 1.2), (1.2, -1.2)] {
            pads.push(Pad { x: 8.0 + dx, y: 8.0 + dy, w: 1.6, h: 1.6, side: Side::Through, round: false, net: -1 });
        }
        let mut r = solve(&board(pads, 12.0, 12.0), Strategy::RipUp);
        let s = r.stats();
        assert_eq!((s[2], s[3], s[4]), (2, 1, 1), "{s:?}");
    }
}
