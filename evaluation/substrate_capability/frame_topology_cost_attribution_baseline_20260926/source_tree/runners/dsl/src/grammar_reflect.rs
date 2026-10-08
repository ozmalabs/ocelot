//! Γ ↔ G-subgraph reflection (Paper Axiom 3, applied to `Grammar`/`Production`
//! specifically — the object `SELF_REFERENCE_INFINITY_GROUNDING.md` §3.2 found
//! was NOT routed through `reflect::term_to_subgraph`, unlike the Rule layer).
//!
//! This module is the exact analogue of `graph_rules.rs` (which does this for
//! `RewriteRule`/Rule nodes), applied to `crate::grammar::Production`. A
//! `Production`'s `where_`/`weight` fields are `TermIdx`s — they round-trip via
//! the SAME generic `reflect::term_to_subgraph`/`term_from_subgraph` machinery
//! Term-trees already use elsewhere (EvalSubgraph, reflex-net stimulus terms,
//! `add_term_subgraph`). The scalar fields (`src`/`tgt`/`edge_type`/
//! `provenance`) are plain Sym-valued node attrs, exactly like
//! `graph_rules::rule_from_node` encodes a Rule's scalar fields.
//!
//! Deliberately DISTINCT node-type vocabulary (`GammaGrammar` /
//! `GammaProduction` / `GammaNodePattern`) from the pre-existing Python
//! `substrate/grammar.py` convention (`Grammar` / `Production` / `NodePattern`)
//! — that Python mechanism is a DIFFERENT object (the CuriousAgent's
//! Γ_dynamic "discovered relations" bookkeeping, disconnected from
//! `ConsistencyChecker.grammar`; see GAMMA_REFLECTION_WIRING_PREREG.md §0.4).
//! Reusing its type strings for the paper's actual admissibility Γ would be
//! both a collision risk and a category error.
//!
//! **Honest scope (see PREREG §2):** `ConsistencyChecker.grammar` remains the
//! sole struct `check_edge` reads — this module does not touch that hot path.
//! What this module gives is a real, independently-reconstructable graph
//! mirror, written in the same call as the Rust-side struct mutation
//! (`Substrate::add_production`), so the two cannot drift for anything added
//! through that one call site. It is a mirror, not a replacement, and not
//! (yet) a single source of truth — named precisely, not overclaimed.

use crate::grammar::{Grammar, NodePattern, Production};
use crate::graph::{NodeID, TypedGraph};
use crate::reflect::{term_from_subgraph, term_to_subgraph, ReflectError};
use crate::sym::{Interner, Sym};
use crate::term::TermArena;

pub const GAMMA_GRAMMAR_NODE: &str = "GammaGrammar";
pub const GAMMA_PRODUCTION_NODE: &str = "GammaProduction";
pub const GAMMA_NODEPATTERN_NODE: &str = "GammaNodePattern";

const EDGE_PRODUCTION: &str = "production";
const EDGE_PATTERN_SRC: &str = "pattern.src";
const EDGE_PATTERN_TGT: &str = "pattern.tgt";
const EDGE_PATTERN_WHERE: &str = "pattern.where";
const EDGE_PATTERN_WEIGHT: &str = "pattern.weight";

