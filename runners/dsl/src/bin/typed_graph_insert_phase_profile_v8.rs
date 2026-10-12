use serde::Serialize;
use std::time::Instant;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Serialize)]
struct Capture {
    nodes: usize,
    shards: usize,
    repeats: usize,
    fork_ns: Vec<u128>,
    indexed_insert_ns: Vec<u128>,
    indexed_lookup_ns: Vec<u128>,
    noindex_insert_ns: Vec<u128>,
    semantics_pass: bool,
}

fn fixture(nodes: usize, indexed: bool) -> TypedGraph {
    let mut graph = TypedGraph::new();
    for i in 0..nodes {
        let mut attrs = Attrs::new();
        attrs.insert(Sym(3), Value::Int(i as i64));
        graph.insert_node(Sym(1), attrs);
    }
    if indexed {
        graph.declare_attr_index(Sym(1), Sym(3));
    }
    graph
}

fn run<const S: usize>(nodes: usize, repeats: usize) {
    let indexed = fixture(nodes, true);
    let noindex = fixture(nodes, false);
    let mut fork_ns = Vec::with_capacity(repeats);
    let mut indexed_insert_ns = Vec::with_capacity(repeats);
    let mut indexed_lookup_ns = Vec::with_capacity(repeats);
    let mut noindex_insert_ns = Vec::with_capacity(repeats);
    let mut semantics_pass = true;

    for _ in 0..repeats {
        let sibling = indexed.clone_sharing_graph_pages();
        let start = Instant::now();
        let mut branch = indexed.clone_sharing_graph_pages();
        fork_ns.push(start.elapsed().as_nanos());

        let mut attrs = Attrs::new();
        attrs.insert(Sym(3), Value::Int(nodes as i64 + 1_000));
        let start = Instant::now();
        let id = branch.insert_node(Sym(1), attrs);
        indexed_insert_ns.push(start.elapsed().as_nanos());

        let query_value = Value::Int(nodes as i64 + 1_000);
        let start = Instant::now();
        let query_result = branch.nodes_where(Sym(1), Sym(3), &query_value);
        indexed_lookup_ns.push(start.elapsed().as_nanos());
        let mut expected: Vec<NodeID> = (0..nodes).map(|i| NodeID(i as u32)).collect();
        expected.push(NodeID(nodes as u32));
        semantics_pass &= id == NodeID(nodes as u32)
            && query_result == [id]
            && branch.nodes_of_type(Sym(1)) == expected
            && indexed.nodes_of_type(Sym(1)).len() == nodes
            && sibling.nodes_of_type(Sym(1)).len() == nodes
            && indexed.nodes_where(Sym(1), Sym(3), &query_value).is_empty()
            && sibling.nodes_where(Sym(1), Sym(3), &query_value).is_empty();

        let sibling_noindex = noindex.clone_sharing_graph_pages();
        let mut branch_noindex = noindex.clone_sharing_graph_pages();
        let mut attrs = Attrs::new();
        attrs.insert(Sym(3), Value::Int(nodes as i64 + 1_000));
        let start = Instant::now();
        let id_noindex = branch_noindex.insert_node(Sym(1), attrs);
        noindex_insert_ns.push(start.elapsed().as_nanos());
        semantics_pass &= id_noindex == NodeID(nodes as u32)
            && branch_noindex.nodes_of_type(Sym(1)).len() == nodes + 1
            && noindex.nodes_of_type(Sym(1)).len() == nodes
            && sibling_noindex.nodes_of_type(Sym(1)).len() == nodes;
    }
    assert!(
        semantics_pass,
        "insert phase semantic/isolation gate failed"
    );
    let capture = Capture {
        nodes,
        shards: S,
        repeats,
        fork_ns,
        indexed_insert_ns,
        indexed_lookup_ns,
        noindex_insert_ns,
        semantics_pass,
    };
    println!("{}", serde_json::to_string(&capture).unwrap());
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let nodes: usize = args[1].parse().unwrap();
    let repeats: usize = args[2].parse().unwrap_or(41);
    match cfg!(feature = "cow_shards_512") {
        true => run::<512>(nodes, repeats),
        false if cfg!(feature = "cow_shards_256") => run::<256>(nodes, repeats),
        false if cfg!(feature = "cow_shards_128") => run::<128>(nodes, repeats),
        _ => run::<64>(nodes, repeats),
    }
}
