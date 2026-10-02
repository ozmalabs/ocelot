use serde::Serialize;
use std::alloc::{GlobalAlloc, Layout, System};
use std::hint::black_box;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

struct CountingAllocator;
static LIVE_BYTES: AtomicUsize = AtomicUsize::new(0);
static REQUESTED_BYTES: AtomicUsize = AtomicUsize::new(0);
static ALLOCATIONS: AtomicUsize = AtomicUsize::new(0);
static TRACK: AtomicBool = AtomicBool::new(false);
static TRACK_BASE: AtomicUsize = AtomicUsize::new(0);
static PEAK_DELTA: AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for CountingAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = System.alloc(layout);
        if !ptr.is_null() { record_alloc(layout.size()); }
        ptr
    }

    unsafe fn alloc_zeroed(&self, layout: Layout) -> *mut u8 {
        let ptr = System.alloc_zeroed(layout);
        if !ptr.is_null() { record_alloc(layout.size()); }
        ptr
    }

    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        LIVE_BYTES.fetch_sub(layout.size(), Ordering::SeqCst);
        System.dealloc(ptr, layout);
    }

    unsafe fn realloc(&self, ptr: *mut u8, layout: Layout, new_size: usize) -> *mut u8 {
        let next = System.realloc(ptr, layout, new_size);
        if !next.is_null() {
            let old = layout.size();
            if new_size >= old {
                LIVE_BYTES.fetch_add(new_size - old, Ordering::SeqCst);
            } else {
                LIVE_BYTES.fetch_sub(old - new_size, Ordering::SeqCst);
            }
            REQUESTED_BYTES.fetch_add(new_size, Ordering::SeqCst);
            ALLOCATIONS.fetch_add(1, Ordering::SeqCst);
            update_peak();
        }
        next
    }
}

#[global_allocator]
static ALLOCATOR: CountingAllocator = CountingAllocator;

fn record_alloc(bytes: usize) {
    LIVE_BYTES.fetch_add(bytes, Ordering::SeqCst);
    REQUESTED_BYTES.fetch_add(bytes, Ordering::SeqCst);
    ALLOCATIONS.fetch_add(1, Ordering::SeqCst);
    update_peak();
}

fn update_peak() {
    if TRACK.load(Ordering::SeqCst) {
        let base = TRACK_BASE.load(Ordering::SeqCst);
        let now = LIVE_BYTES.load(Ordering::SeqCst).saturating_sub(base);
        let mut peak = PEAK_DELTA.load(Ordering::SeqCst);
        while now > peak {
            match PEAK_DELTA.compare_exchange(peak, now, Ordering::SeqCst, Ordering::SeqCst) {
                Ok(_) => break,
                Err(actual) => peak = actual,
            }
        }
    }
}

#[derive(Clone, Copy)]
enum Topology { Path, Star, Grid }

impl Topology {
    fn name(self) -> &'static str {
        match self { Self::Path => "path", Self::Star => "star", Self::Grid => "grid" }
    }
}

#[derive(Clone, Copy)]
struct Bytes { requested: usize, retained: usize, peak: usize, allocations: usize }

#[derive(Serialize)]
struct Row {
    nodes: usize,
    topology: &'static str,
    edges: usize,
    measured_repeats: usize,
    eager_clone_requested_bytes: f64,
    shared_clone_requested_bytes: f64,
    eager_clone_retained_bytes: f64,
    shared_clone_retained_bytes: f64,
    eager_clone_peak_bytes: f64,
    shared_clone_peak_bytes: f64,
    eager_clone_allocation_count: f64,
    shared_clone_allocation_count: f64,
    eager_clone_one_write_retained_bytes: f64,
    shared_clone_one_write_retained_bytes: f64,
    eager_clone_one_percent_write_retained_bytes: f64,
    shared_clone_one_percent_write_retained_bytes: f64,
    returned_to_baseline_after_drop: bool,
    exact_sibling_isolation: bool,
}

