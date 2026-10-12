use serde::Serialize;
use std::time::Instant;
use substrate_rs::graph::{Attrs, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Serialize)]
struct Samples {
    name: &'static str,
    shared_fork_ns: Vec<u128>,
    eager_fork_ns: Vec<u128>,
    shared_write_ns: Vec<u128>,
    eager_write_ns: Vec<u128>,
    shared_insert_op_ns: Vec<u128>,
    shared_insert_lookup_ns: Vec<u128>,
    eager_insert_op_ns: Vec<u128>,
    eager_insert_lookup_ns: Vec<u128>,
    shared_semantics: Vec<bool>,
    eager_semantics: Vec<bool>,
    shared_order_semantics: Vec<bool>,
    eager_order_semantics: Vec<bool>,
}

#[derive(Serialize)]
struct Cell {
    nodes: usize,
    distinct_values: usize,
    repeats: usize,
    baseline_queries_exact: bool,
    baseline_type_order_exact: bool,
    query_sweep_ns: Vec<u128>,
    fixture_rss_kb: u64,
    post_run_rss_kb: u64,
    hwm_kb: u64,
    mutation_samples: Vec<Samples>,
}

#[derive(Serialize)]
struct Capture {
    schema: &'static str,
    cells: Vec<Cell>,
    reuse_compaction_controls_pass: bool,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Mutation {
    SetAttr,
    Insert,
    Delete,
    Retype,
}

impl Mutation {
    fn name(self) -> &'static str {
        match self {
            Self::SetAttr => "set_attr",
            Self::Insert => "insert",
            Self::Delete => "delete",
            Self::Retype => "retype",
        }
    }
}

fn fixture(nodes: usize) -> TypedGraph {
    let mut graph = TypedGraph::new();
    for i in 0..nodes {
        let mut attrs = Attrs::new();
        attrs.insert(Sym(3), Value::Int(i as i64));
        graph.insert_node(Sym(1), attrs);
    }
    graph.declare_attr_index(Sym(1), Sym(3));
    graph
}

fn rss_kb() -> (u64, u64) {
    let status = std::fs::read_to_string("/proc/self/status").unwrap_or_default();
    let value = |name: &str| -> u64 {
        status
            .lines()
            .find(|line| line.starts_with(name))
            .and_then(|line| line.split_whitespace().nth(1))
            .and_then(|v| v.parse().ok())
            .unwrap_or(0)
    };
    (value("VmRSS:"), value("VmHWM:"))
}

fn apply(
    graph: &mut TypedGraph,
    mutation: Mutation,
    nodes: usize,
) -> (u32, bool, Option<(u128, u128)>) {
    match mutation {
        Mutation::SetAttr => {
            graph.set_node_attr(NodeID(0), Sym(3), Value::Int(nodes as i64 + 100));
            (
                0,
                graph.nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 + 100)) == [NodeID(0)]
                    && graph.nodes_where(Sym(1), Sym(3), &Value::Int(0)).is_empty(),
                None,
            )
        }
        Mutation::Insert => {
            let mut attrs = Attrs::new();
            attrs.insert(Sym(3), Value::Int(nodes as i64 + 1_000));
            let operation_start = Instant::now();
            let id = graph.insert_node(Sym(1), attrs);
            let operation_ns = operation_start.elapsed().as_nanos();
            let lookup_start = Instant::now();
            let found = graph.nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 + 1_000));
            let lookup_ns = lookup_start.elapsed().as_nanos();
            (id.0, found == [id], Some((operation_ns, lookup_ns)))
        }
        Mutation::Delete => {
            let id = NodeID((nodes - 1) as u32);
            let deleted = graph.delete_node(id).is_some();
            (
                id.0,
                deleted
                    && graph
                        .nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 - 1))
                        .is_empty(),
                None,
            )
        }
        Mutation::Retype => {
            let id = NodeID((nodes - 2) as u32);
            graph.set_node_type(id, Sym(4));
            let other_nodes = graph.nodes_of_type(Sym(4));
            (
                id.0,
                other_nodes.contains(&id)
                    && graph
                        .nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 - 2))
                        .is_empty(),
                None,
            )
        }
    }
}

fn type_order_ok(graph: &TypedGraph, mutation: Mutation, id: u32, nodes: usize) -> bool {
    let mut expected: Vec<NodeID> = (0..nodes).map(|i| NodeID(i as u32)).collect();
    match mutation {
        Mutation::SetAttr => {}
        Mutation::Insert => expected.push(NodeID(id)),
        Mutation::Delete | Mutation::Retype => expected.retain(|candidate| candidate.0 != id),
    }
    graph.nodes_of_type(Sym(1)) == expected
        && (mutation != Mutation::Retype || graph.nodes_of_type(Sym(4)) == [NodeID(id)])
}

