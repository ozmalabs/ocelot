//! C — consistency checker. The only path through which Π learns
//! whether a prospective edge is admissible under Γ. Paper §1
//! (Theorem XII / reference-monitor containment).
//!
//! Distinguishes the two failure modes of Definition 3:
//! - Type-1: vocabulary present, but no production admits the triple
//!           (either no production at the (src_type, edge_type,
//!           tgt_type) key, or every matching production's where-clause
//!           evaluates false).
//! - Type-2: at least one constituent type is absent from N ∪ E — the
//!           operation can't even be formed.

use crate::grammar::{Grammar, ProdIdx, Production};
use crate::graph::{NodeID, TypedGraph};
use crate::sym::{Interner, Sym};
use crate::term::{evaluate, ConceptResolver, Env, EvalCache, EvalCtx, TermArena};
use crate::value::Value;
use smallvec::{smallvec, SmallVec};

/// Outcome of a consistency check on a prospective edge.
#[derive(Debug, Clone)]
pub enum CheckOutcome {
    /// Edge is admissible; the prods that admitted it (for explain).
    Admitted(SmallVec<[ProdIdx; 2]>),
    /// Type-1: all three types are in N ∪ E but no production admits.
    Type1NoProduction {
        src_type: Sym,
        edge_type: Sym,
        tgt_type: Sym,
    },
    /// Type-2: one or more types isn't even in the vocabulary.
    Type2VocabAbsent { missing: Sym },
}

impl CheckOutcome {
    pub fn admits(&self) -> bool {
        matches!(self, CheckOutcome::Admitted(_))
    }
}

pub struct ConsistencyChecker {
    pub grammar: Grammar,
}

impl ConsistencyChecker {
    pub fn new(grammar: Grammar) -> Self {
        Self { grammar }
    }

    /// Full check on a real (src, edge_type, tgt) triple. Looks up
    /// candidate productions and evaluates each where-clause; the first
    /// admitting production short-circuits.
    pub fn check_edge(
        &self,
        graph: &TypedGraph,
        interner: &Interner,
        terms: &TermArena,
        concepts: Option<&ConceptResolver>,
        src: NodeID,
        edge_type: Sym,
        tgt: NodeID,
    ) -> CheckOutcome {
        let src_type = graph.node(src).type_;
        let tgt_type = graph.node(tgt).type_;

        // Type-2 takes precedence — produce a missing-vocabulary error
        // before scanning the index.
        if !self.grammar.knows_node_type(src_type) {
            return CheckOutcome::Type2VocabAbsent { missing: src_type };
        }
        if !self.grammar.knows_edge_type(edge_type) {
            return CheckOutcome::Type2VocabAbsent { missing: edge_type };
        }
        if !self.grammar.knows_node_type(tgt_type) {
            return CheckOutcome::Type2VocabAbsent { missing: tgt_type };
        }

        let cand = self.grammar.candidates(src_type, edge_type, tgt_type);
        if cand.is_empty() {
            return CheckOutcome::Type1NoProduction {
                src_type,
                edge_type,
                tgt_type,
            };
        }

        let mut admitting: SmallVec<[ProdIdx; 2]> = SmallVec::new();
        for &pi in cand {
            let prod = &self.grammar.productions[pi.0 as usize];
            if production_admits(prod, src, tgt, graph, interner, terms, concepts) {
                admitting.push(pi);
            }
        }
        if admitting.is_empty() {
            CheckOutcome::Type1NoProduction {
                src_type,
                edge_type,
                tgt_type,
            }
        } else {
            CheckOutcome::Admitted(admitting)
        }
    }
}

/// Evaluate a production's where-clause in the env `{src.var: src,
/// tgt.var: tgt}`. A None where-clause admits unconditionally.
pub fn production_admits(
    prod: &Production,
    src: NodeID,
    tgt: NodeID,
    graph: &TypedGraph,
    interner: &Interner,
    terms: &TermArena,
    concepts: Option<&ConceptResolver>,
) -> bool {
    let Some(where_idx) = prod.where_ else {
        return true;
    };
    let mut env: Env = smallvec![
        (prod.src.var, Value::Node(src)),
        (prod.tgt.var, Value::Node(tgt)),
    ];
    let mut cache = EvalCache::default();
    let mut ctx = EvalCtx::new(graph, interner).with_cache(&mut cache);
    if let Some(c) = concepts {
        ctx = ctx.with_concepts(c);
    }
    evaluate(terms, where_idx, &mut env, &mut ctx).truthy()
}

/// Evaluate a production's weight in the same env. Returns f64;
/// production weights are real numbers (Paper §1.2). A weight that
/// evaluates to a non-numeric Value coerces to 0.0 (matches the
/// degraded-silently posture of the Python eval).
pub fn evaluate_weight(
    prod: &Production,
    src: NodeID,
    tgt: NodeID,
    graph: &TypedGraph,
    interner: &Interner,
    terms: &TermArena,
    concepts: Option<&ConceptResolver>,
) -> f64 {
    let mut env: Env = smallvec![
        (prod.src.var, Value::Node(src)),
        (prod.tgt.var, Value::Node(tgt)),
    ];
    let mut cache = EvalCache::default();
    let mut ctx = EvalCtx::new(graph, interner).with_cache(&mut cache);
    if let Some(c) = concepts {
        ctx = ctx.with_concepts(c);
    }
    evaluate(terms, prod.weight, &mut env, &mut ctx).as_f64()
}
