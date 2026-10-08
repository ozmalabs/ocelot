//! Γ — weighted admissibility grammar (Paper §1, Definition 2).
//!
//! A `Production` is `(src-pattern, edge-type, tgt-pattern, where-clause,
//! weight)`. The weight is a `Term` (defaults to `Lit(1.0)`); selection
//! over admitted candidates is ∝ exp(w). This is the load-bearing piece
//! of the paper that the existing Python substrate models as an *optional*
//! `weight: Term | None`. Here weight is always present so the binary
//! admit/deny degenerates to the `w > -∞` short-circuit of Definition 2.
//!
//! The grammar's index `(src_type, edge_type, tgt_type) → matching
//! productions` is what gives the consistency checker C its O(|Γ|)
//! per-operation bound (Paper §Theorem XI condition 3).

use crate::sym::Sym;
use crate::term::{TermArena, TermIdx, TermNode};
use crate::value::Value;
use rustc_hash::{FxHashMap, FxHashSet};
use smallvec::SmallVec;

/// Matches a node by type, binding its NodeID to `var` in the evaluator
/// env. `var` is a Sym so the env push/pop is u32-keyed.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct NodePattern {
    pub type_: Sym,
    pub var: Sym,
}

/// One production. `weight` is mandatory (paper requirement) but
/// defaults to `Lit(1.0)` at construction; `provenance` is the
/// human-readable label that survives Γ-edits.
#[derive(Clone, Debug)]
pub struct Production {
    pub src: NodePattern,
    pub edge_type: Sym,
    pub tgt: NodePattern,
    pub where_: Option<TermIdx>,
    pub weight: TermIdx,
    pub provenance: Sym,
}

/// Dense production handle.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct ProdIdx(pub u32);

/// Γ. Tracks the type vocabulary (N ∪ E in paper notation) so the
/// checker can distinguish Type-1 from Type-2 inadmissibility
/// (Definition 3).
#[derive(Clone)]
pub struct Grammar {
    pub productions: Vec<Production>,
    /// (src_type, edge_type, tgt_type) → matching productions.
    /// SmallVec because the typical key has 1–2 productions; rarely more.
    pub index: FxHashMap<(Sym, Sym, Sym), SmallVec<[ProdIdx; 2]>>,
    /// Node type vocabulary — every type referenced by a NodePattern.
    pub node_types: FxHashSet<Sym>,
    /// Edge type vocabulary — every edge_type referenced by a production.
    pub edge_types: FxHashSet<Sym>,
}

impl Grammar {
    pub fn new() -> Self {
        Self {
            productions: Vec::new(),
            index: FxHashMap::default(),
            node_types: FxHashSet::default(),
            edge_types: FxHashSet::default(),
        }
    }

    /// Add a production. Updates the (src, edge, tgt) index and the
    /// type vocabulary.
    pub fn add(&mut self, p: Production) -> ProdIdx {
        let key = (p.src.type_, p.edge_type, p.tgt.type_);
        let idx = ProdIdx(self.productions.len() as u32);
        self.node_types.insert(p.src.type_);
        self.node_types.insert(p.tgt.type_);
        self.edge_types.insert(p.edge_type);
        self.productions.push(p);
        self.index.entry(key).or_default().push(idx);
        idx
    }

    /// Convenience constructor for callers (the substrate's `Π.add_edge`
    /// helper, the Python wrapper) that wires up the default
    /// `Lit(1.0)` weight Term without forcing callers to mint it.
    pub fn default_weight(arena: &mut TermArena) -> TermIdx {
        arena.add(TermNode::Lit {
            value: Value::Float(1.0),
        })
    }

    /// Lookup productions for an exact `(src_type, edge_type, tgt_type)`
    /// triple. Empty SmallVec iff nothing matches the triple key.
    pub fn candidates(&self, src_type: Sym, edge_type: Sym, tgt_type: Sym) -> &[ProdIdx] {
        self.index
            .get(&(src_type, edge_type, tgt_type))
            .map(|v| v.as_slice())
            .unwrap_or(&[])
    }

    /// Type vocabulary membership check — used by the checker to
    /// produce a Type-2 (vs Type-1) inadmissibility error.
    pub fn knows_node_type(&self, t: Sym) -> bool {
        self.node_types.contains(&t)
    }

    pub fn knows_edge_type(&self, t: Sym) -> bool {
        self.edge_types.contains(&t)
    }
}

impl Default for Grammar {
    fn default() -> Self {
        Self::new()
    }
}
