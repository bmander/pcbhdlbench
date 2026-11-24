//! Grid autorouters that can be watched: each is a state machine advanced a few search
//! expansions at a time, so that a page can draw the wave as it spreads.
//!
//! The board is a grid of points `pitch` apart on each of two copper layers. A track runs from
//! point to point, up, down, left or right, and changes layer by a via. A net's copper keeps other
//! nets' track centres out of a halo round it: the pads' is worked out from their shapes, a
//! track's and a via's from the rules. With the pitch at track width plus clearance, the default,
//! a track's halo is its own points and two nets may run side by side.
//!
//! Six strategies share one search:
//!
//! - **Lee**: a breadth-first wave from the net's copper to its next pad, the nets one after another.
//! - **Bidirectional**: Lee's wave from both ends at once, the two meeting in the middle.
//! - **A\***: the same search, pulled toward the pad by its distance.
//! - **Hadlock**: the points are tried in the order of their detours, the steps a way to them
//!   takes away from the pad; a way with none is followed straight to its end.
//! - **Rip-up and reroute**: A\*, and where a net is walled in, it is routed through the nets in
//!   its way, which are taken up and routed again after it.
//! - **Negotiated congestion** (PathFinder): every net is routed where it likes, sharing points
//!   at a price; the price of a shared point rises each round, and the rounds go on until none
//!   is shared.
//! - **Simulated annealing**: A\* first, then moves: a net left unrouted is routed through the
//!   nets in its way, those are laid again round it, and the move is kept if the board is the
//!   better for it, or, while the temperature is high, sometimes when it is the worse.
//!
//! A track may also step diagonally where the board is told to allow it. A diagonal step passes
//! between two points, which must both be free to its net and which it keeps as its own, so that
//! nothing else runs through them beside it.
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
    Hadlock,
    Bidirectional,
    Anneal,
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
    /// Its tracks, piece by piece: the two points each runs between, on one layer.
    segs: Vec<(u32, u32)>,
    /// Every point its tracks and vias keep others out of, once for each time it is kept.
    halo: Vec<u32>,
    routed: bool,
    failed: bool,
    rips: u32,
}

/// A net's routing as it was, to be put back if an annealing move is not kept.
struct Saved {
    net: usize,
    centres: Vec<u32>,
    vias: Vec<u32>,
    segs: Vec<(u32, u32)>,
    halo: Vec<u32>,
    connected: Vec<bool>,
    routed: bool,
    failed: bool,
}

/// An annealing move in hand: the nets it has touched as they were, those it took up and has
/// yet to lay again, and what the board cost before it.
struct Move {
    saved: Vec<Saved>,
    todo: Vec<usize>,
    before: f32,
    /// How many nets the move has laid again. The first few push through what is in their way
    /// as the move's own net did, so that a move can shift a whole neighbourhood over; after
    /// that a net goes round what is there, and the move ends.
    relaid: u32,
}

/// How many of a move's displaced nets may displace others in their turn.
const RIPPLE: u32 = 10;

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
    /// By place (a point of either layer): what stands within a via's halo of it on either layer.
    /// `via_fixed` is of the pads: FREE, one net's alone, or WALL. `near` and `near_own` are of
    /// the tracks and vias: `usage` and `own` summed over the halo, so that whether a via fits is
    /// looked up and not counted.
    via_fixed: Vec<i16>,
    near: Vec<u32>,
    near_own: Vec<u32>,
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
    // the wave from the pads, of the bidirectional search: as the five above
    g2: Vec<f32>,
    seen2: Vec<u32>,
    closed2: Vec<u32>,
    parent2: Vec<u32>,
    heap2: BinaryHeap<Open>,
    /// The cheapest way yet found through a point both waves have reached: its cost, the point
    /// on the first wave's side, and the one on the other's.
    meet: (f32, u32, u32),
    tbox: (i32, i32, i32, i32),
    mark: Vec<u32>,
    mark_id: u32,

    pub expansions: u64,
    total_rips: u32,
    last_path: Vec<u32>,

    /// Whether a track may step diagonally.
    pub diagonal: bool,
    // the annealing: the move in hand, the temperature and how it cools, the moves made and kept
    mv: Option<Move>,
    temp: f32,
    alpha: f32,
    moves: u32,
    max_moves: u32,
    accepted: u32,
    rng: u64,
}

const DIAGONAL: f32 = std::f32::consts::SQRT_2;
/// What an unrouted net costs the annealing, in steps of track; and where it starts and ends hot.
const UNROUTED: f32 = 600.0;
const HOT: f32 = 300.0;
const COLD: f32 = 3.0;

