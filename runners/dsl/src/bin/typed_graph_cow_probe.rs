use serde::Serialize;
use std::hint::black_box;
use std::time::Instant;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Serialize)]
struct Row {
    nodes: usize,
    edges: usize,
    repeats: usize,
    eager_clone_us: f64,
    shared_slab_clone_us: f64,
    eager_clone_write_us: f64,
    shared_slab_clone_write_us: f64,
    exact_query_and_branch_isolation: bool,
}

fn median(mut xs: Vec<f64>) -> f64 {
    xs.sort_by(f64::total_cmp);
    let n = xs.len();
    if n % 2 == 0 { (xs[n / 2 - 1] + xs[n / 2]) / 2.0 } else { xs[n / 2] }
}

fn micros(start: Instant) -> f64 { start.elapsed().as_secs_f64() * 1_000_000.0 }

fn run(nodes: usize, repeats: usize) -> Row {
    let node_type = Sym(1);
    let edge_type = Sym(2);
    let marker = Sym(3);
    let mut base = TypedGraph::new();
    for _ in 0..nodes { base.insert_node(node_type, Attrs::new()); }
    for i in 0..nodes.saturating_sub(1) {
        base.insert_edge(NodeID(i as u32), edge_type, NodeID((i + 1) as u32), Attrs::new()).unwrap();
    }
    let mut eager_clone = Vec::new();
    let mut shared_clone = Vec::new();
    let mut eager_write = Vec::new();
    let mut shared_write = Vec::new();
    let mut exact = true;
    let query_id = NodeID((nodes / 2) as u32);

    for i in 0..repeats {
        let t = Instant::now();
        let eager = base.clone_eager();
        eager_clone.push(micros(t));
        let t = Instant::now();
        let shared = base.clone_sharing_slabs();
        shared_clone.push(micros(t));
        black_box((eager.node_count(), shared.edge_count()));

        let t = Instant::now();
        let mut eager = base.clone_eager();
        eager.set_node_attr(query_id, marker, Value::Int(i as i64));
        eager_write.push(micros(t));
        let t = Instant::now();
        let mut shared = base.clone_sharing_slabs();
        shared.set_node_attr(query_id, marker, Value::Int(i as i64));
        shared_write.push(micros(t));

        exact &= eager.node_count() == shared.node_count()
            && eager.edge_count() == shared.edge_count()
            && eager.nodes_of_type(node_type) == shared.nodes_of_type(node_type)
            && eager.node(query_id).attrs.get(&marker) == shared.node(query_id).attrs.get(&marker)
            && base.node(query_id).attrs.get(&marker).is_none()
            && eager.node(NodeID(0)).attrs.get(&marker).is_none()
            && shared.node(NodeID(0)).attrs.get(&marker).is_none();
        black_box((&eager, &shared));
    }
    Row { nodes, edges: nodes.saturating_sub(1), repeats,
        eager_clone_us: median(eager_clone), shared_slab_clone_us: median(shared_clone),
        eager_clone_write_us: median(eager_write), shared_slab_clone_write_us: median(shared_write),
        exact_query_and_branch_isolation: exact }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let sizes = args.get(1).map(|s| s.split(',').map(|v| v.parse::<usize>().unwrap()).collect::<Vec<_>>())
        .unwrap_or_else(|| vec![771, 1771, 10771, 50771]);
    let repeats = args.get(2).map(|s| s.parse::<usize>().unwrap()).unwrap_or(25);
    let rows: Vec<_> = sizes.into_iter().map(|n| run(n, repeats)).collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
