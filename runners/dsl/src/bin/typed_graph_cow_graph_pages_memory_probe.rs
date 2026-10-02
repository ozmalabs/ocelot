use serde::Serialize;
use std::alloc::{GlobalAlloc, Layout, System};
use std::sync::atomic::{AtomicUsize, Ordering};
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;

struct Meter;
static LIVE: AtomicUsize = AtomicUsize::new(0);

unsafe impl GlobalAlloc for Meter {
    unsafe fn alloc(&self, l: Layout) -> *mut u8 {
        let p = System.alloc(l);
        if !p.is_null() {
            added(l.size());
        }
        p
    }
    unsafe fn alloc_zeroed(&self, l: Layout) -> *mut u8 {
        let p = System.alloc_zeroed(l);
        if !p.is_null() {
            added(l.size());
        }
        p
    }
    unsafe fn dealloc(&self, p: *mut u8, l: Layout) {
        LIVE.fetch_sub(l.size(), Ordering::SeqCst);
        System.dealloc(p, l);
    }
    unsafe fn realloc(&self, p: *mut u8, l: Layout, n: usize) -> *mut u8 {
        let q = System.realloc(p, l, n);
        if !q.is_null() {
            if n >= l.size() {
                LIVE.fetch_add(n - l.size(), Ordering::SeqCst);
            } else {
                LIVE.fetch_sub(l.size() - n, Ordering::SeqCst);
            }
        }
        q
    }
}
#[global_allocator]
static ALLOCATOR: Meter = Meter;

fn added(n: usize) {
    LIVE.fetch_add(n, Ordering::SeqCst);
}

#[derive(Clone, Copy)]
enum Topology {
    Path,
    Star,
    Grid,
}
impl Topology {
    fn name(self) -> &'static str {
        match self {
            Self::Path => "path",
            Self::Star => "star",
            Self::Grid => "grid",
        }
    }
}
#[derive(Clone, Copy)]
enum Backend {
    Eager,
    SharedRecords,
    SharedGraphPages,
}
impl Backend {
    const ALL: [Self; 3] = [Self::Eager, Self::SharedRecords, Self::SharedGraphPages];
    fn clone_graph(self, g: &TypedGraph) -> TypedGraph {
        match self {
            Self::Eager => g.clone_eager(),
            Self::SharedRecords => g.clone_sharing_slabs(),
            Self::SharedGraphPages => g.clone_sharing_graph_pages(),
        }
    }
}
#[derive(Clone, Copy)]
struct M {
    retained: usize,
}

#[derive(Serialize)]
struct Row {
    nodes: usize,
    topology: &'static str,
    base_edges: usize,
    repeats: usize,
    eager_clone_retained_bytes: f64,
    shared_records_clone_retained_bytes: f64,
    shared_graph_pages_clone_retained_bytes: f64,
    eager_one_edge_retained_bytes: f64,
    shared_records_one_edge_retained_bytes: f64,
    shared_graph_pages_one_edge_retained_bytes: f64,
    eager_one_percent_edges_retained_bytes: f64,
    shared_records_one_percent_edges_retained_bytes: f64,
    shared_graph_pages_one_percent_edges_retained_bytes: f64,
    branches_return_to_live_baseline: bool,
    exact_query_and_sibling_isolation: bool,
}

fn measured<T>(f: impl FnOnce() -> T) -> (M, bool) {
    let before = LIVE.load(Ordering::SeqCst);
    let value = f();
    let now = LIVE.load(Ordering::SeqCst);
    let m = M {
        retained: now.saturating_sub(before),
    };
    drop(value);
    (m, LIVE.load(Ordering::SeqCst) == before)
}
fn median(v: &mut [f64]) -> f64 {
    v.sort_by(f64::total_cmp);
    let n = v.len();
    if n % 2 == 0 {
        (v[n / 2 - 1] + v[n / 2]) / 2.
    } else {
        v[n / 2]
    }
}
fn med(v: &[M]) -> f64 {
    median(&mut v.iter().map(|x| x.retained as f64).collect::<Vec<_>>())
}

