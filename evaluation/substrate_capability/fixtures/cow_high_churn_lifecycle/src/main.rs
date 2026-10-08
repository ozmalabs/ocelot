use rustc_hash::FxHashMap;
use serde_json::json;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::{Arc, Barrier, Mutex};
use std::thread;
use std::time::Instant;
use substrate_rs::checker::ConsistencyChecker;
use substrate_rs::grammar::Grammar;
use substrate_rs::substrate::{ExperimentSnapshot, Substrate};

struct Meter;
static LIVE: AtomicUsize = AtomicUsize::new(0);
unsafe impl GlobalAlloc for Meter {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        let p = System.alloc(l);
        if !p.is_null() { LIVE.fetch_add(l.size(), Ordering::SeqCst); }
        p
    }
    unsafe fn alloc_zeroed(&self, l: Layout) -> *mut u8 {
        let p = System.alloc_zeroed(l);
        if !p.is_null() { LIVE.fetch_add(l.size(), Ordering::SeqCst); }
        p
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) {
        LIVE.fetch_sub(l.size(), Ordering::SeqCst);
        System.dealloc(p, l)
    }
    unsafe fn realloc(&self, p: *mut u8, l: Layout, n: usize) -> *mut u8 {
        let q = System.realloc(p, l, n);
        if !q.is_null() {
            if n >= l.size() { LIVE.fetch_add(n - l.size(), Ordering::SeqCst); }
            else { LIVE.fetch_sub(l.size() - n, Ordering::SeqCst); }
        }
        q
    }
}
#[global_allocator]
static ALLOCATOR: Meter = Meter;

#[derive(Clone, Copy)]
enum Backend { SharedSnapshot, EagerCopy }
impl Backend {
    fn name(self) -> &'static str {
        match self { Self::SharedSnapshot => "shared_snapshot", Self::EagerCopy => "eager_copy" }
    }
}

fn thread_only_delta(fanout: usize) -> i64 {
    let ready = Arc::new(Barrier::new(fanout + 1));
    let cancel = Arc::new(Barrier::new(fanout + 1));
    let after_cancel = Arc::new(Barrier::new(fanout + 1));
    let release = Arc::new(Barrier::new(fanout + 1));
    let baseline = LIVE.load(Ordering::SeqCst);
    let mut workers = Vec::with_capacity(fanout);
    for _ in 0..fanout {
        let ready = Arc::clone(&ready);
        let cancel = Arc::clone(&cancel);
        let after_cancel = Arc::clone(&after_cancel);
        let release = Arc::clone(&release);
        workers.push(thread::spawn(move || {
            ready.wait();
            cancel.wait();
            after_cancel.wait();
            release.wait();
        }));
    }
    ready.wait();
    cancel.wait();
    after_cancel.wait();
    release.wait();
    for worker in workers { worker.join().expect("control worker panicked"); }
    LIVE.load(Ordering::SeqCst) as i64 - baseline as i64
}

fn fixture(size: usize) -> (Substrate, substrate_rs::sym::Sym) {
    let mut primary = Substrate::new(ConsistencyChecker::new(Grammar::new()));
    let base_type = primary.intern_symbol("ConcurrentLifecycleBase");
    for index in 0..16 { primary.intern_symbol(&format!("ConcurrentBranch{index}")); }
    for _ in 0..size { primary.add_node(base_type, FxHashMap::default()); }
    (primary, base_type)
}