/// Write one `Production` into the graph as a `GammaProduction` node, wired
/// from `root` (a `GammaGrammar` node) via a `production` edge carrying an
/// `index` attr (so `grammar_from_graph` can recover insertion order — the
/// same convention `graph_rules::run_graph_rules_opts` doesn't need, but
/// `substrate/grammar.py`'s `to_subgraph` already established for this exact
/// shape). Returns the new `GammaProduction` NodeID.
///
/// `where_`/`weight` route through the GENERIC `reflect::term_to_subgraph` —
/// this is the literal ask of recommendation 2(ii): those two Term-valued
/// fields become real `Term.*` subgraphs, not an opaque JSON blob.
pub fn production_to_subgraph(
    root: NodeID,
    index: i64,
    p: &Production,
    graph: &mut TypedGraph,
    arena: &TermArena,
    interner: &mut Interner,
) -> NodeID {
    let prod_type = interner.intern(GAMMA_PRODUCTION_NODE);
    let pattern_type = interner.intern(GAMMA_NODEPATTERN_NODE);

    let edge_type_key = interner.intern("edge_type");
    let provenance_key = interner.intern("provenance");
    let mut prod_attrs = rustc_hash::FxHashMap::default();
    prod_attrs.insert(edge_type_key, crate::value::Value::Str(p.edge_type));
    prod_attrs.insert(provenance_key, crate::value::Value::Str(p.provenance));
    let prod_id = graph.insert_node(prod_type, prod_attrs);

    let index_key = interner.intern("index");
    let mut prod_edge_attrs = rustc_hash::FxHashMap::default();
    prod_edge_attrs.insert(index_key, crate::value::Value::Int(index));
    let production_edge = interner.intern(EDGE_PRODUCTION);
    graph
        .insert_edge(root, production_edge, prod_id, prod_edge_attrs)
        .expect("freshly-inserted GammaProduction node always connects");

    let type_key = interner.intern("type");
    let var_key = interner.intern("var");

    let mut src_attrs = rustc_hash::FxHashMap::default();
    src_attrs.insert(type_key, crate::value::Value::Str(p.src.type_));
    src_attrs.insert(var_key, crate::value::Value::Str(p.src.var));
    let src_id = graph.insert_node(pattern_type, src_attrs);
    let pattern_src_edge = interner.intern(EDGE_PATTERN_SRC);
    graph
        .insert_edge(
            prod_id,
            pattern_src_edge,
            src_id,
            rustc_hash::FxHashMap::default(),
        )
        .expect("freshly-inserted GammaNodePattern node always connects");

    let mut tgt_attrs = rustc_hash::FxHashMap::default();
    tgt_attrs.insert(type_key, crate::value::Value::Str(p.tgt.type_));
    tgt_attrs.insert(var_key, crate::value::Value::Str(p.tgt.var));
    let tgt_id = graph.insert_node(pattern_type, tgt_attrs);
    let pattern_tgt_edge = interner.intern(EDGE_PATTERN_TGT);
    graph
        .insert_edge(
            prod_id,
            pattern_tgt_edge,
            tgt_id,
            rustc_hash::FxHashMap::default(),
        )
        .expect("freshly-inserted GammaNodePattern node always connects");

    if let Some(where_idx) = p.where_ {
        let where_root = term_to_subgraph(arena, where_idx, graph, interner);
        let pattern_where_edge = interner.intern(EDGE_PATTERN_WHERE);
        graph
            .insert_edge(
                prod_id,
                pattern_where_edge,
                where_root,
                rustc_hash::FxHashMap::default(),
            )
            .expect("freshly-inserted Term subgraph root always connects");
    }

    // weight is mandatory on `Production` (paper requirement) — always
    // reflect it, mirroring the field's own "always present" invariant.
    let weight_root = term_to_subgraph(arena, p.weight, graph, interner);
    let pattern_weight_edge = interner.intern(EDGE_PATTERN_WEIGHT);
    graph
        .insert_edge(
            prod_id,
            pattern_weight_edge,
            weight_root,
            rustc_hash::FxHashMap::default(),
        )
        .expect("freshly-inserted Term subgraph root always connects");

    prod_id
}

/// Errors specific to reading a `GammaProduction`/`GammaGrammar` subgraph
/// back — the exact analogue of `graph_rules::rule_from_node` returning
/// `Option<RewriteRule>`, but with a typed error so `grammar_from_graph`
/// can report exactly which node was malformed rather than silently
/// skipping (this module has no "install what parses, skip what doesn't"
/// fixpoint discipline to fall back on the way `run_graph_rules_opts` does).
#[derive(Debug, Clone)]
pub enum GammaReflectError {
    NotAGammaGrammar {
        type_name: String,
    },
    NotAGammaProduction {
        type_name: String,
    },
    NotAGammaNodePattern {
        type_name: String,
    },
    MissingAttr {
        node: NodeID,
        field: &'static str,
    },
    MissingEdge {
        node: NodeID,
        edge_type: &'static str,
    },
    BadTerm(ReflectError),
}

impl From<ReflectError> for GammaReflectError {
    fn from(e: ReflectError) -> Self {
        GammaReflectError::BadTerm(e)
    }
}

fn read_sym_attr(
    graph: &TypedGraph,
    interner: &Interner,
    node: NodeID,
    field: &'static str,
) -> Result<Sym, GammaReflectError> {
    let key = interner
        .lookup(field)
        .ok_or(GammaReflectError::MissingAttr { node, field })?;
    match graph.node(node).attrs.get(&key) {
        Some(crate::value::Value::Str(s)) => Ok(*s),
        _ => Err(GammaReflectError::MissingAttr { node, field }),
    }
}

fn single_out_edge(
    graph: &TypedGraph,
    interner: &Interner,
    node: NodeID,
    edge_type: &'static str,
) -> Result<NodeID, GammaReflectError> {
    let et_sym = interner
        .lookup(edge_type)
        .ok_or(GammaReflectError::MissingEdge { node, edge_type })?;
    graph
        .out_edges_idx(node, Some(et_sym))
        .into_iter()
        .next()
        .map(|ei| graph.edge(ei).tgt)
        .ok_or(GammaReflectError::MissingEdge { node, edge_type })
}

