use serde::Serialize;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Serialize)]
struct Row {
    nodes: usize,
    distinct_values: usize,
    repeats: usize,
    attr_index: ProfileRow,
    queries_exact: bool,
}

#[derive(Serialize)]
struct ProfileRow {
    entries: usize,
    median_shared_fork_ns: u128,
    median_eager_clone_ns: u128,
}

fn run(nodes: usize, repeats: usize) -> Row {
    let mut graph = TypedGraph::new();
    for i in 0..nodes {
        let mut attrs = Attrs::new();
        attrs.insert(Sym(3), Value::Int(i as i64));
        graph.insert_node(Sym(1), attrs);
    }
    graph.declare_attr_index(Sym(1), Sym(3));
    let queries_exact = graph.nodes_of_type(Sym(1)).len() == nodes
        && (0..nodes).all(|i| {
            graph.nodes_where(Sym(1), Sym(3), &Value::Int(i as i64)) == [NodeID(i as u32)]
        });
    let attr_index = graph
        .profile_index_clone_cost(repeats)
        .into_iter()
        .find(|row| row.component == "attr_indices")
        .expect("attribute-index profile row");
    Row {
        nodes,
        distinct_values: nodes,
        repeats,
        attr_index: ProfileRow {
            entries: attr_index.entries,
            median_shared_fork_ns: attr_index.median_shared_fork_ns,
            median_eager_clone_ns: attr_index.median_eager_clone_ns,
        },
        queries_exact,
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let sizes = args
        .get(1)
        .map(|s| s.split(',').map(|v| v.parse::<usize>().unwrap()).collect::<Vec<_>>())
        .unwrap_or_else(|| vec![7_164, 16_384, 50_771]);
    let repeats = args.get(2).map(|s| s.parse().unwrap()).unwrap_or(51);
    let rows: Vec<_> = sizes.into_iter().map(|n| run(n, repeats)).collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
