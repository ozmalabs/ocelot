//! Current-source evaluator for semantic before-image journal coverage.
//! This is an experiment executable, not part of the project test suite.
use serde_json::{json, Value as Json};
use substrate_rs::{graph::{Attrs, EdgeIdx, NodeID, TypedGraph}, persist::{graph_diff, graph_experiment_delta, graph_to_value}, sym::Interner, value::Value};

fn attrs(entries: &[(substrate_rs::sym::Sym, Value)]) -> Attrs {
    let mut out = Attrs::new();
    for (key, value) in entries { out.insert(*key, value.clone()); }
    out
}

fn fixture(interner: &mut Interner) -> (TypedGraph, NodeID, NodeID, NodeID, EdgeIdx, EdgeIdx) {
    let mut graph = TypedGraph::new();
    let label = interner.intern("label");
    let a = graph.insert_node(interner.intern("A"), attrs(&[(label, Value::Str(interner.intern("a")))]));
    let b = graph.insert_node(interner.intern("B"), Attrs::new());
    let c = graph.insert_node(interner.intern("C"), Attrs::new());
    let rel = interner.intern("rel");
    let edge_key = interner.intern("weight");
    let e1 = graph.insert_edge(a, rel, b, attrs(&[(edge_key, Value::Int(1))])).unwrap();
    let e2 = graph.insert_edge(b, rel, c, Attrs::new()).unwrap();
    (graph, a, b, c, e1, e2)
}

fn run_case(name: &str, operation: &str) -> Json {
    let mut interner = Interner::new();
    let (mut graph, a, b, c, e1, e2) = fixture(&mut interner);
    let before = graph_to_value(&graph, &interner);
    graph.begin_experiment_delta_log();
    let mut phase_before: Option<Json> = None;
    let label = interner.intern("label");
    let mark = interner.intern("mark");
    let relation = interner.intern("rel");
    let weight = interner.intern("weight");
    let new_type = interner.intern("Restored");
    match operation {
        "set_attr" => graph.set_node_attr(a, mark, Value::Bool(true)),
        "node_mut_direct" => { graph.node_mut(a).attrs.insert(mark, Value::Bool(true)); graph.node_mut(a).attrs.insert(label, Value::Str(interner.intern("rewritten"))); },
        "remove_attr" => graph.remove_node_attr(a, label),
        "set_type" => graph.set_node_type(a, new_type),
        "restore_live" => graph.restore_node(a, new_type, attrs(&[(mark, Value::Int(7))])),
        "restore_fresh" => graph.restore_node(NodeID(12), new_type, Attrs::new()),
        "restore_tombstone" => { graph.delete_node(b); graph.restore_node(b, new_type, attrs(&[(mark, Value::Int(3))])); },
        "delete_node" => { graph.delete_node(b); },
        "add_node" => { graph.insert_node(new_type, attrs(&[(mark, Value::Int(2))])); },
        "insert_edge" => { graph.insert_edge(a, interner.intern("extra"), c, Attrs::new()).unwrap(); },
        "replace_edge" => { graph.insert_edge(a, relation, b, attrs(&[(weight, Value::Int(9))])).unwrap(); },
        "mutate_edge_attrs" => { graph.edge_attrs_mut(e1).insert(weight, Value::Int(8)); },
        "delete_edge" => { graph.delete_edge(e1); },
        "batch_delete_edges" => { graph.delete_edges_batch(&[e1, e2, e1]); },
        "repeated_writes" => { graph.set_node_attr(a, mark, Value::Int(1)); graph.set_node_attr(a, mark, Value::Int(2)); graph.set_node_type(a, new_type); },
        "phase_checkpoint" => {
            graph.set_node_attr(a, mark, Value::Int(1));
            graph.checkpoint_experiment_delta_log();
            phase_before = Some(graph_to_value(&graph, &interner));
            graph.set_node_attr(a, mark, Value::Int(2));
            graph.insert_edge(a, interner.intern("phase_edge"), c, Attrs::new()).unwrap();
        },
        "untracked_divergence" => { graph.set_node_attr(a, mark, Value::Bool(true)); },
        _ => unreachable!(),
    }
    let logged_state = graph_to_value(&graph, &interner);
    let log = graph.finish_mutation_log();
    let before_nodes = log.before_nodes.unwrap();
    let before_edges = log.before_edges.unwrap();
    let journal = graph_experiment_delta(&graph, &interner, &before_nodes, &before_edges);
    let oracle = graph_diff(&before, &logged_state).unwrap();
    let (phase_journal, phase_oracle) = if let Some(phase_start) = phase_before {
        let pn = log.phase_before_nodes.as_ref().unwrap();
        let pe = log.phase_before_edges.as_ref().unwrap();
        (Some(graph_experiment_delta(&graph, &interner, pn, pe)),
         Some(graph_diff(&phase_start, &logged_state).unwrap()))
    } else { (None, None) };
    let phase_matches = phase_journal == phase_oracle || phase_journal.is_none();
    let pre_divergence_matches = journal == oracle;
    let divergence_oracle = if operation == "untracked_divergence" {
        graph.set_node_attr(c, mark, Value::Bool(false));
        let final_state = graph_to_value(&graph, &interner);
        Some(graph_diff(&before, &final_state).unwrap())
    } else { None };
    let divergence_detected = divergence_oracle.as_ref().is_some_and(|diff| journal != *diff);
    json!({"case": name, "operation": operation,
        "journal_equals_whole_graph_diff_at_capture": pre_divergence_matches,
        "phase_journal_equals_phase_diff": phase_matches,
        "post_capture_untracked_divergence_detected_by_global_diff": divergence_detected,
        "journal_node_entries": before_nodes.len(), "journal_edge_entries": before_edges.len(),
        "journal_delta": journal, "whole_graph_diff": oracle,
        "phase_journal_delta": phase_journal, "phase_whole_graph_diff": phase_oracle,
        "post_capture_whole_graph_diff": divergence_oracle})
}

fn main() {
    let cases = [
        ("node attribute set", "set_attr"), ("direct mutable node access", "node_mut_direct"),
        ("node attribute removal", "remove_attr"),
        ("node type change", "set_type"), ("live identity restoration", "restore_live"),
        ("fresh identity restoration", "restore_fresh"), ("node deletion with incident edges", "delete_node"),
        ("tombstoned identity restoration", "restore_tombstone"),
        ("node insertion", "add_node"), ("edge insertion", "insert_edge"),
        ("existing edge replacement", "replace_edge"), ("mutable edge attributes", "mutate_edge_attrs"),
        ("single edge deletion", "delete_edge"), ("batch edge deletion with duplicate index", "batch_delete_edges"),
        ("repeated writes to one identity", "repeated_writes"), ("phase checkpoint and derived writes", "phase_checkpoint"),
        ("post-capture untracked divergence control", "untracked_divergence"),
    ];
    let rows: Vec<Json> = cases.iter().map(|(name, op)| run_case(name, op)).collect();
    let all_matrix_cases_match = rows.iter().all(|r| r["journal_equals_whole_graph_diff_at_capture"] == true && r["phase_journal_equals_phase_diff"] == true);
    let divergence_control_works = rows.iter().any(|r| r["post_capture_untracked_divergence_detected_by_global_diff"] == true);
    println!("{}", json!({"schema":"ThoughtexperimentJournalMutationMatrixV1_3", "all_matrix_cases_match":all_matrix_cases_match, "divergence_control_works":divergence_control_works, "rows":rows}));
    if !all_matrix_cases_match || !divergence_control_works { std::process::exit(2); }
}