fn read_node_pattern(
    graph: &TypedGraph,
    interner: &Interner,
    nid: NodeID,
) -> Result<NodePattern, GammaReflectError> {
    let type_name = interner.resolve(graph.node(nid).type_);
    if type_name != GAMMA_NODEPATTERN_NODE {
        return Err(GammaReflectError::NotAGammaNodePattern {
            type_name: type_name.to_string(),
        });
    }
    Ok(NodePattern {
        type_: read_sym_attr(graph, interner, nid, "type")?,
        var: read_sym_attr(graph, interner, nid, "var")?,
    })
}

/// Read one `GammaProduction` node back into a native `Production` —
/// the exact analogue of `graph_rules::rule_from_node`. `where_` is
/// optional (absent edge ⇒ `None`, matching the struct's own
/// `Option<TermIdx>`); `weight` is mandatory (matches the struct's own
/// always-present invariant) and its absence is a malformed-node error
/// rather than a silent default, so a caller can tell "no mirror data"
/// apart from "no weight clause" (the encoder always writes one).
pub fn production_from_node(
    graph: &TypedGraph,
    node_id: NodeID,
    arena: &mut TermArena,
    interner: &Interner,
) -> Result<Production, GammaReflectError> {
    let type_name = interner.resolve(graph.node(node_id).type_);
    if type_name != GAMMA_PRODUCTION_NODE {
        return Err(GammaReflectError::NotAGammaProduction {
            type_name: type_name.to_string(),
        });
    }

    let edge_type = read_sym_attr(graph, interner, node_id, "edge_type")?;
    let provenance = read_sym_attr(graph, interner, node_id, "provenance")?;

    let src_pattern_id = single_out_edge(graph, interner, node_id, EDGE_PATTERN_SRC)?;
    let tgt_pattern_id = single_out_edge(graph, interner, node_id, EDGE_PATTERN_TGT)?;
    let src = read_node_pattern(graph, interner, src_pattern_id)?;
    let tgt = read_node_pattern(graph, interner, tgt_pattern_id)?;

    let where_ = match single_out_edge(graph, interner, node_id, EDGE_PATTERN_WHERE) {
        Ok(where_root) => Some(term_from_subgraph(graph, interner, where_root, arena)?),
        Err(GammaReflectError::MissingEdge { .. }) => None,
        Err(e) => return Err(e),
    };
    let weight_root = single_out_edge(graph, interner, node_id, EDGE_PATTERN_WEIGHT)?;
    let weight = term_from_subgraph(graph, interner, weight_root, arena)?;

    Ok(Production {
        src,
        edge_type,
        tgt,
        where_,
        weight,
        provenance,
    })
}

