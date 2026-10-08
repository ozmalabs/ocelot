use serde::Serialize;
use std::hint::black_box;
use std::time::Instant;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;

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
    fn clone_graph(self, base: &TypedGraph) -> TypedGraph {
        match self {
            Self::Eager => base.clone_eager(),
            Self::SharedRecords => base.clone_sharing_slabs(),
            Self::SharedGraphPages => base.clone_sharing_graph_pages(),
        }
    }
}

#[derive(Serialize)]
struct Row {
    nodes: usize,
    topology: &'static str,
    base_edges: usize,
    repeats: usize,
    eager_clone_us: f64,
    shared_records_clone_us: f64,
    shared_graph_pages_clone_us: f64,
    eager_clone_one_edge_us: f64,
    shared_records_clone_one_edge_us: f64,
    shared_graph_pages_clone_one_edge_us: f64,
    eager_clone_one_percent_edges_us: f64,
    shared_records_clone_one_percent_edges_us: f64,
    shared_graph_pages_clone_one_percent_edges_us: f64,
    exact_edge_query_and_sibling_isolation: bool,
}

fn median(xs: &mut [f64]) -> f64 {
    xs.sort_by(f64::total_cmp);
    let n = xs.len();
    if n % 2 == 0 {
        (xs[n / 2 - 1] + xs[n / 2]) / 2.0
    } else {
        xs[n / 2]
    }
}
fn us(start: Instant) -> f64 {
    start.elapsed().as_secs_f64() * 1_000_000.0
}

fn build_graph(nodes: usize, topology: Topology) -> (TypedGraph, usize) {
    let mut g = TypedGraph::new();
    for _ in 0..nodes {
        g.insert_node(Sym(1), Attrs::new());
    }
    let mut edges = 0;
    match topology {
        Topology::Path => {
            for i in 0..nodes.saturating_sub(1) {
                g.insert_edge(
                    NodeID(i as u32),
                    Sym(2),
                    NodeID((i + 1) as u32),
                    Attrs::new(),
                )
                .unwrap();
                edges += 1;
            }
        }
        Topology::Star => {
            for i in 1..nodes {
                g.insert_edge(NodeID(0), Sym(2), NodeID(i as u32), Attrs::new())
                    .unwrap();
                edges += 1;
            }
        }
        Topology::Grid => {
            let columns = (nodes as f64).sqrt().ceil() as usize;
            for i in 0..nodes {
                let row = i / columns;
                let col = i % columns;
                if col + 1 < columns && i + 1 < nodes {
                    g.insert_edge(
                        NodeID(i as u32),
                        Sym(2),
                        NodeID((i + 1) as u32),
                        Attrs::new(),
                    )
                    .unwrap();
                    edges += 1;
                }
                let down = i + columns;
                if row + 1 < nodes.div_ceil(columns) && down < nodes {
                    g.insert_edge(NodeID(i as u32), Sym(2), NodeID(down as u32), Attrs::new())
                        .unwrap();
                    edges += 1;
                }
            }
        }
    }
    (g, edges)
}

fn inserted_pairs(nodes: usize, writes: usize) -> Vec<(NodeID, NodeID)> {
    (0..writes)
        .map(|j| {
            let src = if writes == 1 {
                nodes - 1
            } else {
                1 + j * (nodes - 1) / writes
            };
            (NodeID(src as u32), NodeID(0))
        })
        .collect()
}

fn mutate(
    mut branch: TypedGraph,
    pairs: &[(NodeID, NodeID)],
) -> (TypedGraph, bool, Vec<(NodeID, Vec<NodeID>)>) {
    let mut ok = true;
    let mut touched = Vec::with_capacity(pairs.len());
    for &(src, tgt) in pairs {
        ok &= branch.insert_edge(src, Sym(2), tgt, Attrs::new()).is_ok();
        touched.push((src, tgt));
    }
    let signature: Vec<_> = touched
        .iter()
        .map(|(src, _)| (*src, branch.neighbours(*src, Some(Sym(2)))))
        .collect();
    (branch, ok, signature)
}

