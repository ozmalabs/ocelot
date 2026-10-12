use serde::Serialize;
use std::hint::black_box;
use std::time::Instant;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Clone, Copy)]
enum Topology { Path, Star, Grid }

impl Topology {
    fn name(self) -> &'static str {
        match self { Self::Path => "path", Self::Star => "star", Self::Grid => "grid" }
    }
}

#[derive(Serialize)]
struct Row {
    nodes: usize,
    topology: &'static str,
    edges: usize,
    repeats: usize,
    eager_clone_us: f64,
    shared_slab_clone_us: f64,
    eager_clone_one_write_us: f64,
    shared_slab_clone_one_write_us: f64,
    eager_clone_one_percent_writes_us: f64,
    shared_slab_clone_one_percent_writes_us: f64,
    exact_query_and_sibling_isolation: bool,
}

fn median(mut xs: Vec<f64>) -> f64 {
    xs.sort_by(f64::total_cmp);
    let n = xs.len();
    if n % 2 == 0 { (xs[n / 2 - 1] + xs[n / 2]) / 2.0 } else { xs[n / 2] }
}

fn micros(start: Instant) -> f64 { start.elapsed().as_secs_f64() * 1_000_000.0 }

fn build_graph(nodes: usize, topology: Topology) -> (TypedGraph, usize) {
    let mut graph = TypedGraph::new();
    let node_type = Sym(1);
    let edge_type = Sym(2);
    for _ in 0..nodes { graph.insert_node(node_type, Attrs::new()); }
    let mut edges = 0;
    match topology {
        Topology::Path => for i in 0..nodes.saturating_sub(1) {
            graph.insert_edge(NodeID(i as u32), edge_type, NodeID((i + 1) as u32), Attrs::new()).unwrap();
            edges += 1;
        },
        Topology::Star => for i in 1..nodes {
            graph.insert_edge(NodeID(0), edge_type, NodeID(i as u32), Attrs::new()).unwrap();
            edges += 1;
        },
        Topology::Grid => {
            let columns = (nodes as f64).sqrt().ceil() as usize;
            for i in 0..nodes {
                let row = i / columns;
                let col = i % columns;
                if col + 1 < columns && i + 1 < nodes {
                    graph.insert_edge(NodeID(i as u32), edge_type, NodeID((i + 1) as u32), Attrs::new()).unwrap();
                    edges += 1;
                }
                let down = i + columns;
                if row + 1 < nodes.div_ceil(columns) && down < nodes {
                    graph.insert_edge(NodeID(i as u32), edge_type, NodeID(down as u32), Attrs::new()).unwrap();
                    edges += 1;
                }
            }
        }
    }
    (graph, edges)
}

fn set_writes(graph: &mut TypedGraph, marker: Sym, writes: usize, value: i64, nodes: usize) {
    for j in 0..writes {
        let id = if writes == 1 { nodes / 2 } else { (j * nodes / writes).min(nodes - 1) };
        graph.set_node_attr(NodeID(id as u32), marker, Value::Int(value + j as i64));
    }
}

