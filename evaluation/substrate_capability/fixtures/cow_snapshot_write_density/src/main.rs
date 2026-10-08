use rustc_hash::{FxHashMap, FxHashSet};
use serde_json::{json, Value as JsonValue};
use std::sync::{Arc, Barrier};
use std::thread;
use std::time::Instant;
use substrate_rs::checker::ConsistencyChecker;
use substrate_rs::grammar::Grammar;
use substrate_rs::graph::NodeID;
use substrate_rs::rewrite::{Effect, MatchEdge, RewriteRule};
use substrate_rs::substrate::{ExperimentSnapshot, Substrate};

#[derive(Clone)]
enum BranchBase {
    Cow(Arc<ExperimentSnapshot>),
    Eager(Arc<Substrate>),
}

impl BranchBase {
    fn fork(&self) -> Substrate {
        match self {
            Self::Cow(snapshot) => snapshot.fork().expect("CoW branch fork"),
            Self::Eager(base) => base.fork_full_copy_experiment().expect("eager branch fork"),
        }
    }

    fn name(&self) -> &'static str {
        match self {
            Self::Cow(_) => "shared_graph_pages",
            Self::Eager(_) => "full_copy",
        }
    }
}

struct BranchOutcome {
    valid: bool,
    fork_us: f64,
    closure_us: f64,
    total_us: f64,
    branch: Substrate,
}

fn micros(start: Instant) -> f64 {
    start.elapsed().as_secs_f64() * 1_000_000.0
}

fn pss_sample() -> FxHashMap<String, i64> {
    let mut out = FxHashMap::default();
    for line in std::fs::read_to_string("/proc/self/smaps_rollup")
        .expect("read smaps_rollup")
        .lines()
    {
        let Some((name, rest)) = line.split_once(':') else { continue };
        if !matches!(name, "Rss" | "Pss" | "Private_Dirty" | "Shared_Dirty" | "Swap") {
            continue;
        }
        let kib = rest.split_whitespace().next().unwrap().parse::<i64>().unwrap();
        out.insert(name.to_owned(), kib * 1024);
    }
    out
}

fn delta(now: &FxHashMap<String, i64>, before: &FxHashMap<String, i64>) -> JsonValue {
    let mut result = serde_json::Map::new();
    for key in ["Rss", "Pss", "Private_Dirty", "Shared_Dirty", "Swap"] {
        if let (Some(a), Some(b)) = (now.get(key), before.get(key)) {
            result.insert(format!("{key}_bytes"), json!(a - b));
        }
    }
    JsonValue::Object(result)
}

fn fixture(size: usize, active_count: usize, locality: &str) -> (Substrate, Arc<ExperimentSnapshot>, Arc<Substrate>, substrate_rs::sym::Sym, (u64, u64, usize)) {
    let mut primary = Substrate::new(ConsistencyChecker::new(Grammar::new()));
    let base_type = primary.interner.intern("ThreadRuleBase");
    let input_edge = primary.interner.intern("thread_rule_input");
    let filler_edge = primary.interner.intern("thread_rule_filler");
    let output_edge = primary.interner.intern("thread_rule_output");
    let src_var = primary.interner.intern("src");
    let tgt_var = primary.interner.intern("tgt");
    let mut rule = RewriteRule::default();
    rule.name = primary.interner.intern("thread_rule_closure");
    rule.match_edges = vec![MatchEdge { src_var, edge_type: input_edge, tgt_var }];
    rule.effects = vec![Effect::AddEdge {
        src_var,
        edge_type: output_edge,
        tgt_var,
        attrs: Vec::new(),
    }];
    rule.derive_access(&primary.terms);
    // AddEdge participates in the engine's read/write conflict set because an
    // existing edge makes the effect idempotent. Keep the real rule semantics
    // and use independent branch-level concurrency instead of asserting a
    // batch-safety proof the effect does not satisfy.
    rule.batch = false;

    for _ in 0..size {
        primary.add_node(base_type, FxHashMap::default());
    }
    let active_nodes: FxHashSet<usize> = if locality == "contiguous" {
        (0..active_count).collect()
    } else {
        (0..active_count).map(|j| j * size / active_count.max(1)).collect()
    };
    for i in 0..size {
        let source = NodeID(i as u32);
        let target = NodeID(((i + 1) % size) as u32);
        let edge_type = if active_nodes.contains(&i) { input_edge } else { filler_edge };
        primary.graph.insert_edge(source, edge_type, target, FxHashMap::default()).unwrap();
    }
    primary.add_rule(rule);
    let snapshot = Arc::new(primary.snapshot().expect("shared-page snapshot"));
    let eager = Arc::new(primary.fork_full_copy_experiment().expect("eager reusable base"));
    let revision = primary.experiment_graph_rule_revision();
    (primary, snapshot, eager, output_edge, revision)
}

