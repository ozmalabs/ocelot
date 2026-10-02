use rustc_hash::FxHashMap;
use serde_json::json;
use std::sync::{Arc, Barrier};
use std::thread;
use std::time::{Duration, Instant};
use substrate_rs::checker::ConsistencyChecker;
use substrate_rs::grammar::Grammar;
use substrate_rs::substrate::{ExperimentSnapshot, Substrate};

fn assert_send_sync<T: Send + Sync>() {}

fn branch_once(snapshot: &ExperimentSnapshot, expected_nodes: usize, index: usize) -> bool {
    let mut branch = match snapshot.fork() {
        Ok(branch) => branch,
        Err(_) => return false,
    };
    let branch_type = branch.interner.intern(&format!("ThreadProbeBranch{index}"));
    branch.add_node(branch_type, FxHashMap::default());
    branch.graph.node_count() == expected_nodes + 1
        && branch.graph.edge_count() == 0
        && branch.graph.nodes_of_type(branch_type).len() == 1
}

fn serial(snapshot: &ExperimentSnapshot, size: usize, fanout: usize) -> (Duration, bool) {
    let start = Instant::now();
    let valid = (0..fanout).all(|index| branch_once(snapshot, size, index));
    (start.elapsed(), valid)
}

fn concurrent(
    snapshot: Arc<ExperimentSnapshot>,
    size: usize,
    fanout: usize,
) -> (Duration, bool) {
    let barrier = Arc::new(Barrier::new(fanout + 1));
    let mut workers = Vec::with_capacity(fanout);
    for index in 0..fanout {
        let snapshot = Arc::clone(&snapshot);
        let barrier = Arc::clone(&barrier);
        workers.push(thread::spawn(move || {
            barrier.wait();
            let start = Instant::now();
            let valid = branch_once(&snapshot, size, index);
            (start.elapsed(), valid)
        }));
    }
    let start = Instant::now();
    barrier.wait();
    let outcomes: Vec<bool> = workers
        .into_iter()
        .map(|worker| worker.join().map(|(_, valid)| valid).unwrap_or(false))
        .collect();
    let valid = outcomes.into_iter().all(|result| result);
    (start.elapsed(), valid)
}

fn main() {
    assert_send_sync::<ExperimentSnapshot>();
    let sizes = [771usize, 10_771, 50_771];
    let fanouts = [1usize, 4, 16];
    let repeats = 5usize;
    let mut rows = Vec::new();
    for size in sizes {
        for fanout in fanouts {
            let mut serial_us = Vec::with_capacity(repeats);
            let mut concurrent_us = Vec::with_capacity(repeats);
            let mut capture_us = Vec::with_capacity(repeats);
            let mut all_semantics_pass = true;
            let mut arm_orders = Vec::with_capacity(repeats);
            for repeat in 0..repeats {
                let mut primary = Substrate::new(ConsistencyChecker::new(Grammar::new()));
                let base_type = primary.interner.intern("ThreadProbeBase");
                for _ in 0..size {
                    primary.add_node(base_type, FxHashMap::default());
                }
                let capture_start = Instant::now();
                let snapshot = Arc::new(primary.snapshot().expect("capture snapshot"));
                capture_us.push(capture_start.elapsed().as_secs_f64() * 1e6);

                let (serial_duration, serial_ok, concurrent_duration, concurrent_ok) =
                    if repeat % 2 == 0 {
                        let (serial_time, serial_valid) = serial(&snapshot, size, fanout);
                        let (parallel_time, parallel_valid) = concurrent(Arc::clone(&snapshot), size, fanout);
                        arm_orders.push("serial_then_concurrent");
                        (serial_time, serial_valid, parallel_time, parallel_valid)
                    } else {
                        let (parallel_time, parallel_valid) = concurrent(Arc::clone(&snapshot), size, fanout);
                        let (serial_time, serial_valid) = serial(&snapshot, size, fanout);
                        arm_orders.push("concurrent_then_serial");
                        (serial_time, serial_valid, parallel_time, parallel_valid)
                    };
                let primary_ok = primary.graph.node_count() == size && primary.graph.edge_count() == 0;
                let later = snapshot.fork().expect("later verification fork");
                let snapshot_ok = later.graph.node_count() == size
                    && later.graph.edge_count() == 0
                    && later.graph.nodes_of_type(base_type).len() == size;
                all_semantics_pass &= serial_ok && concurrent_ok && primary_ok && snapshot_ok;
                serial_us.push(serial_duration.as_secs_f64() * 1e6);
                concurrent_us.push(concurrent_duration.as_secs_f64() * 1e6);
            }
            rows.push(json!({
                "size_nodes": size,
                "fanout": fanout,
                "repeats": repeats,
                "snapshot_capture_us": capture_us,
                "serial_batch_us": serial_us,
                "concurrent_batch_us": concurrent_us,
                "arm_order": arm_orders,
                "all_semantic_gates_pass": all_semantics_pass,
            }));
        }
    }
    println!("{}", json!({
        "schema": "CowSnapshotConcurrentForkProbeV1",
        "experiment_snapshot_send_sync": true,
        "sizes": sizes,
        "fanouts": fanouts,
        "repeats": repeats,
        "rows": rows,
    }));
}