fn run(nodes: usize, topology: Topology, repeats: usize) -> Row {
    let node_type = Sym(1);
    let edge_type = Sym(2);
    let marker = Sym(3);
    let (base, edges) = build_graph(nodes, topology);
    let query_id = NodeID(match topology { Topology::Star => 0, _ => (nodes / 2) as u32 });
    let write_count = ((nodes + 99) / 100).max(1);
    let mut eager_clone = Vec::new();
    let mut shared_clone = Vec::new();
    let mut eager_one = Vec::new();
    let mut shared_one = Vec::new();
    let mut eager_sparse = Vec::new();
    let mut shared_sparse = Vec::new();
    let mut exact = true;

    for i in 0..repeats {
        // Alternate ordering within each measured block to reduce drift bias.
        if i % 2 == 0 {
            let t = Instant::now(); let eager = base.clone_eager(); eager_clone.push(micros(t));
            let t = Instant::now(); let shared = base.clone_sharing_slabs(); shared_clone.push(micros(t));
            black_box((eager.node_count(), shared.edge_count()));

            let t = Instant::now(); let mut branch = base.clone_eager();
            set_writes(&mut branch, marker, 1, i as i64, nodes); eager_one.push(micros(t));
            let t = Instant::now(); let mut branch = base.clone_sharing_slabs();
            set_writes(&mut branch, marker, 1, i as i64, nodes); shared_one.push(micros(t));

            let t = Instant::now(); let mut branch = base.clone_eager();
            set_writes(&mut branch, marker, write_count, i as i64, nodes); eager_sparse.push(micros(t));
            let t = Instant::now(); let mut branch = base.clone_sharing_slabs();
            set_writes(&mut branch, marker, write_count, i as i64, nodes); shared_sparse.push(micros(t));
        } else {
            let t = Instant::now(); let shared = base.clone_sharing_slabs(); shared_clone.push(micros(t));
            let t = Instant::now(); let eager = base.clone_eager(); eager_clone.push(micros(t));
            black_box((shared.node_count(), eager.edge_count()));

            let t = Instant::now(); let mut branch = base.clone_sharing_slabs();
            set_writes(&mut branch, marker, 1, i as i64, nodes); shared_one.push(micros(t));
            let t = Instant::now(); let mut branch = base.clone_eager();
            set_writes(&mut branch, marker, 1, i as i64, nodes); eager_one.push(micros(t));

            let t = Instant::now(); let mut branch = base.clone_sharing_slabs();
            set_writes(&mut branch, marker, write_count, i as i64, nodes); shared_sparse.push(micros(t));
            let t = Instant::now(); let mut branch = base.clone_eager();
            set_writes(&mut branch, marker, write_count, i as i64, nodes); eager_sparse.push(micros(t));
        }

        // Two sibling branches make divergent writes. Their values and the
        // primary are checked independently after all timed operations.
        let mut eager_a = base.clone_eager();
        let mut eager_b = base.clone_eager();
        let mut shared_a = base.clone_sharing_slabs();
        let mut shared_b = base.clone_sharing_slabs();
        eager_a.set_node_attr(query_id, marker, Value::Int(i as i64));
        eager_b.set_node_attr(query_id, marker, Value::Int(-(i as i64) - 1));
        shared_a.set_node_attr(query_id, marker, Value::Int(i as i64));
        shared_b.set_node_attr(query_id, marker, Value::Int(-(i as i64) - 1));
        let expected_neighbours = match topology {
            Topology::Star if query_id == NodeID(0) => (1..nodes).map(|n| NodeID(n as u32)).collect(),
            Topology::Star => Vec::new(),
            _ => base.neighbours(query_id, Some(edge_type)),
        };
        exact &= base.node_count() == nodes && base.edge_count() == edges
            && eager_a.nodes_of_type(node_type) == shared_a.nodes_of_type(node_type)
            && eager_a.neighbours(query_id, Some(edge_type)) == expected_neighbours
            && shared_a.neighbours(query_id, Some(edge_type)) == expected_neighbours
            && eager_a.node(query_id).attrs.get(&marker) == shared_a.node(query_id).attrs.get(&marker)
            && eager_a.node(query_id).attrs.get(&marker) != eager_b.node(query_id).attrs.get(&marker)
            && shared_a.node(query_id).attrs.get(&marker) != shared_b.node(query_id).attrs.get(&marker)
            && base.node(query_id).attrs.get(&marker).is_none();
        black_box((&eager_a, &eager_b, &shared_a, &shared_b));
    }
    Row { nodes, topology: topology.name(), edges, repeats,
        eager_clone_us: median(eager_clone), shared_slab_clone_us: median(shared_clone),
        eager_clone_one_write_us: median(eager_one), shared_slab_clone_one_write_us: median(shared_one),
        eager_clone_one_percent_writes_us: median(eager_sparse),
        shared_slab_clone_one_percent_writes_us: median(shared_sparse),
        exact_query_and_sibling_isolation: exact }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let sizes = args.get(1).map(|s| s.split(',').map(|v| v.parse::<usize>().unwrap()).collect::<Vec<_>>())
        .unwrap_or_else(|| vec![771, 1771, 10771, 50771]);
    let repeats = args.get(2).map(|s| s.parse::<usize>().unwrap()).unwrap_or(25);
    let topologies = [Topology::Path, Topology::Star, Topology::Grid];
    let rows: Vec<_> = sizes.into_iter().flat_map(|n| topologies.into_iter().map(move |t| run(n, t, repeats))).collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