fn run_branch(base: BranchBase, size: usize, active_count: usize, output_edge: substrate_rs::sym::Sym) -> BranchOutcome {
    let total_start = Instant::now();
    let fork_start = Instant::now();
    let mut branch = base.fork();
    let fork_us = micros(fork_start);
    let closure_start = Instant::now();
    let progress = branch.run_rules(100);
    let terminal = branch.run_rules(1);
    let closure_us = micros(closure_start);
    let valid = progress > 0
        && progress < 100
        && terminal == 0
        && branch.graph.node_count() == size
        && branch.graph.edge_count() == size + active_count
        && branch.graph.edges_by_type(output_edge).len() == active_count;
    let total_us = micros(total_start);
    BranchOutcome { valid, fork_us, closure_us, total_us, branch }
}

fn serial_batch(base: &BranchBase, size: usize, active_count: usize, output_edge: substrate_rs::sym::Sym, fanout: usize)
    -> (f64, Vec<f64>, Vec<f64>, bool)
{
    let start = Instant::now();
    let mut closures = Vec::with_capacity(fanout);
    let mut forks = Vec::with_capacity(fanout);
    let mut valid = true;
    for _ in 0..fanout {
        let result = run_branch(base.clone(), size, active_count, output_edge);
        valid &= result.valid;
        forks.push(result.fork_us);
        closures.push(result.closure_us);
        drop(result.branch);
    }
    (micros(start), forks, closures, valid)
}

fn concurrent_batch(base: BranchBase, size: usize, active_count: usize, output_edge: substrate_rs::sym::Sym, fanout: usize)
    -> (f64, Vec<f64>, Vec<f64>, bool)
{
    let barrier = Arc::new(Barrier::new(fanout + 1));
    let mut workers = Vec::with_capacity(fanout);
    for _ in 0..fanout {
        let base = base.clone();
        let barrier = Arc::clone(&barrier);
        workers.push(thread::spawn(move || {
            barrier.wait();
            run_branch(base, size, active_count, output_edge)
        }));
    }
    let start = Instant::now();
    barrier.wait();
    let results: Vec<BranchOutcome> = workers.into_iter().map(|w| w.join().expect("worker panicked")).collect();
    let wall_us = micros(start);
    let valid = results.iter().all(|r| r.valid);
    let forks = results.iter().map(|r| r.fork_us).collect();
    let closures = results.iter().map(|r| r.closure_us).collect();
    drop(results);
    (wall_us, forks, closures, valid)
}

fn memory_sample(base: BranchBase, size: usize, active_count: usize, output_edge: substrate_rs::sym::Sym, fanout: usize)
    -> (JsonValue, bool)
{
    let base_bytes = pss_sample();
    let one = run_branch(base.clone(), size, active_count, output_edge);
    let one_live = pss_sample();
    let one_valid = one.valid;
    drop(one.branch);
    let one_dropped = pss_sample();

    let barrier = Arc::new(Barrier::new(fanout + 1));
    let mut workers = Vec::with_capacity(fanout);
    for _ in 0..fanout {
        let base = base.clone();
        let barrier = Arc::clone(&barrier);
        workers.push(thread::spawn(move || {
            barrier.wait();
            run_branch(base, size, active_count, output_edge)
        }));
    }
    barrier.wait();
    let branches: Vec<BranchOutcome> = workers.into_iter().map(|w| w.join().expect("memory worker panicked")).collect();
    let fanout_valid = branches.iter().all(|b| b.valid);
    let fanout_live = pss_sample();
    drop(branches);
    let fanout_dropped = pss_sample();
    let summary = json!({
        "baseline_bytes": base_bytes,
        "one_branch_live_delta": delta(&one_live, &base_bytes),
        "one_branch_dropped_delta": delta(&one_dropped, &base_bytes),
        "fanout_live_delta": delta(&fanout_live, &base_bytes),
        "fanout_dropped_delta": delta(&fanout_dropped, &base_bytes),
    });
    (summary, one_valid && fanout_valid)
}

