//! Engine extension layer — additional capabilities beyond the paper-
//! pinned core. Phase 7 ships [`Counters`]: per-Substrate
//! observability so the agent (or a human profiler) can see WHERE the
//! work is going.
//!
//! Design pin: the engine increments these counters cheaply (u64 add,
//! one Sym hash). The capability they enable — "which production is the
//! hot path", "is the eval cache earning its keep" — is what the gap
//! analysis flagged as load-bearing for self-improvement; without it
//! the agent can't observe its own bottlenecks.

use crate::grammar::ProdIdx;
use crate::sym::Sym;
use rustc_hash::FxHashMap;

/// Per-Substrate observability. All counters are monotonic u64; reset
/// by `clear()` if a caller wants a windowed sample.
#[derive(Default, Debug, Clone)]
pub struct Counters {
    /// Total nodes inserted (cumulative; not affected by deletes — see
    /// `nodes_live_by_type` for the current live count).
    pub nodes_inserted_total: u64,
    /// Total edges inserted (cumulative).
    pub edges_inserted_total: u64,
    /// Per-type cumulative node insert count. Useful for "what's the
    /// dominant kind in this mind?".
    pub nodes_inserted_by_type: FxHashMap<Sym, u64>,
    /// Per-edge-type cumulative insert count.
    pub edges_inserted_by_type: FxHashMap<Sym, u64>,

    /// Number of times each production admitted an edge.
    /// Indexed by `ProdIdx` — sparse so we use a map not a Vec.
    /// (Vec indexed by ProdIdx.0 would also work and be slightly
    /// faster; map keeps the diagnostic surface uniform with the rest.)
    pub production_admits: FxHashMap<ProdIdx, u64>,
    /// Number of times each production rejected an edge it was a
    /// candidate for (its where-clause evaluated false).
    pub production_rejects: FxHashMap<ProdIdx, u64>,
    /// Total admissibility checks ever submitted to C — denominator for
    /// the admit-rate calculation.
    pub admissibility_checks_total: u64,
    /// Of those, how many resulted in Type-1 (no production admits)
    /// vs Type-2 (vocabulary absent). Splits the rejection envelope
    /// for diagnostics — Type-1 means "Γ is incomplete on this
    /// triple", Type-2 means "the agent reached for a type/edge it
    /// hasn't introduced yet".
    pub rejections_type1: u64,
    pub rejections_type2: u64,

    /// Number of Term evaluations performed via the top-level
    /// `evaluate` entry point. Per-Term-variant counters could
    /// extend this; keeping it coarse for now.
    pub evaluations_total: u64,
    /// Eval-cache hit/miss tallies for Neighbours / Filter. The hit
    /// rate is the headline number for whether the per-step cache is
    /// worth the memory.
    pub cache_neighbours_hits: u64,
    pub cache_neighbours_misses: u64,
    pub cache_filter_hits: u64,
    pub cache_filter_misses: u64,

    /// `shape_mismatch_prunes_negative_problem_space` at the derivation
    /// dispatch level: count of derivable-variant calls where the
    /// registered derivation's Shape was incompatible with the
    /// EvalCtx's active shape_target, causing dispatch to fall back to
    /// the native kernel implementation. Per-tick savings the
    /// Cousot+Ashby pruning earns at the derivation layer.
    pub derivation_shape_pruned: u64,

    /// Same vocabulary rule, applied to the concept resolver: count of
    /// Holds(concept, ...) calls where the concept's Term-tree had a
    /// Shape incompatible with the EvalCtx's active shape_target. Such
    /// calls return Value::None as if the concept were undefined —
    /// the substrate-level filter the agent set excludes the concept.
    pub concept_shape_pruned: u64,