fn run(nodes: usize, topology: Topology, repeats: usize) -> Row {
    let (base, base_edges) = build_graph(nodes, topology);
    let one = inserted_pairs(nodes, 1);
    let sparse = inserted_pairs(nodes, ((nodes + 99) / 100).max(1));
    let mut clone_times: [Vec<f64>; 3] = std::array::from_fn(|_| Vec::new());
    let mut one_times: [Vec<f64>; 3] = std::array::from_fn(|_| Vec::new());
    let mut sparse_times: [Vec<f64>; 3] = std::array::from_fn(|_| Vec::new());
    let mut exact = true;

    for rep in 0..repeats {
        let order = std::array::from_fn::<_, 3, _>(|i| Backend::ALL[(i + rep) % 3]);
        let mut one_signatures: [Option<Vec<(NodeID, Vec<NodeID>)>>; 3] = [None, None, None];
        let mut sparse_signatures: [Option<Vec<(NodeID, Vec<NodeID>)>>; 3] = [None, None, None];
        for backend in order {
            let index = match backend {
                Backend::Eager => 0,
                Backend::SharedRecords => 1,
                Backend::SharedGraphPages => 2,
            };
            let t = Instant::now();
            let branch = backend.clone_graph(&base);
            clone_times[index].push(us(t));
            black_box((branch.node_count(), branch.edge_count()));
            drop(branch);

            let t = Instant::now();
            let (branch, inserted, signature) = mutate(backend.clone_graph(&base), &one);
            one_times[index].push(us(t));
            let expected = base.neighbours(one[0].0, Some(Sym(2)));
            let mut expected_after = expected;
            expected_after.push(one[0].1);
            exact &= inserted
                && branch.edge_count() == base_edges + 1
                && signature[0].1 == expected_after
                && !base.has_edge(one[0].0, Sym(2), one[0].1);
            one_signatures[index] = Some(signature);
            drop(branch);

            let t = Instant::now();
            let (branch, inserted, signature) = mutate(backend.clone_graph(&base), &sparse);
            sparse_times[index].push(us(t));
            exact &= inserted
                && branch.edge_count() == base_edges + sparse.len()
                && sparse.iter().all(|&(src, tgt)| {
                    branch.has_edge(src, Sym(2), tgt) && !base.has_edge(src, Sym(2), tgt)
                });
            sparse_signatures[index] = Some(signature);
            drop(branch);
        }
        exact &= one_signatures[0] == one_signatures[1]
            && one_signatures[1] == one_signatures[2]
            && sparse_signatures[0] == sparse_signatures[1]
            && sparse_signatures[1] == sparse_signatures[2];
    }
    let qa = NodeID(match topology {
        Topology::Star => 0,
        _ => (nodes / 2) as u32,
    });
    let mut a = base.clone_sharing_graph_pages();
    let mut b = base.clone_sharing_graph_pages();
    a.insert_edge(
        NodeID(nodes.saturating_sub(1) as u32),
        Sym(2),
        NodeID(0),
        Attrs::new(),
    )
    .unwrap();
    b.insert_edge(
        NodeID(nodes.saturating_sub(2) as u32),
        Sym(2),
        NodeID(0),
        Attrs::new(),
    )
    .unwrap();
    exact &= base.edge_count() == base_edges
        && a.edge_count() == base_edges + 1
        && b.edge_count() == base_edges + 1
        && !base.has_edge(NodeID(nodes.saturating_sub(1) as u32), Sym(2), NodeID(0))
        && !b.has_edge(NodeID(nodes.saturating_sub(1) as u32), Sym(2), NodeID(0))
        && !a.has_edge(NodeID(nodes.saturating_sub(2) as u32), Sym(2), NodeID(0))
        && a.nodes_of_type(Sym(1)) == base.nodes_of_type(Sym(1))
        && a.neighbours(qa, Some(Sym(2))) == b.neighbours(qa, Some(Sym(2)));

    Row {
        nodes,
        topology: topology.name(),
        base_edges,
        repeats,
        eager_clone_us: median(&mut clone_times[0]),
        shared_records_clone_us: median(&mut clone_times[1]),
        shared_graph_pages_clone_us: median(&mut clone_times[2]),
        eager_clone_one_edge_us: median(&mut one_times[0]),
        shared_records_clone_one_edge_us: median(&mut one_times[1]),
        shared_graph_pages_clone_one_edge_us: median(&mut one_times[2]),
        eager_clone_one_percent_edges_us: median(&mut sparse_times[0]),
        shared_records_clone_one_percent_edges_us: median(&mut sparse_times[1]),
        shared_graph_pages_clone_one_percent_edges_us: median(&mut sparse_times[2]),
        exact_edge_query_and_sibling_isolation: exact,
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let sizes = args
        .get(1)
        .map(|s| {
            s.split(',')
                .map(|v| v.parse::<usize>().unwrap())
                .collect::<Vec<_>>()
        })
        .unwrap_or_else(|| vec![771, 1771, 10771, 50771]);
    let repeats = args
        .get(2)
        .map(|s| s.parse::<usize>().unwrap())
        .unwrap_or(25);
    let topologies = [Topology::Path, Topology::Star, Topology::Grid];
    let rows: Vec<_> = sizes
        .into_iter()
        .flat_map(|n| topologies.into_iter().map(move |t| run(n, t, repeats)))
        .collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