fn med(values: &[f64]) -> f64 {
    let mut x = values.to_vec();
    x.sort_by(f64::total_cmp);
    if x.len() % 2 == 0 { (x[x.len()/2 - 1] + x[x.len()/2]) / 2.0 } else { x[x.len()/2] }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() != 6 { panic!("usage: probe SIZE FANOUT REPEAT_INDEX ACTIVE_COUNT LOCALITY"); }
    let size = args[1].parse::<usize>().unwrap();
    let fanout = args[2].parse::<usize>().unwrap();
    let repeat = args[3].parse::<usize>().unwrap();
    let active_count = args[4].parse::<usize>().unwrap();
    let locality = args[5].as_str();
    assert!(size > 0 && fanout > 0 && repeat < 5 && active_count <= size);
    assert!(matches!(locality, "contiguous" | "spread"));
    let (mut primary, cow_snapshot, eager_template, output_edge, primary_revision) = fixture(size, active_count, locality);
    let cow_base = BranchBase::Cow(cow_snapshot);
    let eager_base = BranchBase::Eager(eager_template);
    let mut all_valid = true;

    let memory_order: Vec<(&str, BranchBase)> = if repeat % 2 == 0 {
        vec![("cow", cow_base.clone()), ("eager", eager_base.clone())]
    } else {
        vec![("eager", eager_base.clone()), ("cow", cow_base.clone())]
    };
    let mut memory = serde_json::Map::new();
    for (name, base) in memory_order {
        let (sample, valid) = memory_sample(base, size, active_count, output_edge, fanout);
        all_valid &= valid;
        memory.insert(name.to_owned(), sample);
    }

    let order: Vec<(&str, BranchBase, bool)> = if repeat % 2 == 0 {
        vec![("cow_serial", cow_base.clone(), false), ("cow_concurrent", cow_base.clone(), true),
             ("eager_serial", eager_base.clone(), false), ("eager_concurrent", eager_base.clone(), true)]
    } else {
        vec![("eager_concurrent", eager_base.clone(), true), ("eager_serial", eager_base.clone(), false),
             ("cow_concurrent", cow_base.clone(), true), ("cow_serial", cow_base.clone(), false)]
    };
    let mut arms = serde_json::Map::new();
    for (name, base, parallel) in &order {
        let (wall, forks, closures, valid) = if *parallel {
            concurrent_batch(base.clone(), size, active_count, output_edge, fanout)
        } else {
            serial_batch(base, size, active_count, output_edge, fanout)
        };
        all_valid &= valid;
        arms.insert((*name).to_owned(), json!({"wall_us":wall,"branch_fork_us":forks,"closure_us":closures}));
    }

    let primary_ok = primary.graph.node_count() == size
        && primary.graph.edge_count() == size
        && primary.graph.edges_by_type(primary.interner.intern("thread_rule_input")).len() == active_count
        && primary.graph.edges_by_type(output_edge).is_empty()
        && primary.experiment_graph_rule_revision() == primary_revision;
    let later_cow = cow_base.fork();
    let later_eager = eager_base.fork();
    let later_ok = [&later_cow, &later_eager].iter().all(|branch| {
        branch.graph.node_count() == size
            && branch.graph.edge_count() == size
            && branch.graph.edges_by_type(output_edge).is_empty()
    });
    all_valid &= primary_ok && later_ok;

    println!("{}", json!({
        "schema":"CowSnapshotWriteDensityLocalityCellV1",
        "size_nodes":size,"fanout":fanout,"repeat_index":repeat,
        "active_edges":active_count,"density":active_count as f64 / size as f64,"locality":locality,
        "arm_order":order.iter().map(|x|x.0).collect::<Vec<_>>(),
        "arms":arms,"memory":memory,
        "primary_unchanged":primary_ok,"later_forks_see_captured_base":later_ok,
        "all_semantic_gates_pass":all_valid,
    }));
}