/// Read an entire `GammaGrammar` subgraph back into a native, indexed
/// `Grammar` — the exact analogue of `graph_rules::run_graph_rules_opts`'s
/// "walk every Rule node, parse, collect" loop, but for productions.
/// Productions are ordered by their `production` edge's `index` attr (the
/// same convention `production_to_subgraph` writes), so the reconstructed
/// `Grammar.productions` order matches insertion order.
pub fn grammar_from_graph(
    graph: &TypedGraph,
    root: NodeID,
    arena: &mut TermArena,
    interner: &Interner,
) -> Result<Grammar, GammaReflectError> {
    let type_name = interner.resolve(graph.node(root).type_);
    if type_name != GAMMA_GRAMMAR_NODE {
        return Err(GammaReflectError::NotAGammaGrammar {
            type_name: type_name.to_string(),
        });
    }
    let production_edge =
        interner
            .lookup(EDGE_PRODUCTION)
            .ok_or(GammaReflectError::MissingEdge {
                node: root,
                edge_type: EDGE_PRODUCTION,
            })?;
    let index_key = interner.lookup("index");

    let mut entries: Vec<(i64, NodeID)> = graph
        .out_edges_idx(root, Some(production_edge))
        .into_iter()
        .map(|ei| {
            let edge = graph.edge(ei);
            let idx = index_key
                .and_then(|k| graph.edge_attrs(ei).iter().find(|(kk, _)| **kk == k))
                .map(|(_, v)| v.as_i64())
                .unwrap_or(0);
            (idx, edge.tgt)
        })
        .collect();
    entries.sort_by_key(|(idx, _)| *idx);

    let mut g = Grammar::new();
    for (_, pid) in entries {
        let p = production_from_node(graph, pid, arena, interner)?;
        g.add(p);
    }
    Ok(g)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::term::TermNode;
    use crate::value::Value;

    fn mk_production(
        interner: &mut Interner,
        arena: &mut TermArena,
        src_t: &str,
        edge_t: &str,
        tgt_t: &str,
        with_where: bool,
    ) -> Production {
        let src = NodePattern {
            type_: interner.intern(src_t),
            var: interner.intern("a"),
        };
        let tgt = NodePattern {
            type_: interner.intern(tgt_t),
            var: interner.intern("b"),
        };
        let where_ = if with_where {
            let lhs = arena.add(TermNode::Var { name: src.var });
            let rhs = arena.add(TermNode::Lit {
                value: Value::Int(7),
            });
            Some(arena.add(TermNode::Eq { a: lhs, b: rhs }))
        } else {
            None
        };
        let weight = Grammar::default_weight(arena);
        Production {
            src,
            edge_type: interner.intern(edge_t),
            tgt,
            where_,
            weight,
            provenance: interner.intern("test:mk_production"),
        }
    }

    /// Round-trip: encode two productions (one with a `where` Term, one
    /// without) into a fresh graph, decode them back via
    /// `grammar_from_graph`, and check the reconstructed `Grammar` is
    /// content-equal to what was encoded — the PREREG §1.3 bar-5 proof.
    #[test]
    fn round_trip_content_equal() {
        let mut interner = Interner::new();
        let mut arena = TermArena::new();
        let mut graph = TypedGraph::new();

        let p1 = mk_production(
            &mut interner,
            &mut arena,
            "AliveCell",
            "adjacent",
            "AliveCell",
            true,
        );
        let p2 = mk_production(&mut interner, &mut arena, "N", "tag", "N", false);

        let root_type = interner.intern(GAMMA_GRAMMAR_NODE);
        let root = graph.insert_node(root_type, rustc_hash::FxHashMap::default());
        production_to_subgraph(root, 0, &p1, &mut graph, &arena, &mut interner);
        production_to_subgraph(root, 1, &p2, &mut graph, &arena, &mut interner);

        let mut arena2 = TermArena::new();
        let rebuilt = grammar_from_graph(&graph, root, &mut arena2, &interner)
            .expect("grammar_from_graph should succeed on a well-formed mirror");

        assert_eq!(rebuilt.productions.len(), 2);

        // p1: has a where-clause — compare via JSON (Term identity across
        // two different arenas isn't meaningful; structural JSON is).
        let r1 = &rebuilt.productions[0];
        assert_eq!(interner.resolve(r1.src.type_), "AliveCell");
        assert_eq!(interner.resolve(r1.edge_type), "adjacent");
        assert_eq!(interner.resolve(r1.tgt.type_), "AliveCell");
        assert_eq!(interner.resolve(r1.provenance), "test:mk_production");
        let orig_where_json = crate::jsonio::term_to_json(&arena, p1.where_.unwrap(), &interner);
        let rebuilt_where_json = crate::jsonio::term_to_json(
            &arena2,
            r1.where_.expect("where_ should round-trip"),
            &interner,
        );
        assert_eq!(orig_where_json, rebuilt_where_json);

        // p2: no where-clause — must round-trip to None, not an accidental Some.
        let r2 = &rebuilt.productions[1];
        assert!(r2.where_.is_none());
        assert_eq!(interner.resolve(r2.src.type_), "N");
        assert_eq!(interner.resolve(r2.edge_type), "tag");

        // weight (mandatory on both) round-trips too.
        let orig_weight_json = crate::jsonio::term_to_json(&arena, p1.weight, &interner);
        let rebuilt_weight_json = crate::jsonio::term_to_json(&arena2, r1.weight, &interner);
        assert_eq!(orig_weight_json, rebuilt_weight_json);
    }

    /// A node of the wrong type is rejected cleanly rather than silently
    /// misparsed — mirrors the discipline `rule_from_node` uses (`?`
    /// short-circuit on shape mismatch), just with a named error instead
    /// of `None`, since `grammar_from_graph` isn't inside a
    /// skip-what-doesn't-parse fixpoint loop.
    #[test]
    fn wrong_type_node_is_rejected() {
        let mut interner = Interner::new();
        let mut graph = TypedGraph::new();
        let not_a_grammar = interner.intern("SomethingElse");
        let nid = graph.insert_node(not_a_grammar, rustc_hash::FxHashMap::default());
        let mut arena = TermArena::new();
        let err = grammar_from_graph(&graph, nid, &mut arena, &interner);
        assert!(matches!(
            err,
            Err(GammaReflectError::NotAGammaGrammar { .. })
        ));
    }
}
