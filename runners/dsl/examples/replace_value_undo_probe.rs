use rustc_hash::FxHashMap;
use substrate_rs::graph::{Attrs, TypedGraph};
use substrate_rs::rewrite::{apply_rule_full, undo_apply, Binding, Effect, RewriteRule};
use substrate_rs::sym::Interner;
use substrate_rs::term::TermArena;
use substrate_rs::value::Value;

fn attrs(key: substrate_rs::sym::Sym, value: i64) -> Attrs {
    Attrs(vec![(key, Value::Int(value))])
}

fn run(collision: bool) {
    let mut i = Interner::new();
    let mut g = TypedGraph::new();
    let mut terms = TermArena::new();
    let t = i.intern("Value");
    let et = i.intern("uses");
    let key = i.intern("weight");
    let a = g.insert_node(t, FxHashMap::default());
    let b = g.insert_node(t, FxHashMap::default());
    let old = g.insert_node(t, FxHashMap::default());
    let new = g.insert_node(t, FxHashMap::default());
    g.insert_edge(a, et, old, attrs(key, 5)).unwrap();
    g.insert_edge(b, et, old, attrs(key, 6)).unwrap();
    if collision {
        g.insert_edge(a, et, new, attrs(key, 99)).unwrap();
    }
    let before_edges = if collision { 3 } else { 2 };
    let rule = RewriteRule {
        name: i.intern("replace_value_undo_probe"),
        effects: vec![Effect::ReplaceValue {
            old_var: i.intern("old"),
            new_var: i.intern("new"),
        }],
        ..Default::default()
    };
    let mut binding = Binding::default();
    binding.insert(i.intern("old"), old);
    binding.insert(i.intern("new"), new);
    let outcome = apply_rule_full(
        &rule, &binding, &mut terms, &mut g, &mut i, None, None, None, true,
    );
    assert!(outcome.progressed);
    let dst_idx = g.edge_idx(a, et, new).expect("rewired destination");
    assert_eq!(g.edge_attrs(dst_idx).get(&key), Some(&Value::Int(5)));
    assert!(!g.has_edge(a, et, old));
    assert!(g.has_edge(b, et, new));
    undo_apply(outcome.undo, &mut g);
    assert!(g.has_edge(a, et, old));
    assert!(g.has_edge(b, et, old));
    assert!(!g.has_edge(b, et, new));
    assert_eq!(g.edge_count(), before_edges);
    let a_old = g.edge_idx(a, et, old).unwrap();
    let b_old = g.edge_idx(b, et, old).unwrap();
    assert_eq!(g.edge_attrs(a_old).get(&key), Some(&Value::Int(5)));
    assert_eq!(g.edge_attrs(b_old).get(&key), Some(&Value::Int(6)));
    if collision {
        let a_new = g
            .edge_idx(a, et, new)
            .expect("original destination restored");
        assert_eq!(g.edge_attrs(a_new).get(&key), Some(&Value::Int(99)));
    } else {
        assert!(!g.has_edge(a, et, new));
    }
}

fn main() {
    run(false);
    run(true);
    println!(
        "{}",
        r#"{"probe":"replace_value_undo","cases":[{"case":"noncollision_rewrite","rollback_exact":true},{"case":"destination_collision_attr_restore","rollback_exact":true}],"all_exact":true}"#
    );
}
