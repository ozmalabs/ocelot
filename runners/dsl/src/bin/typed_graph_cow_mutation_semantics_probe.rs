use serde::Serialize;
use substrate_rs::graph::{Attrs, EdgeIdx, NodeID, TypedGraph};
use substrate_rs::sym::Sym;
use substrate_rs::value::Value;

#[derive(Clone, Copy)]
enum Backend {
    Eager,
    SharedRecords,
    SharedGraphPages,
}
impl Backend {
    const ALL: [Self; 3] = [Self::Eager, Self::SharedRecords, Self::SharedGraphPages];
    fn name(self) -> &'static str {
        match self {
            Self::Eager => "eager",
            Self::SharedRecords => "shared_records",
            Self::SharedGraphPages => "shared_graph_pages",
        }
    }
    fn fork(self, graph: &TypedGraph) -> TypedGraph {
        match self {
            Self::Eager => graph.clone_eager(),
            Self::SharedRecords => graph.clone_sharing_slabs(),
            Self::SharedGraphPages => graph.clone_sharing_graph_pages(),
        }
    }
}

#[derive(Serialize)]
struct Row {
    nodes: usize,
    backend: &'static str,
    primary_unchanged: bool,
    fork_state_matches_eager: bool,
    nested_fork_matches_eager: bool,
    sibling_isolation: bool,
    delete_append_id_reuse: bool,
}

fn graph(nodes: usize) -> TypedGraph {
    let mut g = TypedGraph::new();
    for i in 0..nodes {
        let mut a = Attrs::new();
        a.insert(Sym(3), Value::Int(i as i64));
        g.insert_node(Sym(1), a);
    }
    for i in 0..nodes.saturating_sub(1) {
        g.insert_edge(
            NodeID(i as u32),
            Sym(2),
            NodeID((i + 1) as u32),
            Attrs::new(),
        )
        .unwrap();
    }
    g
}

fn signature(g: &TypedGraph) -> String {
    let mut rows = Vec::new();
    for nid in g.all_nodes() {
        let n = g.node(nid);
        let mut edges = Vec::new();
        for et in [Sym(2), Sym(5)] {
            for idx in g.out_edges_idx(nid, Some(et)) {
                let e = g.edge(idx);
                edges.push(format!(
                    "{}:{}:{}:{:?}",
                    e.src.0,
                    e.edge_type.0,
                    e.tgt.0,
                    g.edge_attrs(idx)
                ));
            }
        }
        rows.push(format!(
            "n{}:{}:{:?}:{}",
            nid.0,
            n.type_.0,
            n.attrs,
            edges.join(",")
        ));
    }
    rows.join("|")
}

fn mutate(g: &mut TypedGraph) -> bool {
    let changed = NodeID(20);
    let deleted = NodeID(30);
    g.set_node_attr(changed, Sym(3), Value::Int(-20));
    g.set_node_attr(changed, Sym(4), Value::Bool(true));
    g.remove_node_attr(NodeID(21), Sym(4));
    g.set_node_type(NodeID(22), Sym(4));
    let edge = g.edge_idx(NodeID(10), Sym(2), NodeID(11)).unwrap();
    g.delete_edge(edge);
    let ok = g.delete_node(deleted).is_some();
    let recycled = g.insert_node(Sym(1), Attrs::new());
    let edge_ok = g
        .insert_edge(recycled, Sym(5), NodeID(40), Attrs::new())
        .is_ok();
    ok && edge_ok && recycled == deleted && !g.has_edge(NodeID(29), Sym(2), deleted)
}

fn run(nodes: usize) -> Vec<Row> {
    let base = graph(nodes);
    let base_state = signature(&base);
    let mut forks: Vec<TypedGraph> = Backend::ALL
        .iter()
        .map(|b| {
            let mut x = b.fork(&base);
            assert!(mutate(&mut x));
            x
        })
        .collect();
    let eager = signature(&forks[0]);
    let eager_nodes_1 = forks[0].node_count();
    let eager_edges_1 = forks[0].edge_count();
    let mut out = Vec::new();
    for (ix, backend) in Backend::ALL.iter().copied().enumerate() {
        let fork_state_matches_eager = signature(&forks[ix]) == eager
            && forks[ix].node_count() == eager_nodes_1
            && forks[ix].edge_count() == eager_edges_1;
        let primary_unchanged = signature(&base) == base_state;
        let nested_source = &forks[ix];
        let mut nested = backend.fork(nested_source);
        nested.set_node_type(NodeID(40), Sym(6));
        nested
            .insert_edge(NodeID(41), Sym(5), NodeID(42), Attrs::new())
            .unwrap();
        let mut eager_nested = Backend::Eager.fork(&forks[0]);
        eager_nested.set_node_type(NodeID(40), Sym(6));
        eager_nested
            .insert_edge(NodeID(41), Sym(5), NodeID(42), Attrs::new())
            .unwrap();
        let nested_fork_matches_eager = signature(&nested) == signature(&eager_nested);
        let mut sibling = backend.fork(&forks[ix]);
        sibling.set_node_type(NodeID(40), Sym(7));
        let sibling_isolation = signature(&forks[ix]) == eager
            && signature(&base) == base_state
            && signature(&sibling) != eager
            && signature(&nested) == signature(&eager_nested);
        out.push(Row {
            nodes,
            backend: backend.name(),
            primary_unchanged,
            fork_state_matches_eager,
            nested_fork_matches_eager,
            sibling_isolation,
            delete_append_id_reuse: forks[ix].has_node(NodeID(30))
                && forks[ix].node(NodeID(30)).type_ == Sym(1)
                && !forks[ix].has_edge(NodeID(29), Sym(2), NodeID(30)),
        });
    }
    out
}

fn main() {
    let sizes: Vec<usize> = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "771,10771,50771".into())
        .split(',')
        .map(|n| n.parse().unwrap())
        .collect();
    let rows: Vec<Row> = sizes.into_iter().flat_map(run).collect();
    println!("{}", serde_json::to_string(&rows).unwrap());
}