fn isolated(
    parent: &TypedGraph,
    sibling: &TypedGraph,
    mutation: Mutation,
    id: u32,
    nodes: usize,
) -> bool {
    let original_order: Vec<NodeID> = (0..nodes).map(|i| NodeID(i as u32)).collect();
    if parent.nodes_of_type(Sym(1)) != original_order
        || sibling.nodes_of_type(Sym(1)) != original_order
        || !parent.nodes_of_type(Sym(4)).is_empty()
        || !sibling.nodes_of_type(Sym(4)).is_empty()
    {
        return false;
    }
    match mutation {
        Mutation::SetAttr => {
            parent.nodes_where(Sym(1), Sym(3), &Value::Int(0)) == [NodeID(0)]
                && sibling.nodes_where(Sym(1), Sym(3), &Value::Int(0)) == [NodeID(0)]
                && parent
                    .nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 + 100))
                    .is_empty()
                && sibling
                    .nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 + 100))
                    .is_empty()
        }
        Mutation::Insert => {
            parent
                .nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 + 1_000))
                .is_empty()
                && sibling
                    .nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 + 1_000))
                    .is_empty()
                && id == nodes as u32
        }
        Mutation::Delete => {
            parent.nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 - 1)) == [NodeID(id)]
                && sibling.nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 - 1))
                    == [NodeID(id)]
        }
        Mutation::Retype => {
            parent.nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 - 2)) == [NodeID(id)]
                && sibling.nodes_where(Sym(1), Sym(3), &Value::Int(nodes as i64 - 2))
                    == [NodeID(id)]
        }
    }
}

fn reuse_compaction_control() -> bool {
    let parent = fixture(128);
    let mut branch = parent.clone_sharing_graph_pages();
    let sibling = parent.clone_sharing_graph_pages();
    let original: Vec<NodeID> = (0..128).map(NodeID).collect();
    for i in 0..64 {
        if branch.delete_node(NodeID(i)).is_none() {
            return false;
        }
    }
    let mut expected: Vec<NodeID> = (64..128).map(NodeID).collect();
    if branch.nodes_of_type(Sym(1)) != expected {
        return false;
    }
    if branch.delete_node(NodeID(100)).is_none() {
        return false;
    }
    expected.retain(|node| node.0 != 100);
    if branch.nodes_of_type(Sym(1)) != expected {
        return false;
    }
    let mut reused = Vec::new();
    for i in 0..65 {
        let mut attrs = Attrs::new();
        attrs.insert(Sym(3), Value::Int(1_000 + i));
        let id = branch.insert_node(Sym(1), attrs);
        reused.push(id);
        expected.push(id);
        if branch.nodes_where(Sym(1), Sym(3), &Value::Int(1_000 + i)) != [id] {
            return false;
        }
    }
    if reused
        != [NodeID(100)]
            .into_iter()
            .chain((0..64).rev().map(NodeID))
            .collect::<Vec<_>>()
        || branch.nodes_of_type(Sym(1)) != expected
    {
        return false;
    }
    let mut replacement = Attrs::new();
    replacement.insert(Sym(3), Value::Int(7_777));
    branch.restore_node(NodeID(70), Sym(4), replacement);
    let mut expected_after_restore = expected;
    expected_after_restore.retain(|node| *node != NodeID(70));
    branch.nodes_of_type(Sym(4)) == [NodeID(70)]
        && branch.nodes_of_type(Sym(1)) == expected_after_restore
        && branch
            .nodes_where(Sym(1), Sym(3), &Value::Int(70))
            .is_empty()
        && parent.nodes_of_type(Sym(1)) == original
        && sibling.nodes_of_type(Sym(1)) == original
        && parent.nodes_where(Sym(1), Sym(3), &Value::Int(70)) == [NodeID(70)]
        && sibling.nodes_where(Sym(1), Sym(3), &Value::Int(70)) == [NodeID(70)]
}

