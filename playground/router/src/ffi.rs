//! The C ABI the page calls: one board at a time, kept here between calls.
//!
//! A board goes in as a run of 32-bit floats written into memory this module hands out
//! (`buffer`): width, height, pitch, track width, clearance, via diameter, edge clearance; the
//! number of the outline's corners and their x and y; the number of pads, and for each its x, y,
//! width, height, side (0 top, 1 bottom, 2 through), 1 if round, and its net (-1 for none).
//! `load` builds the grid, `start` picks a strategy, `step` advances it, and `paint` fills the two
//! arrays a page draws from, whose addresses `nets` and `flags` give.

use crate::{Order, Pad, Problem, Router, Side, Strategy};
use std::cell::RefCell;

#[derive(Default)]
struct Held {
    input: Vec<f32>,
    pads: Vec<Pad>,
    router: Option<Router>,
    nets: Vec<i16>,
    flags: Vec<u8>,
    stats: [i32; 12],
    error: Vec<u8>,
}

thread_local! {
    static HELD: RefCell<Held> = RefCell::new(Held::default());
}

/// Memory for a board of `len` floats, to be written and then given to `load`.
#[no_mangle]
pub extern "C" fn buffer(len: usize) -> *mut f32 {
    HELD.with(|h| {
        let mut h = h.borrow_mut();
        h.input = vec![0.0; len];
        h.input.as_mut_ptr()
    })
}

fn read(v: &[f32]) -> Option<Problem> {
    let mut at = 0;
    let mut next = || {
        at += 1;
        v.get(at - 1).copied()
    };
    let (width, height, pitch, track, clearance, via, edge) = (next()?, next()?, next()?, next()?, next()?, next()?, next()?);
    let mut outline = Vec::new();
    for _ in 0..next()? as usize {
        outline.push((next()?, next()?));
    }
    let mut pads = Vec::new();
    for _ in 0..next()? as usize {
        let (x, y, w, h) = (next()?, next()?, next()?, next()?);
        let side = match next()? as i32 { 0 => Side::Top, 1 => Side::Bottom, _ => Side::Through };
        pads.push(Pad { x, y, w, h, side, round: next()? != 0.0, net: next()? as i32 });
    }
    Some(Problem { width, height, pitch, track, clearance, via, edge, outline, pads })
}

/// Builds the grid of the board written to `buffer`. 1, or 0 with a reason for `error`.
#[no_mangle]
pub extern "C" fn load() -> i32 {
    HELD.with(|h| {
        let mut h = h.borrow_mut();
        let made = read(&h.input).ok_or("the board's numbers end early").and_then(|p| Router::new(&p).map(|r| (r, p.pads)));
        match made {
            Ok((router, pads)) => {
                let n = 2 * router.gw * router.gh;
                h.nets = vec![-1; n];
                h.flags = vec![0; n];
                h.router = Some(router);
                h.pads = pads;
                1
            }
            Err(why) => {
                h.router = None;
                h.error = why.as_bytes().to_vec();
                0
            }
        }
    })
}

/// Begins routing: strategy 0 Lee, 1 A*, 2 rip-up and reroute, 3 negotiated congestion, 4 Hadlock,
/// 5 bidirectional; order 0 as given, 1 the shortest net first, 2 the longest.
#[no_mangle]
pub extern "C" fn start(strategy: u32, order: u32) {
    HELD.with(|h| {
        let h = &mut *h.borrow_mut();
        if let Some(r) = h.router.as_mut() {
            let s = [Strategy::Lee, Strategy::AStar, Strategy::RipUp, Strategy::Negotiated, Strategy::Hadlock,
                     Strategy::Bidirectional][strategy.min(5) as usize];
            let o = [Order::AsGiven, Order::ShortestFirst, Order::LongestFirst][order.min(2) as usize];
            r.start(s, o, &h.pads);
        }
    })
}

/// Advances the routing by up to `budget` expansions of the search. 1 when it is over.
#[no_mangle]
pub extern "C" fn step(budget: u32) -> i32 {
    HELD.with(|h| h.borrow_mut().router.as_mut().map_or(1, |r| r.step(budget) as i32))
}

/// Fills the arrays `nets` and `flags` point at, and the numbers `stats` points at.
#[no_mangle]
pub extern "C" fn paint() {
    HELD.with(|h| {
        let h = &mut *h.borrow_mut();
        if let Some(r) = h.router.as_mut() {
            r.paint(&mut h.nets, &mut h.flags);
            h.stats = r.stats();
        }
    })
}

/// By point, layer by layer and row by row from the bottom: the net whose copper is there, -1
/// for none, -2 where no track may go.
#[no_mangle]
pub extern "C" fn nets() -> *const i16 {
    HELD.with(|h| h.borrow().nets.as_ptr())
}

/// By point: bit 0 a pad, 1 a track through what another net keeps, 2 open to the search, 3
/// closed by it, 4 a via, 5 the path laid last, 6 closed by the wave from the pads.
#[no_mangle]
pub extern "C" fn flags() -> *const u8 {
    HELD.with(|h| h.borrow().flags.as_ptr())
}

/// Twelve numbers: 1 when over; the round; the nets of two pads or more; those routed; those
/// given up; the search's expansions; the tracks' length in hundredths of a mm; the vias; the
/// points still shared; the net being routed, or -1; the times a net was taken up; 1 while the
/// search is routing through other nets.
#[no_mangle]
pub extern "C" fn stats() -> *const i32 {
    HELD.with(|h| h.borrow().stats.as_ptr())
}

/// How many pads have no way out on this grid, hemmed in by their neighbours' halos.
#[no_mangle]
pub extern "C" fn hemmed() -> usize {
    HELD.with(|h| h.borrow_mut().router.as_mut().map_or(0, |r| r.hemmed()))
}

#[no_mangle]
pub extern "C" fn grid_width() -> usize {
    HELD.with(|h| h.borrow().router.as_ref().map_or(0, |r| r.gw))
}

#[no_mangle]
pub extern "C" fn grid_height() -> usize {
    HELD.with(|h| h.borrow().router.as_ref().map_or(0, |r| r.gh))
}

/// Why the last `load` failed, as UTF-8: its address and its length.
#[no_mangle]
pub extern "C" fn error() -> *const u8 {
    HELD.with(|h| h.borrow().error.as_ptr())
}

#[no_mangle]
pub extern "C" fn error_length() -> usize {
    HELD.with(|h| h.borrow().error.len())
}
