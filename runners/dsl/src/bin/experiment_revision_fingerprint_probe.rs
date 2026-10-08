use serde_json::json;
use std::time::Instant;
use substrate_rs::checker::ConsistencyChecker;
use substrate_rs::grammar::{Grammar, NodePattern, Production};
use substrate_rs::graph::Attrs;
use substrate_rs::rewrite::RewriteRule;
use substrate_rs::substrate::Substrate;
use substrate_rs::sym::Sym;
use substrate_rs::term::TermNode;
use substrate_rs::value::Value;

fn substrate_at_size(n: usize) -> Substrate {
    let mut sub = Substrate::new(ConsistencyChecker::new(Grammar::new()));
    // Each semantic store grows with n so the fingerprint cost surface is
    // visible independently of the graph, whose O(1) mutation version remains
    // the first revision component.
    for i in 0..n {
        let weight = sub.add_term_node(TermNode::Lit {
            value: Value::Int(i as i64),
        });
        let name = sub.intern_symbol(&format!("rule_{i}"));
        let area = sub.intern_symbol("default");
        let mut rule = RewriteRule::default();
        rule.name = name;
        rule.area = area;
        sub.add_rule(rule);
        let ty = Sym((i % (u16::MAX as usize)) as u32 + 1);
        sub.add_production_no_mirror(Production {
            src: NodePattern {
                type_: ty,
                var: Sym(1),
            },
            edge_type: Sym(2),
            tgt: NodePattern {
                type_: ty,
                var: Sym(3),
            },
            where_: None,
            weight,
            provenance: Sym(4),
        });
    }
    for _ in 0..n {
        sub.graph.insert_node(Sym(20), Attrs::new());
    }
    sub
}

fn median(mut xs: Vec<f64>) -> f64 {
    xs.sort_by(f64::total_cmp);
    xs[xs.len() / 2]
}

fn fingerprint_ms(sub: &Substrate, repeats: usize) -> f64 {
    let mut samples = Vec::with_capacity(repeats);
    for _ in 0..repeats {
        let start = Instant::now();
        std::hint::black_box(full_semantic_fingerprint(sub));
        samples.push(start.elapsed().as_secs_f64() * 1000.0);
    }
    median(samples)
}

fn full_semantic_fingerprint(sub: &Substrate) -> String {
    use std::fmt::Write as _;
    let mut semantic = String::new();
    let _ = write!(
        semantic,
        "rules={:?};terms={:?};",
        sub.rules(),
        sub.term_arena().nodes
    );
    let grammar = &sub.consistency_checker().grammar;
    let _ = write!(semantic, "productions={:?};", grammar.productions);
    let mut index: Vec<_> = grammar
        .index
        .iter()
        .map(|(&(s, e, t), ps)| ((s.0, e.0, t.0), ps.iter().map(|p| p.0).collect::<Vec<_>>()))
        .collect();
    index.sort_by_key(|(key, _)| *key);
    let _ = write!(semantic, "grammar_index={index:?};");
    let mut node_types: Vec<_> = grammar.node_types.iter().map(|s| s.0).collect();
    let mut edge_types: Vec<_> = grammar.edge_types.iter().map(|s| s.0).collect();
    node_types.sort_unstable();
    edge_types.sort_unstable();
    let _ = write!(
        semantic,
        "node_types={node_types:?};edge_types={edge_types:?};"
    );
    let mut concepts: Vec<_> = sub
        .concept_resolver()
        .iter()
        .map(|(s, t)| (s.0, t.0))
        .collect();
    concepts.sort_unstable();
    let _ = write!(
        semantic,
        "concepts={concepts:?};shape_target={:?};",
        sub.active_shape_target()
    );
    substrate_rs::p3_graph::snapshot(semantic.as_bytes()).digest
}

fn tracked_revision_ms(sub: &Substrate, repeats: usize) -> f64 {
    let mut samples = Vec::with_capacity(repeats);
    for _ in 0..repeats {
        let start = Instant::now();
        std::hint::black_box(sub.experiment_graph_rule_revision());
        samples.push(start.elapsed().as_secs_f64() * 1000.0);
    }
    median(samples)
}

fn tracked_mutation_checks() -> serde_json::Value {
    let mut sub = Substrate::new(ConsistencyChecker::new(Grammar::new()));
    let before_term = sub.experiment_graph_rule_revision();
    let term = sub.add_term_node(TermNode::Lit {
        value: Value::Int(1),
    });
    let term_bumped = sub.experiment_graph_rule_revision() != before_term;
    let before_rule = sub.experiment_graph_rule_revision();
    sub.add_rule(RewriteRule::default());
    let rule_bumped = sub.experiment_graph_rule_revision() != before_rule;
    let before_production = sub.experiment_graph_rule_revision();
    sub.add_production_no_mirror(Production {
        src: NodePattern {
            type_: Sym(10),
            var: Sym(1),
        },
        edge_type: Sym(11),
        tgt: NodePattern {
            type_: Sym(10),
            var: Sym(2),
        },
        where_: None,
        weight: term,
        provenance: Sym(12),
    });
    let production_bumped = sub.experiment_graph_rule_revision() != before_production;
    let before_concept = sub.experiment_graph_rule_revision();
    sub.define_concept(Sym(13), term);
    let concept_bumped = sub.experiment_graph_rule_revision() != before_concept;
    json!({"term": term_bumped, "rule": rule_bumped,
        "production": production_bumped, "concept": concept_bumped})
}

fn main() {
    let cells: Vec<_> = [0usize, 100, 1000, 5000]
        .into_iter()
        .map(|n| {
            let sub = substrate_at_size(n);
            json!({"n_per_store": n, "graph_nodes": sub.graph.node_count(),
              "rules": sub.rules().len(), "terms": sub.term_arena().len(),
              "productions": sub.consistency_checker().grammar.productions.len(),
              "tracked_revision_median_ms": tracked_revision_ms(&sub, 31),
              "full_fingerprint_median_ms": fingerprint_ms(&sub, 31)})
        })
        .collect();
    println!(
        "{}",
        json!({"schema":"ExperimentRevisionFingerprintProbeV1",
        "repeats":31,"cells":cells,"tracked_mutation_checks":tracked_mutation_checks()})
    );
}