fn run_cell(nodes: usize, repeats: usize) -> Cell {
    let graph = fixture(nodes);
    let fixture_rss_kb = rss_kb().0;
    let baseline_queries_exact = (0..nodes)
        .all(|i| graph.nodes_where(Sym(1), Sym(3), &Value::Int(i as i64)) == [NodeID(i as u32)]);
    let mut query_sweep_ns = Vec::with_capacity(7);
    for _ in 0..7 {
        let start = Instant::now();
        let exact = (0..nodes).all(|i| {
            graph.nodes_where(Sym(1), Sym(3), &Value::Int(i as i64)) == [NodeID(i as u32)]
        });
        query_sweep_ns.push(start.elapsed().as_nanos());
        assert!(exact, "full exact query sweep failed");
    }
    let mutations = [
        Mutation::SetAttr,
        Mutation::Insert,
        Mutation::Delete,
        Mutation::Retype,
    ];
    let mut rows: Vec<Samples> = mutations
        .iter()
        .map(|m| Samples {
            name: m.name(),
            shared_fork_ns: Vec::with_capacity(repeats),
            eager_fork_ns: Vec::with_capacity(repeats),
            shared_write_ns: Vec::with_capacity(repeats),
            eager_write_ns: Vec::with_capacity(repeats),
            shared_insert_op_ns: Vec::with_capacity(repeats),
            shared_insert_lookup_ns: Vec::with_capacity(repeats),
            eager_insert_op_ns: Vec::with_capacity(repeats),
            eager_insert_lookup_ns: Vec::with_capacity(repeats),
            shared_semantics: Vec::with_capacity(repeats),
            eager_semantics: Vec::with_capacity(repeats),
            shared_order_semantics: Vec::with_capacity(repeats),
            eager_order_semantics: Vec::with_capacity(repeats),
        })
        .collect();
    for rep in 0..repeats {
        for (idx, mutation) in mutations.iter().copied().enumerate() {
            let row = &mut rows[idx];
            let sibling = graph.clone_sharing_graph_pages();
            if rep % 2 == 0 {
                let start = Instant::now();
                let mut shared = graph.clone_sharing_graph_pages();
                row.shared_fork_ns.push(start.elapsed().as_nanos());
                let start = Instant::now();
                let (id, local_ok, insert_phases) = apply(&mut shared, mutation, nodes);
                row.shared_write_ns.push(start.elapsed().as_nanos());
                if let Some((operation_ns, lookup_ns)) = insert_phases {
                    row.shared_insert_op_ns.push(operation_ns);
                    row.shared_insert_lookup_ns.push(lookup_ns);
                }
                row.shared_semantics
                    .push(local_ok && isolated(&graph, &sibling, mutation, id, nodes));
                row.shared_order_semantics
                    .push(type_order_ok(&shared, mutation, id, nodes));

                let start = Instant::now();
                let mut eager = graph.clone_eager();
                row.eager_fork_ns.push(start.elapsed().as_nanos());
                let start = Instant::now();
                let (id, local_ok, insert_phases) = apply(&mut eager, mutation, nodes);
                row.eager_write_ns.push(start.elapsed().as_nanos());
                if let Some((operation_ns, lookup_ns)) = insert_phases {
                    row.eager_insert_op_ns.push(operation_ns);
                    row.eager_insert_lookup_ns.push(lookup_ns);
                }
                row.eager_semantics
                    .push(local_ok && isolated(&graph, &sibling, mutation, id, nodes));
                row.eager_order_semantics
                    .push(type_order_ok(&eager, mutation, id, nodes));
            } else {
                let start = Instant::now();
                let mut eager = graph.clone_eager();
                row.eager_fork_ns.push(start.elapsed().as_nanos());
                let start = Instant::now();
                let (id, local_ok, insert_phases) = apply(&mut eager, mutation, nodes);
                row.eager_write_ns.push(start.elapsed().as_nanos());
                if let Some((operation_ns, lookup_ns)) = insert_phases {
                    row.eager_insert_op_ns.push(operation_ns);
                    row.eager_insert_lookup_ns.push(lookup_ns);
                }
                row.eager_semantics
                    .push(local_ok && isolated(&graph, &sibling, mutation, id, nodes));
                row.eager_order_semantics
                    .push(type_order_ok(&eager, mutation, id, nodes));

                let start = Instant::now();
                let mut shared = graph.clone_sharing_graph_pages();
                row.shared_fork_ns.push(start.elapsed().as_nanos());
                let start = Instant::now();
                let (id, local_ok, insert_phases) = apply(&mut shared, mutation, nodes);
                row.shared_write_ns.push(start.elapsed().as_nanos());
                if let Some((operation_ns, lookup_ns)) = insert_phases {
                    row.shared_insert_op_ns.push(operation_ns);
                    row.shared_insert_lookup_ns.push(lookup_ns);
                }
                row.shared_semantics
                    .push(local_ok && isolated(&graph, &sibling, mutation, id, nodes));
                row.shared_order_semantics
                    .push(type_order_ok(&shared, mutation, id, nodes));
            }
        }
    }
    let baseline_type_order_exact =
        graph.nodes_of_type(Sym(1)) == (0..nodes).map(|i| NodeID(i as u32)).collect::<Vec<_>>();
    let (post_run_rss_kb, hwm_kb) = rss_kb();
    Cell {
        nodes,
        distinct_values: nodes,
        repeats,
        baseline_queries_exact,
        baseline_type_order_exact,
        query_sweep_ns,
        fixture_rss_kb,
        post_run_rss_kb,
        hwm_kb,
        mutation_samples: rows,
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
        .unwrap_or_else(|| vec![7_164, 16_384, 50_771]);
    let repeats = args.get(2).map(|s| s.parse().unwrap()).unwrap_or(21);
    let reuse_compaction_controls_pass = reuse_compaction_control();
    let capture = Capture {
        schema: "TypedGraphCowInsertScheduleProfileV9",
        cells: sizes.into_iter().map(|n| run_cell(n, repeats)).collect(),
        reuse_compaction_controls_pass,
    };
    println!("{}", serde_json::to_string(&capture).unwrap());
}