fn build(nodes: usize, top: Topology) -> (TypedGraph, usize) {
    let mut g = TypedGraph::new();
    for _ in 0..nodes {
        g.insert_node(Sym(1), Attrs::new());
    }
    let mut e = 0;
    match top {
        Topology::Path => {
            for i in 0..nodes.saturating_sub(1) {
                g.insert_edge(
                    NodeID(i as u32),
                    Sym(2),
                    NodeID((i + 1) as u32),
                    Attrs::new(),
                )
                .unwrap();
                e += 1;
            }
        }
        Topology::Star => {
            for i in 1..nodes {
                g.insert_edge(NodeID(0), Sym(2), NodeID(i as u32), Attrs::new())
                    .unwrap();
                e += 1;
            }
        }
        Topology::Grid => {
            let c = (nodes as f64).sqrt().ceil() as usize;
            for i in 0..nodes {
                let r = i / c;
                let col = i % c;
                if col + 1 < c && i + 1 < nodes {
                    g.insert_edge(
                        NodeID(i as u32),
                        Sym(2),
                        NodeID((i + 1) as u32),
                        Attrs::new(),
                    )
                    .unwrap();
                    e += 1;
                }
                let d = i + c;
                if r + 1 < nodes.div_ceil(c) && d < nodes {
                    g.insert_edge(NodeID(i as u32), Sym(2), NodeID(d as u32), Attrs::new())
                        .unwrap();
                    e += 1;
                }
            }
        }
    }
    (g, e)
}
fn pairs(n: usize, count: usize) -> Vec<(NodeID, NodeID)> {
    (0..count)
        .map(|j| {
            let src = if count == 1 {
                n - 1
            } else {
                1 + j * (n - 1) / count
            };
            (NodeID(src as u32), NodeID(0))
        })
        .collect()
}
fn branch(g: &TypedGraph, b: Backend, ps: &[(NodeID, NodeID)]) -> (TypedGraph, bool) {
    let mut c = b.clone_graph(g);
    let mut ok = true;
    for &(s, t) in ps {
        ok &= c.insert_edge(s, Sym(2), t, Attrs::new()).is_ok();
    }
    (c, ok)
}

fn run(nodes: usize, top: Topology, repeats: usize) -> Row {
    let (base, base_edges) = build(nodes, top);
    let one = pairs(nodes, 1);
    let sparse = pairs(nodes, ((nodes + 99) / 100).max(1));
    let mut clone: [Vec<M>; 3] = std::array::from_fn(|_| Vec::new());
    let mut one_m: [Vec<M>; 3] = std::array::from_fn(|_| Vec::new());
    let mut sparse_m: [Vec<M>; 3] = std::array::from_fn(|_| Vec::new());
    let mut returned = true;
    for i in 0..repeats {
        for step in 0..3 {
            let b = Backend::ALL[(step + i) % 3];
            let ix = match b {
                Backend::Eager => 0,
                Backend::SharedRecords => 1,
                Backend::SharedGraphPages => 2,
            };
            let (m, ok) = measured(|| b.clone_graph(&base));
            clone[ix].push(m);
            returned &= ok;
            let (m, ok) = measured(|| branch(&base, b, &one));
            one_m[ix].push(m);
            returned &= ok;
            let (m, ok) = measured(|| branch(&base, b, &sparse));
            sparse_m[ix].push(m);
            returned &= ok;
        }
    }
    let q = NodeID(match top {
        Topology::Star => 0,
        _ => (nodes / 2) as u32,
    });
    let mut a = base.clone_sharing_graph_pages();
    let mut b = base.clone_sharing_graph_pages();
    a.insert_edge(NodeID((nodes - 1) as u32), Sym(2), NodeID(0), Attrs::new())
        .unwrap();
    b.insert_edge(NodeID((nodes - 2) as u32), Sym(2), NodeID(0), Attrs::new())
        .unwrap();
    let exact = base.edge_count() == base_edges
        && a.edge_count() == base_edges + 1
        && b.edge_count() == base_edges + 1
        && !base.has_edge(NodeID((nodes - 1) as u32), Sym(2), NodeID(0))
        && !b.has_edge(NodeID((nodes - 1) as u32), Sym(2), NodeID(0))
        && a.neighbours(q, Some(Sym(2))) == b.neighbours(q, Some(Sym(2)));
    Row {
        nodes,
        topology: top.name(),
        base_edges,
        repeats,
        eager_clone_retained_bytes: med(&clone[0]),
        shared_records_clone_retained_bytes: med(&clone[1]),
        shared_graph_pages_clone_retained_bytes: med(&clone[2]),
        eager_one_edge_retained_bytes: med(&one_m[0]),
        shared_records_one_edge_retained_bytes: med(&one_m[1]),
        shared_graph_pages_one_edge_retained_bytes: med(&one_m[2]),
        eager_one_percent_edges_retained_bytes: med(&sparse_m[0]),
        shared_records_one_percent_edges_retained_bytes: med(&sparse_m[1]),
        shared_graph_pages_one_percent_edges_retained_bytes: med(&sparse_m[2]),
        branches_return_to_live_baseline: returned,
        exact_query_and_sibling_isolation: exact,
    }
}
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let sizes = a
        .get(1)
        .map(|s| {
            s.split(',')
                .map(|x| x.parse::<usize>().unwrap())
                .collect::<Vec<_>>()
        })
        .unwrap_or_else(|| vec![771, 1771, 10771, 50771]);
    let reps = a.get(2).map(|s| s.parse::<usize>().unwrap()).unwrap_or(7);
    let ts = [Topology::Path, Topology::Star, Topology::Grid];
    let rows: Vec<_> = sizes
        .into_iter()
        .flat_map(|n| ts.into_iter().map(move |t| run(n, t, reps)))
        .collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