fn point_segment(px: f32, py: f32, a: (f32, f32), b: (f32, f32)) -> f32 {
    let (dx, dy) = (b.0 - a.0, b.1 - a.1);
    let n = dx * dx + dy * dy;
    let t = if n == 0.0 { 0.0 } else { (((px - a.0) * dx + (py - a.1) * dy) / n).clamp(0.0, 1.0) };
    ((px - a.0 - t * dx).powi(2) + (py - a.1 - t * dy).powi(2)).sqrt()
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
        if gw * gh > 800_000 {
            return Err("the grid is over 800,000 points a layer: widen the grid or shrink the board");
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
            via_fixed: vec![FREE; n / 2], near: vec![0; n / 2], near_own: vec![0; n / 2],
            rt: (((p.track + p.clearance) / p.pitch - eps).ceil() as i32 - 1).max(0),
            rv: (((p.via / 2.0 + p.clearance + p.track / 2.0) / p.pitch - eps).ceil() as i32 - 1).max(0),
            strategy: Strategy::AStar, queue: VecDeque::new(), cur: 0, phase: Phase::Done, ripping: false,
            round: 0, present: 0.5, history: vec![0.0; n],
            sid: 0, g: vec![0.0; n], seen: vec![0; n], closed: vec![0; n], parent: vec![NONE; n], target: vec![0; n],
            heap: BinaryHeap::new(),
            g2: vec![0.0; n], seen2: vec![0; n], closed2: vec![0; n], parent2: vec![NONE; n], heap2: BinaryHeap::new(),
            meet: (f32::INFINITY, NONE, NONE), tbox: (0, 0, 0, 0), mark: vec![0; n], mark_id: 0,
            expansions: 0, total_rips: 0, last_path: Vec::new(),
            diagonal: false, mv: None, temp: HOT, alpha: 1.0, moves: 0, max_moves: 0, accepted: 0, rng: 0x9E3779B97F4A7C15,
        };
        // the edge: a track's centre keeps half its width and the edge clearance inside the outline
        let keep = p.edge + p.track / 2.0 - eps;
        // outside it, row by row: between the outline's crossings of the row, a point is inside
        for y in 0..gh {
            let py = y as f32 * p.pitch + 1e-5;
            let mut xs: Vec<f32> = (0..outline.len())
                .filter_map(|i| {
                    let (a, b) = (outline[i], outline[(i + 1) % outline.len()]);
                    ((a.1 > py) != (b.1 > py)).then(|| a.0 + (py - a.1) * (b.0 - a.0) / (b.1 - a.1))
                })
                .collect();
            xs.sort_by(f32::total_cmp);
            for x in 0..gw {
                let px = x as f32 * p.pitch;
                if xs.iter().filter(|&&c| c < px).count() % 2 == 0 {
                    r.fixed[y * gw + x] = WALL;
                    r.fixed[(gh + y) * gw + x] = WALL;
                }
            }
        }
        // and too near it: the points within the margin of each of its edges
        for i in 0..outline.len() {
            let (a, b) = (outline[i], outline[(i + 1) % outline.len()]);
            let lo = |u: f32, v: f32| ((u.min(v) - keep) / p.pitch).floor().max(0.0) as usize;
            let hi = |u: f32, v: f32, max: usize| (((u.max(v) + keep) / p.pitch).ceil().max(0.0) as usize).min(max - 1);
            for y in lo(a.1, b.1)..=hi(a.1, b.1, gh) {
                for x in lo(a.0, b.0)..=hi(a.0, b.0, gw) {
                    if point_segment(x as f32 * p.pitch, y as f32 * p.pitch, a, b) < keep {
                        r.fixed[y * gw + x] = WALL;
                        r.fixed[(gh + y) * gw + x] = WALL;
                    }
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
        // what the pads leave of each place for a via: nothing, one net's own, or no via at all
        for c in 0..n {
            let f = r.fixed[c];
            if f == FREE {
                continue;
            }
            let (x, y, _) = r.xy(c as u32);
            for dy in -r.rv..=r.rv {
                for dx in -r.rv..=r.rv {
                    if let Some(at) = r.at(x + dx, y + dy, 0) {
                        let v = &mut r.via_fixed[at];
                        *v = if *v == FREE || *v == f { f } else { WALL };
                    }
                }
            }
        }
        // a place too near the board's edge for a via's halo has no via either
        for y in 0..gh as i32 {
            for x in 0..gw as i32 {
                if x < r.rv || y < r.rv || x >= gw as i32 - r.rv || y >= gh as i32 - r.rv {
                    r.via_fixed[y as usize * gw + x as usize] = WALL;
                }
            }
        }
        for net in 0..nets {
            let pads: Vec<usize> = (0..p.pads.len()).filter(|&i| p.pads[i].net == net as i32).collect();
            r.nets.push(Net { connected: vec![false; pads.len()], pads, centres: Vec::new(), vias: Vec::new(),
                              segs: Vec::new(), halo: Vec::new(), routed: false, failed: false, rips: 0 });
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
        self.ripping = false;
        self.mv = None;
        (self.temp, self.alpha, self.moves, self.max_moves, self.accepted) = (HOT, 1.0, 0, 0, 0);
        self.rng = 0x9E3779B97F4A7C15;   // the same moves every time: a run can be watched again
    }

    /// A number from 0 up to 1, the next of a fixed sequence.
    fn random(&mut self) -> f32 {
        self.rng ^= self.rng << 13;
        self.rng ^= self.rng >> 7;
        self.rng ^= self.rng << 17;
        (self.rng >> 40) as f32 / (1u64 << 24) as f32
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
        for k in 0..self.nets[i].halo.len() {
            let c = self.nets[i].halo[k];
            self.usage[c as usize] -= 1;
            self.around(c, |r, at| r.near[at] -= 1);
        }
        let net = &mut self.nets[i];
        for &c in &net.centres {
            if self.centre[c as usize] == i as i16 {
                self.centre[c as usize] = FREE;
            }
        }
        net.halo.clear();
        net.centres.clear();
        net.vias.clear();
        net.segs.clear();
        net.routed = false;
        net.connected.iter_mut().for_each(|c| *c = false);
    }

    /// Calls `f` with each place within a via's halo of a point.
    fn around(&mut self, c: u32, f: impl Fn(&mut Router, usize)) {
        let (x, y, _) = self.xy(c);
        for dy in -self.rv..=self.rv {
            for dx in -self.rv..=self.rv {
                if let Some(at) = self.at(x + dx, y + dy, 0) {
                    f(self, at);
                }
            }
        }
    }

    /// Keeps the points within `r` of (x, y) on layer `l` for the net now being routed.
    fn keep(&mut self, x: i32, y: i32, l: usize, r: i32) {
        for dy in -r..=r {
            for dx in -r..=r {
                if let Some(c) = self.at(x + dx, y + dy, l) {
                    self.usage[c] += 1;
                    self.own[c] += 1;
                    self.nets[self.cur].halo.push(c as u32);
                    self.around(c as u32, |r, at| {
                        r.near[at] += 1;
                        r.near_own[at] += 1;
                    });
                }
            }
        }
    }

    /// A net's routing as it is now.
    fn snapshot(&self, i: usize) -> Saved {
        let n = &self.nets[i];
        Saved { net: i, centres: n.centres.clone(), vias: n.vias.clone(), segs: n.segs.clone(), halo: n.halo.clone(),
                connected: n.connected.clone(), routed: n.routed, failed: n.failed }
    }

    /// Puts a net's routing back as it was saved. The net has been taken up first.
    fn restore(&mut self, s: Saved) {
        for &c in &s.halo {
            self.usage[c as usize] += 1;
            self.around(c, |r, at| r.near[at] += 1);
        }
        for &c in &s.centres {
            if self.pad_net[c as usize] == FREE {
                self.centre[c as usize] = s.net as i16;
            }
        }
        let n = &mut self.nets[s.net];
        (n.centres, n.vias, n.segs, n.halo, n.connected, n.routed, n.failed) =
            (s.centres, s.vias, s.segs, s.halo, s.connected, s.routed, s.failed);
    }

    /// How long a net's tracks are, in steps.
    fn length(&self, i: usize) -> f32 {
        self.nets[i].segs.iter().map(|&(a, b)| {
            let ((ax, ay, _), (bx, by, _)) = (self.xy(a), self.xy(b));
            if ax != bx && ay != by { DIAGONAL } else { 1.0 }
        }).sum()
    }

    /// What the board costs the annealing: its tracks' length, its vias, and a great deal for
    /// each net that is not whole.
    fn cost(&self) -> f32 {
        (0..self.nets.len()).filter(|&i| self.nets[i].pads.len() > 1).map(|i| {
            let n = &self.nets[i];
            self.length(i) + VIA_COST * n.vias.len() as f32 + if n.routed && !n.failed { 0.0 } else { UNROUTED }
        }).sum()
    }

    /// The two points a diagonal step passes between, or nothing for a step that is not diagonal.
    fn beside(&self, a: u32, b: u32) -> Option<(usize, usize)> {
        let ((ax, ay, l), (bx, by, lb)) = (self.xy(a), self.xy(b));
        (l == lb && ax != bx && ay != by).then(|| (self.at(bx, ay, l).unwrap(), self.at(ax, by, l).unwrap()))
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
        let at = y as usize * self.gw + x as usize;
        let f = self.via_fixed[at];
        if f == WALL || (f >= 0 && f as usize != self.cur) {
            return None;
        }
        // what other nets keep within the via's halo, on both layers, each time it is kept
        let others = (self.near[at] - self.near_own[at]) as f32;
        match self.strategy {
            Strategy::Negotiated => Some(VIA_COST + self.present * others.min(40.0)),
            _ if others == 0.0 => Some(VIA_COST),
            _ if self.ripping => Some(VIA_COST + RIP_COST * others.min(8.0)),
            _ => None,
        }
    }

    /// How far a point is from the pads the search is for, in steps, as the crow walks.
    fn distance(&self, c: u32) -> f32 {
        let (x, y, _) = self.xy(c);
        let (x0, y0, x1, y1) = self.tbox;
        let (dx, dy) = ((x0 - x).max(x - x1).max(0) as f32, (y0 - y).max(y - y1).max(0) as f32);
        if self.diagonal { dx.max(dy) + (DIAGONAL - 1.0) * dx.min(dy) } else { dx + dy }
    }

    /// What the search adds to a point's cost to order the points it has open.
    fn heuristic(&self, c: u32) -> f32 {
        match self.strategy {
            Strategy::Lee | Strategy::Bidirectional => 0.0,
            // Hadlock's order is the detours alone; of two points with as many, the nearer first
            Strategy::Hadlock => self.distance(c) * 1e-4,
            _ => self.distance(c),
        }
    }

    /// What a step costs by the strategy's own measure. Hadlock counts detours: how much further
    /// a step goes than it brings the pads nearer, so that a step straight at them is free and a
    /// step straight away costs two. A via is as dear as half its length in steps.
    fn price(&self, from: u32, to: usize, cost: f32) -> f32 {
        if self.strategy != Strategy::Hadlock || cost == 0.0 {
            return cost;
        }
        let per = self.gw * self.gh;
        if from as usize / per != to / per {
            1.0 + VIA_COST / 2.0
        } else {
            (cost + self.distance(to as u32) - self.distance(from)).max(0.0)
        }
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
        self.heap2.clear();
        self.meet = (f32::INFINITY, NONE, NONE);
        if self.strategy == Strategy::Bidirectional {
            for &c in &targets {
                self.g2[c as usize] = 0.0;
                self.seen2[c as usize] = sid;
                self.parent2[c as usize] = NONE;
                self.heap2.push(Open(0.0, c));
            }
        }
        self.phase = Phase::Searching;
    }

    fn relax(&mut self, from: u32, to: usize, cost: f32) {
        let g = self.g[from as usize] + self.price(from, to, cost);
        if self.closed[to] != self.sid && (self.seen[to] != self.sid || g < self.g[to]) {
            self.g[to] = g;
            self.seen[to] = self.sid;
            self.parent[to] = from;
            let f = g + self.heuristic(to as u32);
            self.heap.push(Open(f, to as u32));
        }
    }

    /// The steps from a point: each point a track may go on to, or the far layer, and its cost.
    fn steps(&self, c: u32) -> Vec<(usize, f32)> {
        let (x, y, l) = self.xy(c);
        let mut out = Vec::with_capacity(9);
        for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
            if let Some(to) = self.at(x + dx, y + dy, l) {
                if let Some(cost) = self.enter(to) {
                    out.push((to, cost));
                }
            }
        }
        if self.diagonal {
            // a diagonal step passes between two points: both must be free to the net, and what
            // they cost beyond a plain point is paid too
            for (dx, dy) in [(1, 1), (1, -1), (-1, 1), (-1, -1)] {
                let Some(to) = self.at(x + dx, y + dy, l) else { continue };
                let (a, b) = (self.at(x + dx, y, l).unwrap(), self.at(x, y + dy, l).unwrap());
                if let (Some(cost), Some(ca), Some(cb)) = (self.enter(to), self.enter(a), self.enter(b)) {
                    out.push((to, DIAGONAL * cost + (ca - 1.0).max(0.0) + (cb - 1.0).max(0.0)));
                }
            }
        }
        let to = self.at(x, y, 1 - l).unwrap();
        let me = self.cur as i16;
        if self.pad_net[c as usize] == me && self.pad_net[to] == me {
            out.push((to, 0.0)); // a through-hole pad of the net's own is a way through for nothing
        } else if self.closed[to] != self.sid || self.strategy == Strategy::Bidirectional {
            if let (Some(step), Some(via)) = (self.enter(to), self.via(x, y)) {
                out.push((to, step + via));
            }
        }
        out
    }

    /// One expansion of the bidirectional search: of the wave that is behind. A step costs the
    /// same either way, so the two waves' costs add where they meet, and the search is over when
    /// no way through points still open could be cheaper than the best meeting found.
    fn expand_both(&mut self) -> bool {
        let (a, b) = (self.heap.peek().map(|o| o.0), self.heap2.peek().map(|o| o.0));
        let (Some(a), Some(b)) = (a, b) else {
            return self.met();
        };
        if a + b >= self.meet.0 {
            return self.met();
        }
        let sid = self.sid;
        if a <= b {
            let c = self.heap.pop().unwrap().1;
            if self.closed[c as usize] == sid {
                return false;
            }
            self.closed[c as usize] = sid;
            self.expansions += 1;
            for (to, cost) in self.steps(c) {
                let g = self.g[c as usize] + cost;
                if self.closed[to] != sid && (self.seen[to] != sid || g < self.g[to]) {
                    self.g[to] = g;
                    self.seen[to] = sid;
                    self.parent[to] = c;
                    self.heap.push(Open(g, to as u32));
                }
                if self.seen2[to] == sid && g + self.g2[to] < self.meet.0 {
                    self.meet = (g + self.g2[to], c, to as u32);
                }
            }
        } else {
            let c = self.heap2.pop().unwrap().1;
            if self.closed2[c as usize] == sid {
                return false;
            }
            self.closed2[c as usize] = sid;
            self.expansions += 1;
            for (to, cost) in self.steps(c) {
                let g = self.g2[c as usize] + cost;
                if self.closed2[to] != sid && (self.seen2[to] != sid || g < self.g2[to]) {
                    self.g2[to] = g;
                    self.seen2[to] = sid;
                    self.parent2[to] = c;
                    self.heap2.push(Open(g, to as u32));
                }
                if self.seen[to] == sid && g + self.g[to] < self.meet.0 {
                    self.meet = (g + self.g[to], to as u32, c);
                }
            }
        }
        false
    }

    /// The two waves have met, or one has run out: the way through their meeting is laid.
    fn met(&mut self) -> bool {
        let (cost, near, far) = self.meet;
        if cost.is_infinite() {
            self.dead_end();
            return true;
        }
        let mut path = vec![far];
        while self.parent2[*path.last().unwrap() as usize] != NONE {
            path.push(self.parent2[*path.last().unwrap() as usize]);
        }
        path.reverse(); // from the pad reached to the meeting
        path.push(near);
        while self.parent[*path.last().unwrap() as usize] != NONE {
            path.push(self.parent[*path.last().unwrap() as usize]);
        }
        self.lay(path);
        true
    }

    /// One expansion of the search. True when the search is over, with a path or without.
    fn expand(&mut self) -> bool {
        if self.strategy == Strategy::Bidirectional {
            return self.expand_both();
        }
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
        for (to, cost) in self.steps(c) {
            self.relax(c, to, cost);
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

    /// The search has reached a pad: the way back from it is the path.
    fn arrive(&mut self, end: u32) {
        let mut path = vec![end];
        while self.parent[*path.last().unwrap() as usize] != NONE {
            path.push(self.parent[*path.last().unwrap() as usize]);
        }
        self.lay(path);
    }

    /// A path from a pad reached back to the net's copper is laid, and what it runs through is
    /// taken up.
    fn lay(&mut self, path: Vec<u32>) {
        let end = path[0];
        let me = self.cur as i16;
        let mut vias = Vec::new();
        for w in path.windows(2) {
            let ((x, y, l0), (_, _, l1)) = (self.xy(w[0]), self.xy(w[1]));
            if l0 != l1 && !(self.pad_net[w[0] as usize] == me && self.pad_net[w[1] as usize] == me) {
                vias.push((x, y));
            }
        }
        // a diagonal step keeps the two points it passes between as well as its ends
        let beside: Vec<u32> = path.windows(2).filter_map(|w| self.beside(w[0], w[1]))
            .flat_map(|(a, b)| [a as u32, b as u32]).collect();
        if self.ripping {
            // every net that keeps a point the path needs is in its way
            self.mark_id += 1;
            for &c in path.iter().chain(&beside) {
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
            if self.strategy == Strategy::Anneal {
                // the nets in the way are taken up, as they were kept, to be laid again after
                // this one; the search goes on through other nets until this net is whole
                let mut mv = self.mv.take().expect("an annealing move is in hand while it routes through nets");
                for &i in &blockers {
                    if !mv.saved.iter().any(|s| s.net == i) {
                        mv.saved.push(self.snapshot(i));
                    }
                    if !mv.todo.contains(&i) {
                        mv.todo.push(i);
                    }
                    self.rip(i);
                    self.total_rips += 1;
                }
                self.mv = Some(mv);
            } else {
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
        }
        for &c in &path {
            let (x, y, l) = self.xy(c);
            self.keep(x, y, l, self.rt);
            if self.pad_net[c as usize] == FREE {
                self.centre[c as usize] = me;
            }
            self.nets[self.cur].centres.push(c);
        }
        for &c in &beside {
            let (x, y, l) = self.xy(c);
            self.keep(x, y, l, self.rt);
        }
        for w in path.windows(2) {
            if self.xy(w[0]).2 == self.xy(w[1]).2 {
                self.nets[self.cur].segs.push((w[0], w[1]));
            }
        }
        for &(x, y) in &vias {
            self.keep(x, y, 0, self.rv);
            self.keep(x, y, 1, self.rv);
            let c = self.at(x, y, 0).unwrap() as u32;
            self.nets[self.cur].vias.push(c);
        }
        // every pad of the net that has the point reached is reached: pads of one net may overlap
        // (a tab and its pin, a hole in a land), and the point is one pad's by name alone
        let mut reached = false;
        for k in 0..self.nets[self.cur].pads.len() {
            let pad = self.nets[self.cur].pads[k];
            if !self.nets[self.cur].connected[k] && self.pad_cells[pad].contains(&end) {
                self.nets[self.cur].connected[k] = true;
                reached = true;
            }
        }
        self.last_path = path;
        if !reached {
            // no pad left has the point: the search would find it again for ever
            self.nets[self.cur].failed = true;
            self.finish_net();
            return;
        }
        if self.nets[self.cur].connected.iter().all(|&c| c) {
            self.nets[self.cur].routed = true;
            self.finish_net();
        } else {
            self.phase = Phase::Begin;
        }
    }

    fn finish_net(&mut self) {
        for i in 0..self.nets[self.cur].halo.len() {
            let c = self.nets[self.cur].halo[i];
            self.own[c as usize] = 0;
            self.around(c, |r, at| r.near_own[at] = 0);
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
        if self.strategy == Strategy::Anneal {
            self.anneal();
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

    /// The annealing, between searches: the next net of the move in hand, or the move judged and
    /// the next one begun.
    fn anneal(&mut self) {
        let unrouted = |r: &Router| -> Vec<usize> {
            (0..r.nets.len()).filter(|&i| r.nets[i].pads.len() > 1 && (r.nets[i].failed || !r.nets[i].routed)).collect()
        };
        if let Some(mv) = self.mv.as_mut() {
            if let Some(i) = mv.todo.pop() {
                // a net the move took up is laid again: the first few through what is in their
                // way, the rest round what is there now
                mv.relaid += 1;
                let through = mv.relaid <= RIPPLE;
                self.cur = i;
                self.ripping = through;
                self.nets[i].failed = false;
                self.nets[i].connected[0] = true;
                self.phase = Phase::Begin;
                return;
            }
            // the move is whole: kept if the board is no worse for it, or by chance while it is hot
            let mv = self.mv.take().unwrap();
            let worse = self.cost() - mv.before;
            if worse <= 0.0 || self.random() < (-worse / self.temp).exp() {
                self.accepted += 1;
            } else {
                for s in &mv.saved {
                    self.rip(s.net);
                }
                for s in mv.saved {
                    self.restore(s);
                }
            }
            self.temp = (self.temp * self.alpha).max(COLD * 0.1);
            self.moves += 1;
        } else {
            // the first pass is over: the cooling is set by how much is left to do
            self.max_moves = 30 * unrouted(self).len() as u32 + 40;
            self.alpha = (COLD / HOT).powf(1.0 / (0.7 * self.max_moves as f32));
        }
        self.ripping = false;
        let left = unrouted(self);
        if left.is_empty() || self.moves >= self.max_moves {
            self.phase = Phase::Done;
            return;
        }
        // a move: one of the nets left, routed through whatever is in its way
        let i = left[((self.random() * left.len() as f32) as usize).min(left.len() - 1)];
        self.mv = Some(Move { saved: vec![self.snapshot(i)], todo: Vec::new(), before: self.cost(), relaid: 0 });
        self.rip(i);
        self.cur = i;
        self.nets[i].failed = false;
        self.nets[i].connected[0] = true;
        self.ripping = true;
        self.phase = Phase::Begin;
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

    /// How many pads of a net of two or more have no way out on this grid: their points, and what
    /// their net may step to from them, are a dozen points or fewer, hemmed in by other pads'
    /// halos. A finer grid, or less clearance, lets them out.
    pub fn hemmed(&mut self) -> usize {
        let mut count = 0;
        for i in 0..self.nets.len() {
            if self.nets[i].pads.len() < 2 {
                continue;
            }
            for k in 0..self.nets[i].pads.len() {
                let pad = self.nets[i].pads[k];
                self.mark_id += 1;
                let mut reach: Vec<u32> = self.pad_cells[pad].clone();
                for &c in &reach {
                    self.mark[c as usize] = self.mark_id;
                }
                let (mut at, limit) = (0, self.pad_cells[pad].len() + 12);
                while at < reach.len() && reach.len() <= limit {
                    let (x, y, l) = self.xy(reach[at]);
                    at += 1;
                    for (dx, dy) in [(1, 0), (-1, 0), (0, 1), (0, -1)] {
                        if let Some(to) = self.at(x + dx, y + dy, l) {
                            let f = self.fixed[to];
                            if self.mark[to] != self.mark_id && (f == FREE || f == i as i16) {
                                self.mark[to] = self.mark_id;
                                reach.push(to as u32);
                            }
                        }
                    }
                }
                count += (reach.len() <= limit) as usize;
            }
        }
        count
    }

    /// The nets of two pads or more that are not whole, and of each, how many of its pads the
    /// routing has reached.
    pub fn unrouted(&self) -> Vec<(usize, usize, usize)> {
        (0..self.nets.len())
            .filter(|&i| self.nets[i].pads.len() > 1 && (self.nets[i].failed || !self.nets[i].routed))
            .map(|i| (i, self.nets[i].connected.iter().filter(|&&c| c).count(), self.nets[i].pads.len()))
            .collect()
    }

    pub fn done(&self) -> bool {
        self.phase == Phase::Done
    }

    /// What there is to say of the routing so far: see `ffi::stats` for the order.
    pub fn stats(&mut self) -> [i32; 14] {
        let shared = if self.strategy == Strategy::Negotiated { self.shared().len() } else { 0 };
        let wired = self.nets.iter().filter(|n| n.pads.len() > 1);
        [
            self.done() as i32,
            if self.strategy == Strategy::Anneal { self.moves as i32 } else { self.round as i32 },
            wired.clone().count() as i32,
            wired.clone().filter(|n| n.routed).count() as i32,
            wired.filter(|n| n.failed).count() as i32,
            self.expansions.min(i32::MAX as u64) as i32,
            ((0..self.nets.len()).map(|i| self.length(i)).sum::<f32>() * self.pitch * 100.0) as i32,
            self.nets.iter().map(|n| n.vias.len()).sum::<usize>() as i32,
            shared as i32,
            if self.phase == Phase::Searching || self.phase == Phase::Begin { self.cur as i32 } else { -1 },
            self.total_rips as i32,
            self.ripping as i32,
            (self.temp * 10.0) as i32,
            self.accepted as i32,
        ]
    }

    /// The board as a page draws it: by point, the net whose copper is there (a track's, else a
    /// pad's), FREE or WALL; and flags, bit 0 a pad's copper, bit 1 a track through what another
    /// net keeps, bit 2 a point the search has open, bit 3 one it has closed, bit 4 a via, bit 5
    /// the path laid last, bit 6 a point closed by the wave from the pads. And by point, the
    /// tracks that leave it: bit 0 to the east, 1 to the north, 2 to the north-east, 3 to the
    /// north-west (a track is drawn from one of its ends only).
    pub fn paint(&mut self, net: &mut [i16], flags: &mut [u8], links: &mut [u8]) {
        links.iter_mut().for_each(|l| *l = 0);
        for n in &self.nets {
            for &(a, b) in &n.segs {
                let ((ax, ay, _), (bx, by, _)) = (self.xy(a), self.xy(b));
                // from the lower end, or the western of two on a row
                let (from, dx) = if by > ay || (by == ay && bx > ax) { (a, bx - ax) } else { (b, ax - bx) };
                links[from as usize] |= if ay == by { 1 } else if dx == 0 { 2 } else if dx > 0 { 4 } else { 8 };
            }
        }
        let live = self.phase == Phase::Searching;
        for c in 0..net.len() {
            net[c] = if self.pad_net[c] != FREE { self.pad_net[c] } else if self.centre[c] != FREE { self.centre[c] }
                     else if self.fixed[c] == WALL { WALL } else { FREE };
            flags[c] = (self.pad_net[c] != FREE) as u8
                | if live && self.closed[c] == self.sid { 8 }
                  else if live && self.closed2[c] == self.sid { 64 }
                  else if live && (self.seen[c] == self.sid || self.seen2[c] == self.sid) { 4 }
                  else { 0 };
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
        solve_with(p, s, false)
    }

    fn solve_with(p: &Problem, s: Strategy, diagonal: bool) -> Router {
        let mut r = Router::new(p).unwrap();
        r.diagonal = diagonal;
        r.start(s, Order::AsGiven, &p.pads);
        let mut steps = 0;
        while !r.step(10_000) {
            steps += 1;
            assert!(steps < 10_000, "the router does not end");
        }
        r
    }

    const ALL: [Strategy; 7] = [Strategy::Lee, Strategy::AStar, Strategy::RipUp, Strategy::Negotiated, Strategy::Hadlock,
                                Strategy::Bidirectional, Strategy::Anneal];

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
        for s in ALL {
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

    /// One net across an empty board, on one layer: nothing to go round, so every search that
    /// finds a shortest way finds one of the same length, and they differ in how far they look.
    fn open_field() -> Problem {
        board(vec![pad(3.0, 3.0, 0, Side::Top), pad(21.0, 12.0, 0, Side::Top)], 24.0, 15.0)
    }

    #[test]
    fn the_searches_find_ways_as_short_and_look_less_far_than_lee() {
        let mut lee = solve(&open_field(), Strategy::Lee);
        let length = lee.stats()[6];
        for s in [Strategy::AStar, Strategy::Hadlock, Strategy::Bidirectional] {
            let mut r = solve(&open_field(), s);
            assert!(r.sound());
            assert_eq!(r.stats()[6], length, "{s:?} finds a longer way than Lee");
            assert_eq!(r.stats()[7], 0, "{s:?} takes a via across an empty board");
            assert!(r.expansions < lee.expansions, "{s:?} looks as far as Lee: {} against {}", r.expansions, lee.expansions);
        }
    }

    #[test]
    fn hadlock_with_nothing_in_the_way_looks_no_further_than_the_way_is_long() {
        let mut r = solve(&open_field(), Strategy::Hadlock);
        let points = r.stats()[6] as f32 / 100.0 / 0.3;
        assert!((r.expansions as f32) < 2.0 * points + 40.0, "{} expansions for a way of {points} points", r.expansions);
    }

    #[test]
    fn on_a_crowded_board_the_searches_end_and_what_they_lay_is_clean() {
        // which nets a search that takes nothing up gets through depends on the ways it happens
        // to pick, so the count is not compared: every net is routed or given up, and no track
        // runs through what another net keeps
        for s in [Strategy::Lee, Strategy::AStar, Strategy::Hadlock, Strategy::Bidirectional] {
            let mut r = solve(&reversed(), s);
            let stats = r.stats();
            assert_eq!(stats[3] + stats[4], stats[2], "{s:?} leaves a net neither routed nor given up");
            assert!(stats[3] >= 4, "{s:?} routes only {} of the 8", stats[3]);
            assert!(r.shared().is_empty(), "{s:?} lays a track through another net's");
        }
    }

    #[test]
    fn the_reversed_bus_is_routed_by_the_strategies_that_take_nets_up() {
        for s in [Strategy::RipUp, Strategy::Negotiated, Strategy::Anneal] {
            let mut r = solve(&reversed(), s);
            assert!(r.sound(), "{s:?} leaves the reversed bus unrouted or shared: {:?}", r.stats());
        }
    }

    #[test]
    fn with_diagonal_steps_every_strategy_is_still_clean_and_the_way_is_shorter() {
        for s in ALL {
            let mut r = solve_with(&crossing(), s, true);
            assert!(r.sound(), "{s:?} with diagonals leaves the crossing unrouted or shared");
        }
        for s in [Strategy::RipUp, Strategy::Negotiated, Strategy::Anneal] {
            let mut r = solve_with(&reversed(), s, true);
            assert!(r.sound(), "{s:?} with diagonals leaves the reversed bus unrouted or shared: {:?}", r.stats());
        }
        // across an empty board a diagonal way is shorter than a square one, and every search finds one as short
        let square = solve(&open_field(), Strategy::Lee).stats()[6];
        let slant = solve_with(&open_field(), Strategy::Lee, true).stats()[6];
        assert!(slant < square, "a diagonal way of {slant} is no shorter than a square one of {square}");
        for s in [Strategy::AStar, Strategy::Hadlock, Strategy::Bidirectional] {
            let got = solve_with(&open_field(), s, true).stats()[6];
            assert!((got - slant).abs() <= 1, "{s:?} with diagonals finds a way of {got}, and Lee one of {slant}");
        }
    }

    #[test]
    fn a_diagonal_track_keeps_the_points_it_passes_between() {
        // one net laid diagonally across the board, then a second that must cross it: it may not
        // slip between two of the first's points, so it changes layer or goes round
        let p = board(vec![pad(3.0, 3.0, 0, Side::Top), pad(9.0, 9.0, 0, Side::Top),
                           pad(3.0, 9.0, 1, Side::Top), pad(9.0, 3.0, 1, Side::Top)], 12.0, 12.0);
        let mut r = solve_with(&p, Strategy::AStar, true);
        assert!(r.sound());
        let mut links = vec![0u8; 2 * r.gw * r.gh];
        let (mut net, mut flags) = (vec![0i16; links.len()], vec![0u8; links.len()]);
        r.paint(&mut net, &mut flags, &mut links);
        // no north-east piece of one net crosses a north-west piece of another in the same square
        let (gw, gh) = (r.gw, r.gh);
        for l in 0..2 {
            for y in 0..gh - 1 {
                for x in 0..gw - 1 {
                    let (sw, se) = ((l * gh + y) * gw + x, (l * gh + y) * gw + x + 1);
                    assert!(!(links[sw] & 4 != 0 && links[se] & 8 != 0), "two diagonal tracks cross at ({x}, {y})");
                }
            }
        }
    }

    #[test]
    fn pads_of_one_net_that_overlap_are_reached_together() {
        // a land with a hole in it, as two pads, and a third pad of the net across the board
        let mut pads = vec![pad(3.0, 3.0, 0, Side::Top), pad(3.0, 3.0, 0, Side::Through), pad(9.0, 9.0, 0, Side::Top)];
        pads.push(pad(9.0, 3.0, 1, Side::Top));
        pads.push(pad(3.0, 9.0, 1, Side::Top));
        for s in [Strategy::AStar, Strategy::Bidirectional, Strategy::Negotiated] {
            let mut r = solve(&board(pads.clone(), 12.0, 12.0), s);
            assert!(r.sound(), "{s:?}: {:?}", r.stats());
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