fn measured<T>(f: impl FnOnce() -> T) -> (Bytes, bool) {
    let live_before = LIVE_BYTES.load(Ordering::SeqCst);
    let req_before = REQUESTED_BYTES.load(Ordering::SeqCst);
    let alloc_before = ALLOCATIONS.load(Ordering::SeqCst);
    TRACK_BASE.store(live_before, Ordering::SeqCst);
    PEAK_DELTA.store(0, Ordering::SeqCst);
    TRACK.store(true, Ordering::SeqCst);
    let value = f();
    TRACK.store(false, Ordering::SeqCst);
    let live_after = LIVE_BYTES.load(Ordering::SeqCst);
    let result = Bytes {
        requested: REQUESTED_BYTES.load(Ordering::SeqCst) - req_before,
        retained: live_after.saturating_sub(live_before),
        peak: PEAK_DELTA.load(Ordering::SeqCst),
        allocations: ALLOCATIONS.load(Ordering::SeqCst) - alloc_before,
    };
    let retained = result.retained;
    drop(value);
    let returned = LIVE_BYTES.load(Ordering::SeqCst) == live_before;
    black_box(retained);
    (result, returned)
}

fn median(xs: &mut [f64]) -> f64 {
    xs.sort_by(f64::total_cmp);
    let n = xs.len();
    if n % 2 == 0 { (xs[n / 2 - 1] + xs[n / 2]) / 2.0 } else { xs[n / 2] }
}

fn build_graph(nodes: usize, topology: Topology) -> (TypedGraph, usize) {
    let mut graph = TypedGraph::new();
    for _ in 0..nodes { graph.insert_node(Sym(1), Attrs::new()); }
    let mut edges = 0;
    match topology {
        Topology::Path => for i in 0..nodes.saturating_sub(1) {
            graph.insert_edge(NodeID(i as u32), Sym(2), NodeID((i + 1) as u32), Attrs::new()).unwrap(); edges += 1;
        },
        Topology::Star => for i in 1..nodes {
            graph.insert_edge(NodeID(0), Sym(2), NodeID(i as u32), Attrs::new()).unwrap(); edges += 1;
        },
        Topology::Grid => {
            let columns = (nodes as f64).sqrt().ceil() as usize;
            for i in 0..nodes {
                let row = i / columns; let col = i % columns;
                if col + 1 < columns && i + 1 < nodes {
                    graph.insert_edge(NodeID(i as u32), Sym(2), NodeID((i + 1) as u32), Attrs::new()).unwrap(); edges += 1;
                }
                let down = i + columns;
                if row + 1 < nodes.div_ceil(columns) && down < nodes {
                    graph.insert_edge(NodeID(i as u32), Sym(2), NodeID(down as u32), Attrs::new()).unwrap(); edges += 1;
                }
            }
        }
    }
    (graph, edges)
}

fn write_branch(mut graph: TypedGraph, nodes: usize, writes: usize, value: i64) -> TypedGraph {
    for j in 0..writes {
        let id = if writes == 1 { nodes / 2 } else { (j * nodes / writes).min(nodes - 1) };
        graph.set_node_attr(NodeID(id as u32), Sym(3), Value::Int(value + j as i64));
    }
    graph
}

