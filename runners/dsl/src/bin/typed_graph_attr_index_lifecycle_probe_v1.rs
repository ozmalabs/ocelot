use serde::Serialize;
use std::hint::black_box;
use std::time::Instant;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::persist::{graph_from_value, graph_to_value};
use substrate_rs::sym::{Interner, Sym};
use substrate_rs::value::Value;

#[derive(Serialize)]
struct Row {
    nodes: usize,
    cardinality: usize,
    selected_fraction: f64,
    index_build_ns: u128,
    indexed_query_median_ns: u128,
    scan_query_median_ns: u128,
    indexed_queries: usize,
    scan_queries: usize,
    mutation_count: usize,
    indexed_mutation_ns: u128,
    scan_mutation_ns: u128,
    unindexed_graph_fork_median_ns: u128,
    graph_fork_median_ns: u128,
    graph_serialize_ns: u128,
    graph_restore_ns: u128,
    index_redeclare_ns: u128,
    fork_query_rows: usize,
    queries_match: bool,
    mutation_parity: bool,
    restored_graph_matches: bool,
    restored_index_matches: bool,
}

const NODE_TYPE: Sym = Sym(1);
const ATTR: Sym = Sym(3);

fn build(nodes: usize, cardinality: usize) -> TypedGraph {
    let mut graph = TypedGraph::new();
    for i in 0..nodes {
        let mut attrs = Attrs::new();
        attrs.insert(ATTR, Value::Int((i % cardinality) as i64));
        graph.insert_node(NODE_TYPE, attrs);
    }
    graph
}

fn scan(graph: &TypedGraph, value: &Value) -> Vec<NodeID> {
    graph
        .nodes_of_type(NODE_TYPE)
        .into_iter()
        .filter(|nid| graph.node(*nid).attrs.get(&ATTR) == Some(value))
        .collect()
}

fn median_ns<F: FnMut()>(repeats: usize, mut f: F) -> u128 {
    let mut samples = Vec::with_capacity(repeats);
    for _ in 0..repeats {
        let t = Instant::now();
        f();
        samples.push(t.elapsed().as_nanos());
    }
    samples.sort_unstable();
    samples[samples.len() / 2]
}

fn run(nodes: usize, cardinality: usize, repeats: usize, queries: usize) -> Row {
    let graph = build(nodes, cardinality);
    let query_value = Value::Int(0);
    let expected = scan(&graph, &query_value);
    let mut indexed = graph.clone();
    let started = Instant::now();
    indexed.declare_attr_index(NODE_TYPE, ATTR);
    let index_build_ns = started.elapsed().as_nanos();
    let indexed_result = indexed.nodes_where(NODE_TYPE, ATTR, &query_value);
    let queries_match = indexed_result == expected;
    let indexed_query_median_ns = median_ns(repeats, || {
        for _ in 0..queries {
            black_box(indexed.nodes_where(NODE_TYPE, ATTR, &query_value));
        }
    });
    let scan_query_median_ns = median_ns(repeats, || {
        for _ in 0..queries {
            black_box(scan(&graph, &query_value));
        }
    });

    let mutation_count = (nodes / 100).max(1).min(1000);
    let mut indexed_mut = indexed.clone();
    let mut scan_mut = graph.clone();
    let started = Instant::now();
    for i in 0..mutation_count {
        indexed_mut.set_node_attr(NodeID(i as u32), ATTR, Value::Int(-1));
    }
    let indexed_mutation_ns = started.elapsed().as_nanos();
    let started = Instant::now();
    for i in 0..mutation_count {
        scan_mut.set_node_attr(NodeID(i as u32), ATTR, Value::Int(-1));
    }
    let scan_mutation_ns = started.elapsed().as_nanos();
    let mutation_parity = indexed_mut.nodes_where(NODE_TYPE, ATTR, &query_value)
        == scan(&scan_mut, &query_value)
        && indexed_mut.nodes_where(NODE_TYPE, ATTR, &Value::Int(-1))
            == scan(&scan_mut, &Value::Int(-1));

    let graph_fork_median_ns = median_ns(repeats, || {
        black_box(indexed.clone_sharing_graph_pages());
    });
    let unindexed_graph_fork_median_ns = median_ns(repeats, || {
        black_box(graph.clone_sharing_graph_pages());
    });
    let fork_query_rows = indexed
        .clone_sharing_graph_pages()
        .nodes_where(NODE_TYPE, ATTR, &query_value)
        .len();

    let mut interner = Interner::new();
    // Use a stable named-symbol mapping for the persistence path.
    let mut persist_graph = TypedGraph::new();
    let p_type = interner.intern("IndexedNode");
    let p_attr = interner.intern("bucket");
    for i in 0..nodes {
        let mut attrs = Attrs::new();
        attrs.insert(p_attr, Value::Int((i % cardinality) as i64));
        persist_graph.insert_node(p_type, attrs);
    }
    persist_graph.declare_attr_index(p_type, p_attr);
    let started = Instant::now();
    let serialized = graph_to_value(&persist_graph, &interner);
    let graph_serialize_ns = started.elapsed().as_nanos();
    let mut restored_interner = Interner::new();
    let started = Instant::now();
    let mut restored = graph_from_value(&serialized, &mut restored_interner).unwrap();
    let graph_restore_ns = started.elapsed().as_nanos();
    let restored_graph_matches = restored.node_count() == nodes
        && graph_to_value(&restored, &restored_interner) == serialized;
    let restored_type = restored_interner.intern("IndexedNode");
    let restored_attr = restored_interner.intern("bucket");
    let started = Instant::now();
    restored.declare_attr_index(restored_type, restored_attr);
    let index_redeclare_ns = started.elapsed().as_nanos();
    let restored_index_matches =
        restored.nodes_where(restored_type, restored_attr, &query_value) == expected;
    Row {
        nodes,
        cardinality,
        selected_fraction: 1.0 / cardinality as f64,
        index_build_ns,
        indexed_query_median_ns,
        scan_query_median_ns,
        indexed_queries: queries,
        scan_queries: queries,
        mutation_count,
        indexed_mutation_ns,
        scan_mutation_ns,
        unindexed_graph_fork_median_ns,
        graph_fork_median_ns,
        graph_serialize_ns,
        graph_restore_ns,
        index_redeclare_ns,
        fork_query_rows,
        queries_match,
        mutation_parity,
        restored_graph_matches,
        restored_index_matches,
    }
}

fn main() {
    let args = std::env::args().collect::<Vec<_>>();
    let sizes = args
        .get(1)
        .map(|s| {
            s.split(',')
                .map(|v| v.parse().unwrap())
                .collect::<Vec<usize>>()
        })
        .unwrap_or_else(|| vec![1000, 10000, 50000]);
    let repeats = args.get(2).map(|s| s.parse().unwrap()).unwrap_or(7);
    let queries = args.get(3).map(|s| s.parse().unwrap()).unwrap_or(25);
    let rows = sizes
        .into_iter()
        .flat_map(|n| {
            [8, 128, 1024]
                .into_iter()
                .map(move |c| run(n, c.min(n), repeats, queries))
        })
        .collect::<Vec<_>>();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
