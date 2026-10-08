use serde_json::{json, Value};
use std::time::Instant;
use substrate_rs::checker::ConsistencyChecker;
use substrate_rs::grammar::Grammar;
use substrate_rs::jsonio::term_from_json;
use substrate_rs::reflect::term_to_subgraph;
use substrate_rs::substrate::Substrate;

fn term_json() -> Value {
    json!({"type":"Cat","items":[
        {"type":"Lit","value":"left"},
        {"type":"Reverse","seq":{"type":"Var","name":"x"}}
    ]})
}
fn fresh() -> Substrate {
    Substrate::new(ConsistencyChecker::new(Grammar::default()))
}
fn run(safe: bool) -> Value {
    let mut sub = fresh();
    let initial_graph = sub.graph.node_count();
    let initial_arena = sub.terms.len();
    let mut checkpoints = Vec::new();
    let start = Instant::now();
    for cycle in 1..=1_000 {
        let idx = term_from_json(&term_json(), &mut sub.terms, &mut sub.interner).unwrap();
        let root = term_to_subgraph(&sub.terms, idx, &mut sub.graph, &mut sub.interner);
        if safe {
            sub.remove_term_subgraph(root).unwrap();
        } else {
            sub.remove_node(root);
        }
        if [1, 10, 100, 1_000].contains(&cycle) {
            checkpoints.push(json!({
                "cycles": cycle,
                "arena_nodes": sub.terms.len(),
                "arena_delta": sub.terms.len() - initial_arena,
                "graph_nodes": sub.graph.node_count(),
                "graph_delta": sub.graph.node_count() - initial_graph,
                "elapsed_ns": start.elapsed().as_nanos()
            }));
        }
    }
    json!({"mode":if safe {"ownership_cleanup"} else {"root_only_control"},
           "initial_graph_nodes":initial_graph,"initial_arena_nodes":initial_arena,
           "checkpoints":checkpoints})
}
fn main() {
    println!(
        "{}",
        json!({"schema_version":1,"run_id":"term-arena-growth-20260925-v1",
        "term":term_json(),"results":[run(true),run(false)],
        "claim_boundary":"fixed four-node Term; arena length is logical node count, not RSS or allocated capacity"})
    );
}
