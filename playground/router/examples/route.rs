//! Routes a board from the command line, with no page: for timing, and for finding faults with
//! a debugger's help.
//!
//!     python3 playground/boards/floats.py playground/boards/corne-keyboard.json /tmp/corne.f32
//!     cargo run --release --example route -- /tmp/corne.f32 6 1 [seconds]
//!
//! The arguments are the board as the page would write it (32-bit floats, little-endian), the
//! strategy's number, 1 for diagonal steps, and how long to go on for.

use pcb_router_playground::{ffi, Order, Router, Strategy};
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let bytes = std::fs::read(&args[1]).expect("the board's file");
    let floats: Vec<f32> = bytes.chunks_exact(4).map(|b| f32::from_le_bytes([b[0], b[1], b[2], b[3]])).collect();
    let problem = ffi::read(&floats).expect("a whole board");
    let strategy = [Strategy::Lee, Strategy::AStar, Strategy::RipUp, Strategy::Negotiated, Strategy::Hadlock,
                    Strategy::Bidirectional, Strategy::Anneal][args[2].parse::<usize>().unwrap()];
    let limit: f32 = args.get(4).map_or(60.0, |s| s.parse().unwrap());
    let mut r = Router::new(&problem).expect("a board that fits");
    r.diagonal = args.get(3).map_or(false, |s| s == "1");
    r.start(strategy, Order::ShortestFirst, &problem.pads);
    let began = Instant::now();
    let mut said = 0.0;
    loop {
        let done = r.step(200_000);
        let t = began.elapsed().as_secs_f32();
        if done || t - said >= 10.0 || t > limit {
            said = t;
            let s = r.stats();
            println!("{t:6.1} s  {} of {} nets routed, {} given up, {} shared; {} moves, {} kept, at {:.0}; {:.0} mm, {} vias",
                     s[3], s[2], s[4], s[8], s[1], s[13], s[12] as f32 / 10.0, s[6] as f32 / 100.0, s[7]);
        }
        if done || t > limit {
            println!("{}", if done { "over" } else { "stopped at the limit" });
            for (net, reached, pads) in r.unrouted() {
                println!("unrouted: net {net}, {reached} of {pads} pads reached");
            }
            break;
        }
    }
}
