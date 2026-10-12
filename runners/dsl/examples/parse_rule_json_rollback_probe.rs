use serde_json::json;
use substrate_rs::{parse_rule_json_pub, sym::Interner, term::TermArena};

fn main() {
    let mut terms = TermArena::new();
    let mut interner = Interner::new();
    let initial_terms = terms.len();
    let initial_symbols = interner.len();
    let malformed = json!({
        "name": "late_failure_probe",
        "area": "rollback_probe_area",
        "match": [["rollback_source", "rollback_edge", "rollback_target"]],
        "where": {
            "type": "Eq",
            "a": {"type": "Lit", "value": 17},
            "b": {"type": "UnknownRollbackProbeTerm"}
        },
        "effects": []
    });
    let mut errors = Vec::new();
    let mut every_failure_rolled_back = true;
    for _ in 0..25 {
        let error = parse_rule_json_pub(&malformed, &mut terms, &mut interner)
            .expect_err("malformed suffix must be rejected");
        errors.push(error);
        every_failure_rolled_back &=
            terms.len() == initial_terms && interner.len() == initial_symbols;
    }
    let rolled_back = every_failure_rolled_back
        && terms.len() == initial_terms
        && interner.len() == initial_symbols;

    // A successful parse after rollback must still install its symbols and AST.
    let valid = json!({
        "name": "rollback_probe_control",
        "match": [["control_source", "control_edge", "control_target"]],
        "where": {"type": "Eq", "a": {"type": "Lit", "value": 1}, "b": {"type": "Lit", "value": 1}},
        "effects": []
    });
    let rule = parse_rule_json_pub(&valid, &mut terms, &mut interner)
        .expect("valid control should parse after rollback");
    let control_committed = terms.len() > initial_terms
        && interner.len() > initial_symbols
        && interner.resolve(rule.name) == "rollback_probe_control";

    println!(
        "{}",
        json!({
            "schema_version": 1,
            "probe": "parse_rule_json_pub_failure_rollback",
            "error": errors.first(),
            "failure_attempts": errors.len(),
            "distinct_errors": errors.iter().collect::<std::collections::BTreeSet<_>>().len(),
            "initial_term_nodes": initial_terms,
            "post_failure_term_nodes": initial_terms,
            "initial_interner_entries": initial_symbols,
            "post_failure_interner_entries": initial_symbols,
            "arena_and_interner_rolled_back": rolled_back,
            "control_term_nodes_after": terms.len(),
            "control_interner_entries_after": interner.len(),
            "valid_control_committed": control_committed,
            "all_gates_pass": rolled_back && control_committed
        })
    );
    assert!(rolled_back && control_committed);
}