fn run(nodes: usize, topology: Topology, repeats: usize) -> Row {
    let (base, edges) = build_graph(nodes, topology);
    let one_percent = ((nodes + 99) / 100).max(1);
    let mut eager = Vec::new(); let mut shared = Vec::new();
    let mut eager_one = Vec::new(); let mut shared_one = Vec::new();
    let mut eager_sparse = Vec::new(); let mut shared_sparse = Vec::new();
    let mut returned = true;
    for i in 0..repeats {
        // Alternate arm order; memory accounting is independent of time.
        let run_eager = |writes: Option<usize>| measured(|| {
            let graph = base.clone_eager();
            match writes { Some(n) => write_branch(graph, nodes, n, i as i64), None => graph }
        });
        let run_shared = |writes: Option<usize>| measured(|| {
            let graph = base.clone_sharing_slabs();
            match writes { Some(n) => write_branch(graph, nodes, n, i as i64), None => graph }
        });
        if i % 2 == 0 {
            let (m, ok) = run_eager(None); eager.push(m); returned &= ok;
            let (m, ok) = run_shared(None); shared.push(m); returned &= ok;
            let (m, ok) = run_eager(Some(1)); eager_one.push(m); returned &= ok;
            let (m, ok) = run_shared(Some(1)); shared_one.push(m); returned &= ok;
            let (m, ok) = run_eager(Some(one_percent)); eager_sparse.push(m); returned &= ok;
            let (m, ok) = run_shared(Some(one_percent)); shared_sparse.push(m); returned &= ok;
        } else {
            let (m, ok) = run_shared(None); shared.push(m); returned &= ok;
            let (m, ok) = run_eager(None); eager.push(m); returned &= ok;
            let (m, ok) = run_shared(Some(1)); shared_one.push(m); returned &= ok;
            let (m, ok) = run_eager(Some(1)); eager_one.push(m); returned &= ok;
            let (m, ok) = run_shared(Some(one_percent)); shared_sparse.push(m); returned &= ok;
            let (m, ok) = run_eager(Some(one_percent)); eager_sparse.push(m); returned &= ok;
        }
    }
    let metric = |items: &mut [Bytes], f: fn(Bytes) -> usize| median(&mut items.iter().map(|&x| f(x) as f64).collect::<Vec<_>>());
    let eager_clone_requested_bytes = metric(&mut eager, |x| x.requested);
    let shared_clone_requested_bytes = metric(&mut shared, |x| x.requested);
    let eager_clone_retained_bytes = metric(&mut eager, |x| x.retained);
    let shared_clone_retained_bytes = metric(&mut shared, |x| x.retained);
    let eager_clone_peak_bytes = metric(&mut eager, |x| x.peak);
    let shared_clone_peak_bytes = metric(&mut shared, |x| x.peak);
    let eager_clone_allocation_count = metric(&mut eager, |x| x.allocations);
    let shared_clone_allocation_count = metric(&mut shared, |x| x.allocations);
    let eager_clone_one_write_retained_bytes = metric(&mut eager_one, |x| x.retained);
    let shared_clone_one_write_retained_bytes = metric(&mut shared_one, |x| x.retained);
    let eager_clone_one_percent_write_retained_bytes = metric(&mut eager_sparse, |x| x.retained);
    let shared_clone_one_percent_write_retained_bytes = metric(&mut shared_sparse, |x| x.retained);

    let q = NodeID(match topology { Topology::Star => 0, _ => (nodes / 2) as u32 });
    let mut a = base.clone_sharing_slabs(); let mut b = base.clone_sharing_slabs();
    a.set_node_attr(q, Sym(3), Value::Int(11)); b.set_node_attr(q, Sym(3), Value::Int(-11));
    let exact_sibling_isolation = base.node_count() == nodes && base.edge_count() == edges
        && a.nodes_of_type(Sym(1)) == b.nodes_of_type(Sym(1))
        && a.neighbours(q, Some(Sym(2))) == b.neighbours(q, Some(Sym(2)))
        && a.node(q).attrs.get(&Sym(3)) != b.node(q).attrs.get(&Sym(3))
        && base.node(q).attrs.get(&Sym(3)).is_none();
    Row { nodes, topology: topology.name(), edges, measured_repeats: repeats,
        eager_clone_requested_bytes, shared_clone_requested_bytes,
        eager_clone_retained_bytes, shared_clone_retained_bytes,
        eager_clone_peak_bytes, shared_clone_peak_bytes,
        eager_clone_allocation_count, shared_clone_allocation_count,
        eager_clone_one_write_retained_bytes, shared_clone_one_write_retained_bytes,
        eager_clone_one_percent_write_retained_bytes, shared_clone_one_percent_write_retained_bytes,
        returned_to_baseline_after_drop: returned, exact_sibling_isolation }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let sizes = args.get(1).map(|s| s.split(',').map(|v| v.parse::<usize>().unwrap()).collect::<Vec<_>>())
        .unwrap_or_else(|| vec![771, 1771, 10771, 50771]);
    let repeats = args.get(2).map(|s| s.parse::<usize>().unwrap()).unwrap_or(7);
    let topologies = [Topology::Path, Topology::Star, Topology::Grid];
    let rows: Vec<_> = sizes.into_iter().flat_map(|n| topologies.into_iter().map(move |t| run(n, t, repeats))).collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
