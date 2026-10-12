use serde::Serialize;
use substrate_rs::graph::{Attrs, GraphIndexCloneCost, GraphIndexReadCost, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Clone, Copy)]
enum Topology {
    Path,
    Star,
}
impl Topology {
    fn name(self) -> &'static str {
        match self {
            Self::Path => "path",
            Self::Star => "star",
        }
    }
}

#[derive(Serialize)]
struct ComponentRow {
    component: &'static str,
    entries: usize,
    median_shared_fork_ns: u128,
    median_eager_clone_ns: u128,
}

#[derive(Serialize)]
struct Row {
    nodes: usize,
    topology: &'static str,
    edges: usize,
    repeats: usize,
    components: Vec<ComponentRow>,
    read_costs: Vec<ReadRow>,
    exact_index_queries: bool,
}

#[derive(Serialize)]
struct ReadRow {
    component: &'static str,
    lookups: usize,
    cow_sharded_median_ns_per_lookup: f64,
    fx_hash_median_ns_per_lookup: f64,
    checksums_match: bool,
}

fn build(nodes: usize, topology: Topology) -> (TypedGraph, usize) {
    let mut graph = TypedGraph::new();
    for i in 0..nodes {
        let mut attrs = Attrs::new();
        attrs.insert(Sym(3), Value::Int((i % 128) as i64));
        graph.insert_node(Sym(1), attrs);
    }
    let mut edges = 0;
    match topology {
        Topology::Path => {
            for i in 0..nodes.saturating_sub(1) {
                let mut attrs = Attrs::new();
                if i % 16 == 0 {
                    attrs.insert(Sym(5), Value::Int((i % 8) as i64));
                }
                graph
                    .insert_edge(
                        NodeID(i as u32),
                        Sym(2 + (i % 4) as u32),
                        NodeID((i + 1) as u32),
                        attrs,
                    )
                    .unwrap();
                edges += 1;
            }
        }
        Topology::Star => {
            for i in 1..nodes {
                let mut attrs = Attrs::new();
                if i % 16 == 0 {
                    attrs.insert(Sym(5), Value::Int((i % 8) as i64));
                }
                graph
                    .insert_edge(NodeID(0), Sym(2 + (i % 4) as u32), NodeID(i as u32), attrs)
                    .unwrap();
                edges += 1;
            }
        }
    }
    graph.declare_attr_index(Sym(1), Sym(3));
    (graph, edges)
}

fn summarize(profile: Vec<GraphIndexCloneCost>) -> Vec<ComponentRow> {
    profile
        .into_iter()
        .map(|row| ComponentRow {
            component: row.component,
            entries: row.entries,
            median_shared_fork_ns: row.median_shared_fork_ns,
            median_eager_clone_ns: row.median_eager_clone_ns,
        })
        .collect()
}

fn summarize_reads(profile: Vec<GraphIndexReadCost>) -> Vec<ReadRow> {
    profile
        .into_iter()
        .map(|row| ReadRow {
            component: row.component,
            lookups: row.lookups,
            cow_sharded_median_ns_per_lookup: row.cow_sharded_median_ns_per_lookup,
            fx_hash_median_ns_per_lookup: row.fx_hash_median_ns_per_lookup,
            checksums_match: row.checksums_match,
        })
        .collect()
}

fn run(nodes: usize, topology: Topology, repeats: usize) -> Row {
    let (graph, edges) = build(nodes, topology);
    let profile = graph.profile_index_clone_cost(repeats);
    let read_costs = graph.profile_typed_adjacency_read_cost(100_000, repeats);
    let exact_index_queries = graph.nodes_of_type(Sym(1)).len() == nodes
        && graph.nodes_where(Sym(1), Sym(3), &Value::Int(0)).len() == nodes.div_ceil(128)
        && graph.edges_by_type(Sym(2)).len()
            + graph.edges_by_type(Sym(3)).len()
            + graph.edges_by_type(Sym(4)).len()
            + graph.edges_by_type(Sym(5)).len()
            == edges;
    Row {
        nodes,
        topology: topology.name(),
        edges,
        repeats,
        components: summarize(profile),
        read_costs: summarize_reads(read_costs),
        exact_index_queries,
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
        .unwrap_or_else(|| vec![771, 10_771, 50_771]);
    let repeats = args
        .get(2)
        .map(|s| s.parse::<usize>().unwrap())
        .unwrap_or(25);
    let rows: Vec<_> = sizes
        .into_iter()
        .flat_map(|n| {
            [Topology::Path, Topology::Star]
                .into_iter()
                .map(move |topology| run(n, topology, repeats))
        })
        .collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