    /// THE `P0`-ON-A-STRING COUNTER (2026-08-10).
    ///
    /// `P0(node, key)` is `Plus(Attr(node, key), 0.0)` — the
    /// first-class-absence idiom, and it is an idiom for NUMBERS. A
    /// MISSING attr evaluates to `Value::None`, contributes the
    /// identity, and yields 0: that is the idiom working, and it stays
    /// silent.
    ///
    /// A PRESENT non-numeric — a `Str`/`Sym` attr — is a different
    /// thing entirely, and used to be indistinguishable from absence:
    /// `numeric_variadic`'s catch-all `_ => {}` skipped it, so `P0` on a
    /// string returned 0 and compared FALSE forever against any real
    /// string term. Measured on the F-16 arc (commit 05f7231857): the
    /// reflex-condensation index silently took the "varied" branch on a
    /// byte-identical program, giving 16 shapes, every run 1, epoch 0 —
    /// a faculty that installed cleanly and could never fire.
    ///
    /// The value semantics are UNCHANGED (a present string still
    /// contributes the identity, so every existing seed is
    /// byte-identical); what changed is that it is now COUNTABLE
    /// instead of invisible. Non-zero means some rule is reading a
    /// string through a numeric idiom, and the fix at that site is `A`,
    /// not `P0` — `A`'s absence polarity is also the correct one, since
    /// an unset attr is equal to nothing.
    pub numeric_op_non_numeric_operand: u64,
}

impl Counters {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn clear(&mut self) {
        *self = Self::default();
    }

    pub fn on_node_inserted(&mut self, type_: Sym) {
        self.nodes_inserted_total += 1;
        *self.nodes_inserted_by_type.entry(type_).or_insert(0) += 1;
    }

    pub fn on_edge_inserted(&mut self, edge_type: Sym) {
        self.edges_inserted_total += 1;
        *self.edges_inserted_by_type.entry(edge_type).or_insert(0) += 1;
    }

    pub fn on_production_admit(&mut self, prod: ProdIdx) {
        *self.production_admits.entry(prod).or_insert(0) += 1;
    }

    pub fn on_production_reject(&mut self, prod: ProdIdx) {
        *self.production_rejects.entry(prod).or_insert(0) += 1;
    }

    pub fn on_admissibility_check(&mut self) {
        self.admissibility_checks_total += 1;
    }

    pub fn on_rejection_type1(&mut self) {
        self.rejections_type1 += 1;
    }

    pub fn on_rejection_type2(&mut self) {
        self.rejections_type2 += 1;
    }

    pub fn on_evaluation(&mut self) {
        self.evaluations_total += 1;
    }

    pub fn on_cache_neighbours(&mut self, hit: bool) {
        if hit {
            self.cache_neighbours_hits += 1;
        } else {
            self.cache_neighbours_misses += 1;
        }
    }

    /// Bumped by `lookup_value_taker_def` when the registered
    /// derivation is shape-pruned away (fell back to native dispatch).
    pub fn on_derivation_shape_pruned(&mut self) {
        self.derivation_shape_pruned += 1;
    }

    /// Bumped by the Holds eval arm when the concept's def Shape is
    /// incompatible with the active shape_target — concept appears
    /// undefined for this call.
    pub fn on_concept_shape_pruned(&mut self) {
        self.concept_shape_pruned += 1;
    }

    pub fn on_cache_filter(&mut self, hit: bool) {
        if hit {
            self.cache_filter_hits += 1;
        } else {
            self.cache_filter_misses += 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn counter_increments() {
        let mut c = Counters::new();
        let t = Sym(1);
        c.on_node_inserted(t);
        c.on_node_inserted(t);
        c.on_node_inserted(Sym(2));
        assert_eq!(c.nodes_inserted_total, 3);
        assert_eq!(c.nodes_inserted_by_type[&t], 2);
        assert_eq!(c.nodes_inserted_by_type[&Sym(2)], 1);
    }

    #[test]
    fn cache_counters_separate() {
        let mut c = Counters::new();
        c.on_cache_neighbours(true);
        c.on_cache_neighbours(true);
        c.on_cache_neighbours(false);
        c.on_cache_filter(true);
        assert_eq!(c.cache_neighbours_hits, 2);
        assert_eq!(c.cache_neighbours_misses, 1);
        assert_eq!(c.cache_filter_hits, 1);
        assert_eq!(c.cache_filter_misses, 0);
    }

    #[test]
    fn clear_resets_everything() {
        let mut c = Counters::new();
        c.on_node_inserted(Sym(1));
        c.on_evaluation();
        c.clear();
        assert_eq!(c.nodes_inserted_total, 0);
        assert_eq!(c.evaluations_total, 0);
    }
}