fn one_wave(primary: Arc<Substrate>, snapshot: Option<Arc<ExperimentSnapshot>>, base_type: substrate_rs::sym::Sym,
            size: usize, fanout: usize, backend: Backend, repeat: usize, mutate: bool) -> serde_json::Value {
    let control_delta = thread_only_delta(fanout);
    let ready = Arc::new(Barrier::new(fanout + 1));
    let cancel = Arc::new(Barrier::new(fanout + 1));
    let after_cancel = Arc::new(Barrier::new(fanout + 1));
    let release = Arc::new(Barrier::new(fanout + 1));
    let cancel_count = if fanout == 1 { 0 } else { fanout / 2 };
    let all_semantics = Arc::new(AtomicBool::new(true));
    let branch_ids = Arc::new(Mutex::new(Vec::with_capacity(fanout)));
    let mut workers = Vec::with_capacity(fanout);
    let baseline = LIVE.load(Ordering::SeqCst);
    let start = Instant::now();
    for index in 0..fanout {
        let primary = Arc::clone(&primary);
        let snapshot = snapshot.as_ref().map(Arc::clone);
        let ready = Arc::clone(&ready);
        let cancel = Arc::clone(&cancel);
        let after_cancel = Arc::clone(&after_cancel);
        let release = Arc::clone(&release);
        let all_semantics = Arc::clone(&all_semantics);
        let branch_ids = Arc::clone(&branch_ids);
        workers.push(thread::spawn(move || {
            let branch = match backend {
                Backend::SharedSnapshot => snapshot.unwrap().fork().expect("snapshot fork"),
                Backend::EagerCopy => primary.fork_full_copy_experiment().expect("eager fork"),
            };
            let mut branch = Some(branch);
            let branch_type = branch.as_ref().unwrap().interner().lookup(&format!("ConcurrentBranch{index}"))
                .expect("branch symbol preloaded in immutable base");
            let added_id = if mutate {
                Some(branch.as_mut().unwrap().add_node(branch_type, FxHashMap::default()).0)
            } else { None };
            branch_ids.lock().unwrap().push((index, added_id));
            let expected_nodes = size + usize::from(mutate);
            let valid = branch.as_ref().unwrap().graph.node_count() == expected_nodes
                && branch.as_ref().unwrap().graph.nodes_of_type(branch_type).len() == usize::from(mutate)
                && branch.as_ref().unwrap().graph.nodes_of_type(base_type).len() == size;
            if !valid { all_semantics.store(false, Ordering::SeqCst); }
            ready.wait();
            cancel.wait();
            if index < cancel_count { drop(branch.take()); }
            after_cancel.wait();
            if index >= cancel_count {
                if branch.as_ref().unwrap().graph.node_count() != expected_nodes
                    || branch.as_ref().unwrap().graph.nodes_of_type(branch_type).len() != usize::from(mutate) {
                    all_semantics.store(false, Ordering::SeqCst);
                }
            }
            release.wait();
            drop(branch);
        }));
    }
    ready.wait();
    let all_live = LIVE.load(Ordering::SeqCst);
    cancel.wait();
    after_cancel.wait();
    let after_cancel_bytes = LIVE.load(Ordering::SeqCst);
    release.wait();
    for worker in workers { worker.join().expect("worker panicked"); }
    let mut branch_ids = Arc::try_unwrap(branch_ids).expect("branch ID receipts shared after join").into_inner().unwrap();
    branch_ids.sort_by_key(|row| row.0);
    let branch_added_ids: Vec<Option<u32>> = branch_ids.into_iter().map(|row| row.1).collect();
    let elapsed_us = start.elapsed().as_secs_f64() * 1e6;
    let after_drop = LIVE.load(Ordering::SeqCst);
    let raw_after_drop_delta = after_drop as i64 - baseline as i64;
    let adjusted_after_drop_delta = raw_after_drop_delta - control_delta;
    let primary_ok = primary.graph.node_count() == size && primary.graph.edge_count() == 0
        && primary.graph.nodes_of_type(base_type).len() == size;
    json!({
        "size_nodes": size, "fanout": fanout, "backend": backend.name(), "repeat": repeat,
        "branch_added_ids": branch_added_ids,
        "cancelled_branches": cancel_count, "wave_wall_us": elapsed_us,
        "baseline_live_bytes": baseline,
        "all_live_delta_bytes": all_live as i64 - baseline as i64,
        "after_cancel_delta_bytes": after_cancel_bytes as i64 - baseline as i64,
        "thread_only_control_delta_bytes": control_delta,
        "after_drop_delta_bytes": raw_after_drop_delta,
        "thread_adjusted_after_drop_delta_bytes": adjusted_after_drop_delta,
        "all_semantics_pass": all_semantics.load(Ordering::SeqCst),
        "primary_unchanged": primary_ok,
        "all_live_bytes_increased": all_live > baseline,
        "cancel_reduced_live_bytes": after_cancel_bytes < all_live || cancel_count == 0,
        "thread_control_adjusted_after_drop_delta_bytes": adjusted_after_drop_delta,
    })
}

fn main() {
    fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<ExperimentSnapshot>();
    assert_send_sync::<Substrate>();
    let sizes = [10_000usize, 50_000];
    let fanouts = [4usize, 16];
    let repeats = 25usize;
    let mut rows = Vec::new();
    for size in sizes {
        for fanout in fanouts {
            let (primary, base_type) = fixture(size);
            let primary = Arc::new(primary);
            let snapshot = Arc::new(primary.snapshot().expect("snapshot"));
            for repeat in 0..repeats {
                let order = if repeat % 2 == 0 {
                    [Backend::SharedSnapshot, Backend::EagerCopy]
                } else { [Backend::EagerCopy, Backend::SharedSnapshot] };
                for backend in order {
                    let control = one_wave(Arc::clone(&primary), Some(Arc::clone(&snapshot)), base_type,
                                           size, fanout, backend, repeat, false);
                    let mut measured = one_wave(Arc::clone(&primary), Some(Arc::clone(&snapshot)), base_type,
                                                size, fanout, backend, repeat, true);
                    let control_live = control["all_live_delta_bytes"].as_i64().unwrap();
                    let control_cancel = control["after_cancel_delta_bytes"].as_i64().unwrap();
                    let control_drop = control["after_drop_delta_bytes"].as_i64().unwrap();
                    let live = measured["all_live_delta_bytes"].as_i64().unwrap();
                    let cancelled = measured["after_cancel_delta_bytes"].as_i64().unwrap();
                    let dropped = measured["after_drop_delta_bytes"].as_i64().unwrap();
                    measured["fork_only_control_all_live_delta_bytes"] = json!(control_live);
                    measured["fork_only_control_after_cancel_delta_bytes"] = json!(control_cancel);
                    measured["fork_only_control_after_drop_delta_bytes"] = json!(control_drop);
                    measured["mutation_adjusted_all_live_bytes"] = json!(live - control_live);
                    measured["mutation_adjusted_after_cancel_bytes"] = json!(cancelled - control_cancel);
                    measured["mutation_adjusted_after_drop_bytes"] = json!(dropped - control_drop);
                    measured["mutation_adjusted_reclamation_pass"] = json!(dropped == control_drop);
                    measured["wave_index"] = json!(repeat);
                    rows.push(measured);
                }
            }
            let later = snapshot.fork().expect("post-churn snapshot fork");
            let later_ok = later.graph.node_count() == size
                && later.graph.nodes_of_type(base_type).len() == size;
            if !later_ok { panic!("later snapshot fork changed after high-churn waves"); }
            drop(later);
            if primary.graph.node_count() != size || primary.graph.edge_count() != 0
                || primary.graph.nodes_of_type(base_type).len() != size {
                panic!("primary changed after high-churn waves");
            }
        }
    }
    println!("{}", json!({"schema":"CowHighChurnLifecycleProbeV1",
        "sizes":sizes,"fanouts":fanouts,"repeats":repeats,"rows":rows}));
}
