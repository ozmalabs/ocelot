//! `stage_a` — non-mutating proposal construction.
//!
//! # What this is
//!
//! `DECISION_LAYER_PREREG.md` Stage A: a pass DERIVES against an immutable base
//! and produces a proposal, instead of applying-then-maybe-undoing per binding.
//! Selection over a *set* of candidate outcomes presupposes candidates that
//! exist before any of them is applied, so this is the prerequisite for Stage B
//! rather than an independent optimisation.
//!
//! # What measurement changed about the plan
//!
//! Two facts, both measured before any of this was written, and both of which
//! move the justification:
//!
//! 1. **The prereg cited the wrong applier.** It names `rewrite.rs`'s cold path
//!    as the mutate-during-derivation site. There are TWO appliers, and the one
//!    the live engine runs is the drain loop in `substrate.rs` — a fact found
//!    only because an instrument placed at the prereg's own citation recorded
//!    ZERO events on a workload that `scale_audit` said had 401.
//!
//! 2. **The correctness premise is false as stated.** Bindings are collected
//!    before any apply, so enumeration already reads an unmutated graph, and on
//!    401 of 401 rolled-back probes the graph fingerprint after undo equalled
//!    the fingerprint before (`effect_audit::probe_exactness`). Apply-then-undo
//!    is WASTEFUL, NOT WRONG. There is a structural reason it is exact rather
//!    than luck: `DelNode` is the one effect undo cannot reverse, and a firing
//!    that deletes a node reports progress, so it is never the firing that gets
//!    rolled back.
//!
//! What genuinely mutates during derivation is narrower and was never named in
//! the prereg: the drain applies EVERY progressing binding without breaking, so
//! binding N+1's effect terms evaluate against binding N's committed writes.
//! That affects 11 rules on the conversational workload — under the prereg's
//! own NO-GO of 20 — so changing it is permitted, but it is a semantic change
//! with no measured defect behind it. Hence: **flagged, default OFF, and
//! byte-identical when off.** This is a mode to measure with, not a fix.
//!
//! # The exclusion, and why it is principled rather than convenient
//!
//! Deriving every binding against one base means undoing the PROGRESSING
//! firings too, not just the rejected ones — and `UndoStep::NodeDeleted` is
//! documented in `rewrite.rs` as unrestorable: *"We don't try to restore
//! deleted nodes — the NodeID would change on re-insertion."* So a rule whose
//! effects can delete a node cannot be derived speculatively by this route at
//! all. Such rules (44 in the seed corpus, all pruning/retirement) keep the
//! committed semantics and are counted, never silently skipped.

use rustc_hash::FxHashMap;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

use crate::graph::{Attrs, NodeID, TypedGraph};
use crate::rewrite::UndoStep;
use crate::sym::Sym;
use crate::term::TermIdx;
use crate::value::Value;

/// One resolved write, captured from a speculative firing before it was undone.
///
/// These are CONCRETE — Terms are already evaluated — so replay is a pure write
/// list with no re-evaluation, and therefore cannot observe the graph it is
/// being applied to. That is the whole point: it is what a proposal has to be
/// for a later stage to select among several of them.
#[derive(Clone, Debug)]
pub enum Write {
    /// Mint a node. `slot` is a proposal-local handle; later writes in the same
    /// proposal refer to the new node by slot, because its replay-time NodeID
    /// is not knowable at derivation time (the derivation-time id was freed by
    /// the undo and may be reissued to someone else).
    AddNode {
        slot: usize,
        type_: Sym,
        attrs: Attrs,
    },
    /// Mint a node ONLY if no node of `type_` already carries every
    /// `dedup` pair — `AddNodeIfAbsent`'s own subset semantics, re-checked at
    /// COMMIT time rather than resolved during derivation.
    ///
    /// This is the difference between a proposal and a pre-made decision. The
    /// absence check is a question about the graph the write lands on, so
    /// answering it while deriving — against a base that does not yet contain
    /// the sibling proposals about to be applied — is answering the wrong
    /// question. Flattening it to an unconditional `AddNode` is exactly what
    /// made two bindings each mint `Concept{name: friend}` where the committed
    /// engine minted one.
    AddNodeIfAbsent {
        slot: usize,
        type_: Sym,
        dedup: Vec<(Sym, Value)>,
        attrs: Attrs,
    },
    AddEdge {
        src: Ref,
        edge_type: Sym,
        tgt: Ref,
        attrs: Attrs,
    },
    DelEdge {
        src: Ref,
        edge_type: Sym,
        tgt: Ref,
    },
    SetAttr {
        node: Ref,
        key: Sym,
        value: Option<Value>,
    },
}

/// A node reference in a proposal: either an id that already existed in the
/// base, or a slot minted earlier in this same proposal.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ref {
    Existing(NodeID),
    Slot(usize),
}

/// The accumulated effects of one rule firing, before application.
#[derive(Clone, Debug, Default)]
pub struct Proposal {
    pub writes: Vec<Write>,
    pub progressed: bool,
}

/// `None` until first read. Initialised from `OZMA_STAGE_A` (`1`/`true`/`on`)
/// so a whole test suite can be run under the mode without a per-test hook —
/// the same shape as the engine's other opt-in modes. An explicit
/// `set_enabled` call overrides it for the rest of the process.
static ENV_DEFAULT: std::sync::OnceLock<bool> = std::sync::OnceLock::new();

static ENABLED: AtomicBool = AtomicBool::new(false);
static ENABLED_SET: AtomicBool = AtomicBool::new(false);
static PROPOSALS: AtomicU64 = AtomicU64::new(0);
static WRITES: AtomicU64 = AtomicU64::new(0);
static EXCLUDED_DRAINS: AtomicU64 = AtomicU64::new(0);

pub fn enabled() -> bool {
    if ENABLED_SET.load(Ordering::Relaxed) {
        return ENABLED.load(Ordering::Relaxed);
    }
    *ENV_DEFAULT.get_or_init(|| {
        matches!(
            std::env::var("OZMA_STAGE_A").unwrap_or_default().as_str(),
            "1" | "true" | "on" | "yes"
        )
    })
}

pub fn set_enabled(on: bool) {
    ENABLED.store(on, Ordering::Relaxed);
    ENABLED_SET.store(true, Ordering::Relaxed);
}

/// `(proposals_derived, writes_captured, drains_excluded_for_del_node)`.
pub fn stats() -> (u64, u64, u64) {
    (
        PROPOSALS.load(Ordering::Relaxed),
        WRITES.load(Ordering::Relaxed),
        EXCLUDED_DRAINS.load(Ordering::Relaxed),
    )
}

pub fn reset() {
    PROPOSALS.store(0, Ordering::Relaxed);
    WRITES.store(0, Ordering::Relaxed);
    EXCLUDED_DRAINS.store(0, Ordering::Relaxed);
    CONFLICT_FALLBACKS.store(0, Ordering::Relaxed);
}

// --- COMPARE MODE -----------------------------------------------------------
//
// The prereg's NO-GO is "more than 20 rules whose behaviour CHANGES". The
// at-risk instrument (`effect_audit::multi_binding_stats`) counts rules that
// commit >=2 bindings in one drain, which is an UPPER BOUND on that — two
// bindings may touch disjoint state and be perfectly order-independent. Quoting
// the upper bound as if it were the gate's own quantity would be the same
// category error as quoting a tie COUNT as a defect count.
//
// Compare mode measures the real thing. For each drain it derives every binding
// against the base (Stage A), undoes, then runs the COMMITTED path and captures
// what that produced. Differing write lists are recorded BY RULE NAME. The
// committed result is what stays in the graph, so this changes no behaviour: it
// is an instrument, and it costs roughly double.
static COMPARE: AtomicBool = AtomicBool::new(false);
static COMPARED_DRAINS: AtomicU64 = AtomicU64::new(0);
static DIVERGED_DRAINS: AtomicU64 = AtomicU64::new(0);
static DIVERGED_RULES: std::sync::Mutex<Vec<String>> = std::sync::Mutex::new(Vec::new());
/// Up to `SAMPLES_PER_RULE` worked examples per diverging rule: the Stage A
/// write list and the committed one, verbatim. A divergence COUNT says only
/// that something changed; the residual has to be READ to be explained, and
/// this repo's own baseline lesson is that a characterisation can be held while
/// a list has to be looked at.
static SAMPLES: std::sync::Mutex<Vec<(String, String, String)>> =
    std::sync::Mutex::new(Vec::new());
const SAMPLES_PER_RULE: usize = 3;

static COMPARE_ENV: std::sync::OnceLock<bool> = std::sync::OnceLock::new();

pub fn compare_mode() -> bool {
    if COMPARE.load(Ordering::Relaxed) {
        return true;
    }
    *COMPARE_ENV.get_or_init(|| {
        matches!(
            std::env::var("OZMA_STAGE_A_COMPARE").unwrap_or_default().as_str(),
            "1" | "true" | "on" | "yes"
        )
    })
}

pub fn set_compare_mode(on: bool) {
    COMPARE.store(on, Ordering::Relaxed);
}

static UNSOUND_DRAINS: AtomicU64 = AtomicU64::new(0);
static UNSOUND_RULES: std::sync::Mutex<Vec<String>> = std::sync::Mutex::new(Vec::new());

/// `(unsound_drains, unsound_rule_names)` — drains that DIVERGED from the
/// committed engine and that `conflicts` did NOT flag, i.e. cases Stage A would
/// have committed while being wrong. **This is the soundness property**: the
/// guard is sound exactly when this is zero. A fallback count merely close to
/// the divergence count proves nothing; the two sets have to be compared.
pub fn unsound_stats() -> (u64, Vec<String>) {
    (
        UNSOUND_DRAINS.load(Ordering::Relaxed),
        UNSOUND_RULES.lock().map(|n| n.clone()).unwrap_or_default(),
    )
}

/// Record one drain's Stage-A-vs-committed comparison.
pub fn record_comparison(rule: &str, stage_a: &[Proposal], committed: &[Proposal]) {
    COMPARED_DRAINS.fetch_add(1, Ordering::Relaxed);
    let a = format!("{:?}", stage_a.iter().map(|p| &p.writes).collect::<Vec<_>>());
    let c = format!("{:?}", committed.iter().map(|p| &p.writes).collect::<Vec<_>>());
    if a == c {
        return;
    }
    DIVERGED_DRAINS.fetch_add(1, Ordering::Relaxed);
    if !conflicts(stage_a) {
        // Diverged, and the guard would NOT have caught it.
        UNSOUND_DRAINS.fetch_add(1, Ordering::Relaxed);
        if let Ok(mut u) = UNSOUND_RULES.lock() {
            if !u.iter().any(|n| n == rule) {
                u.push(rule.to_string());
            }
        }
    }
    if let Ok(mut names) = DIVERGED_RULES.lock() {
        if !names.iter().any(|n| n == rule) {
            names.push(rule.to_string());
        }
    }
    if let Ok(mut samples) = SAMPLES.lock() {
        let seen = samples.iter().filter(|(r, _, _)| r == rule).count();
        if seen < SAMPLES_PER_RULE {
            samples.push((rule.to_string(), a, c));
        }
    }
}

/// Worked examples of divergence: `(rule, stage_a_writes, committed_writes)`.
pub fn compare_samples() -> Vec<(String, String, String)> {
    SAMPLES.lock().map(|s| s.clone()).unwrap_or_default()
}

/// `(compared_drains, diverged_drains, diverged_rule_names)`.
pub fn compare_stats() -> (u64, u64, Vec<String>) {
    (
        COMPARED_DRAINS.load(Ordering::Relaxed),
        DIVERGED_DRAINS.load(Ordering::Relaxed),
        DIVERGED_RULES.lock().map(|n| n.clone()).unwrap_or_default(),
    )
}

pub fn compare_reset() {
    COMPARED_DRAINS.store(0, Ordering::Relaxed);
    DIVERGED_DRAINS.store(0, Ordering::Relaxed);
    if let Ok(mut n) = DIVERGED_RULES.lock() {
        n.clear();
    }
    if let Ok(mut s) = SAMPLES.lock() {
        s.clear();
    }
    UNSOUND_DRAINS.store(0, Ordering::Relaxed);
    if let Ok(mut u) = UNSOUND_RULES.lock() {
        u.clear();
    }
}

pub fn note_excluded_drain() {
    EXCLUDED_DRAINS.fetch_add(1, Ordering::Relaxed);
}

/// True when an effect term reads the very attribute key its effect writes.
///
/// This is the whole read-write test, and it is deliberately not split by WHERE
/// the read happens, because both divergence shapes reduce to it:
///
///   * PROPAGATION — writes `K` on one node, reads `K` off ANOTHER (a neighbour,
///     another bound var). `mo_flood` is this: proposals write disjoint cells
///     and read each other's `mlabel`.
///   * FOLD — writes `K` on a node, reads `K` off the SAME node, across
///     different bindings. `adaptive_control_assign_discounted_credit` is this:
///     each binding adds to what the previous wrote.
///
/// A first pass at this dismissed FOLD as "plain counters, already caught by the
/// write-set relation". That was wrong — `STAGE_A_RESULTS.md` §5c calls it "this
/// one is real", and it is four times commoner than propagation in this tree
/// (12.6% of seed rules against 3.2%).
fn effect_reads_what_it_writes(arena: &crate::term::TermArena, root: TermIdx, key: Sym) -> bool {
    let mut stack = vec![root];
    while let Some(t) = stack.pop() {
        let node = arena.get(t);
        if let crate::term::TermNode::Attr { key: k, .. } = node {
            if *k == key {
                return true;
            }
        }
        stack.extend(crate::term::children(node));
    }
    false
}

/// True when this rule can be derived speculatively.
///
/// TWO exclusions, and the second is what `STAGE_A_RESULTS.md` §5f falsified the
/// whole scheme on.
///
/// 1. NODE DELETION — undo cannot restore a deleted node, and deriving against
///    one base requires undoing progressing firings too.
///
/// 2. READ-WRITE DEPENDENCE — an effect that reads the attribute key it writes.
///    `conflicts()` compares WRITE sets, so it is blind to a read-write
///    dependency by construction, and §5f established that no refinement of a
///    write-set relation can see one. The doc's remedy is per-proposal READ
///    sets, which means instrumenting every graph read during effect evaluation
///    — the hottest path in the engine.
///
///    But Stage A does not have to DECIDE these rules, only to REFUSE them, and
///    refusing needs no instrumentation at all: the dependency is visible in the
///    rule's own Term tree. Measured over 3739 seed rules, that refuses 14.7%
///    and leaves 85.3% still speculable — and it catches every rule the doc
///    names that lives in a seed (`mo_flood`, `qf_relax`, and both fold cases).
///
///    HONEST LIMITS. This is SUFFICIENT for refusal, not a complete read-set
///    analysis. It does not see a CROSS-RULE dependency (rule A writes `K`, rule
///    B reads `K` in the same drain), and it cannot see rules that are not
///    Term-resident at all — `mv_relax` lives in `substrate.rs`, so no
///    inspection of effect terms reaches it.
pub fn rule_is_derivable(rule: &crate::rewrite::RewriteRule, arena: &crate::term::TermArena) -> bool {
    use crate::rewrite::{Effect, EffectArg};

    if rule
        .effects
        .iter()
        .any(|e| matches!(e, Effect::DelNode { .. }))
    {
        return false;
    }

    for e in &rule.effects {
        let (key, value) = match e {
            Effect::SetAttr { key, value, .. } => (*key, value),
            Effect::SetAttrIfDifferent { key, value, .. } => (*key, value),
            _ => continue,
        };
        if let EffectArg::Computed(t) = value {
            if effect_reads_what_it_writes(arena, *t, key) {
                return false;
            }
        }
    }
    true
}

/// Read the forward delta of a firing that has been applied but NOT yet undone.
///
/// `undo` is in application order, so walking it forwards and reading the graph
/// as it currently stands reconstructs what the firing actually did. This is
/// the inverse of the inverse, and it is why §A.2's observation that `UndoStep`
/// is "already correct enough" is the load-bearing one: the delta carrier was
/// already built, computed on the probe path, and thrown away.
pub fn capture(
    rule: &crate::rewrite::RewriteRule,
    undo: &[UndoStep],
    undo_src: &[u32],
    graph: &TypedGraph,
    progressed: bool,
) -> Proposal {
    let mut writes = Vec::with_capacity(undo.len());
    // derivation-time NodeID -> proposal slot, for nodes minted by this firing.
    let mut slots: FxHashMap<NodeID, usize> = FxHashMap::default();

    let as_ref = |nid: NodeID, slots: &FxHashMap<NodeID, usize>| -> Ref {
        match slots.get(&nid) {
            Some(&s) => Ref::Slot(s),
            None => Ref::Existing(nid),
        }
    };

    for (i, step) in undo.iter().enumerate() {
        match step {
            UndoStep::AddedNode(nid) => {
                let slot = slots.len();
                slots.insert(*nid, slot);
                let n = graph.node(*nid);
                let (type_, attrs) = (n.type_, n.attrs.clone());
                // Recover the effect that inserted this node so a CONDITIONAL
                // insert stays conditional in the proposal.
                let src = undo_src.get(i).copied().unwrap_or(u32::MAX) as usize;
                match rule.effects.get(src) {
                    Some(crate::rewrite::Effect::AddNodeIfAbsent { attrs: keyed, .. }) => {
                        // The author's own attr keys ARE the dedup key set.
                        let dedup: Vec<(Sym, Value)> = keyed
                            .iter()
                            .filter_map(|(k, _)| attrs.get(k).map(|v| (*k, v.clone())))
                            .collect();
                        writes.push(Write::AddNodeIfAbsent { slot, type_, dedup, attrs });
                    }
                    _ => writes.push(Write::AddNode { slot, type_, attrs }),
                }
            }
            UndoStep::AddedEdge(key) => {
                let attrs = graph
                    .edge_idx(key.src, key.edge_type, key.tgt)
                    .map(|idx| graph.edge_attrs(idx).clone())
                    .unwrap_or_default();
                writes.push(Write::AddEdge {
                    src: as_ref(key.src, &slots),
                    edge_type: key.edge_type,
                    tgt: as_ref(key.tgt, &slots),
                    attrs,
                });
            }
            UndoStep::DeletedEdge { src, edge_type, tgt, .. } => {
                writes.push(Write::DelEdge {
                    src: as_ref(*src, &slots),
                    edge_type: *edge_type,
                    tgt: as_ref(*tgt, &slots),
                });
            }
            UndoStep::AttrSet { nid, key, .. } => {
                // The NEW value is whatever the graph holds right now; the
                // UndoStep carries only the old one.
                let value = graph.node(*nid).attrs.get(key).cloned();
                writes.push(Write::SetAttr {
                    node: as_ref(*nid, &slots),
                    key: *key,
                    value,
                });
            }
            UndoStep::NodeDeleted => {
                // Unreachable for derivable rules (`rule_is_derivable` excludes
                // them). Kept explicit so a future effect that emits this step
                // fails loudly here rather than silently losing a delete.
                debug_assert!(false, "NodeDeleted captured for a rule that passed rule_is_derivable");
            }
        }
    }

    PROPOSALS.fetch_add(1, Ordering::Relaxed);
    WRITES.fetch_add(writes.len() as u64, Ordering::Relaxed);
    Proposal { writes, progressed }
}

/// Do these independently-derived proposals write the same place twice?
///
/// This is the **merge incompatibility relation**, and it is what makes
/// deriving against one base safe rather than merely tidy. Two proposals that
/// both write `(node, key)` were each computed without seeing the other, so
/// applying both in sequence keeps only the last — and if the rule was FOLDING
/// (each binding reading what the previous wrote, the accumulator shape) the
/// result is one increment instead of N.
///
/// Detecting it at derivation time beats detecting it statically: it asks what
/// the bindings ACTUALLY did on this graph, not what the rule might do on some
/// graph. A conflicting drain falls back to the committed sequential path, so
/// the engine declines to treat the set as independent rather than silently
/// getting it wrong.
///
/// Attribute writes are the load-bearing case. Repeating an identical edge
/// insert or delete is idempotent, so edges conflict only when one proposal
/// deletes an edge another adds.
pub fn conflicts(proposals: &[Proposal]) -> bool {
    // Pairwise NODE disjointness, not attribute disjointness.
    //
    // The attribute-level relation was measured UNSOUND: on the embodied
    // workload it flagged 14 of 49 diverging drains, letting 35 through. Those
    // are the "2 firings vs 1" shape — a binding that progresses against the
    // base but would NOT have progressed once a sibling's writes landed. Its
    // extra writes need not touch the same attribute as anything else, so an
    // attribute-keyed check cannot see it, yet the graph gains work the
    // committed engine never did.
    //
    // What those cases DO share is a node: the bindings of one drain
    // characteristically fan out from a hub, and every proposal touches it. So
    // the relation is: two proposals that touch any node in common are not
    // independent, because either one's writes may change whether the other
    // still applies. Freshly minted nodes are private to their proposal and
    // cannot collide, so they are excluded.
    //
    // This is deliberately conservative. It refuses drains that would in fact
    // have been fine, and it must: a relation whose job is to decline when it
    // cannot tell has to err toward declining, and there is no cheap way to
    // know whether a sibling's writes would have suppressed this binding
    // without computing exactly the thing Stage A exists to avoid computing.
    let touched = |p: &Proposal| -> rustc_hash::FxHashSet<u32> {
        let mut set: rustc_hash::FxHashSet<u32> = Default::default();
        let mut add = |r: &Ref| {
            if let Ref::Existing(nid) = r {
                set.insert(nid.0);
            }
        };
        for w in &p.writes {
            match w {
                Write::AddNode { .. } | Write::AddNodeIfAbsent { .. } => {}
                Write::AddEdge { src, tgt, .. } => { add(src); add(tgt); }
                Write::DelEdge { src, tgt, .. } => { add(src); add(tgt); }
                Write::SetAttr { node, .. } => add(node),
            }
        }
        set
    };
    let sets: Vec<_> = proposals.iter().map(touched).collect();
    for i in 0..sets.len() {
        for j in (i + 1)..sets.len() {
            if sets[i].intersection(&sets[j]).next().is_some() {
                return true;
            }
        }
    }
    false
}

static CONFLICT_FALLBACKS: AtomicU64 = AtomicU64::new(0);

pub fn note_conflict_fallback() {
    CONFLICT_FALLBACKS.fetch_add(1, Ordering::Relaxed);
}

pub fn conflict_fallbacks() -> u64 {
    CONFLICT_FALLBACKS.load(Ordering::Relaxed)
}

/// Apply a derived proposal at the application boundary.
pub fn commit(proposal: &Proposal, graph: &mut TypedGraph) {
    let mut minted: Vec<NodeID> = Vec::new();
    let resolve = |r: &Ref, minted: &Vec<NodeID>| -> Option<NodeID> {
        match r {
            Ref::Existing(nid) => Some(*nid),
            Ref::Slot(s) => minted.get(*s).copied(),
        }
    };
    for write in &proposal.writes {
        match write {
            Write::AddNode { type_, attrs, .. } => {
                let nid = graph.insert_node(*type_, attrs.clone());
                minted.push(nid);
            }
            Write::AddNodeIfAbsent { type_, dedup, attrs, .. } => {
                // Same subset semantics as the effect itself: an existing node
                // matches when it carries every dedup pair, and may carry more.
                let found = graph.nodes_of_type(*type_).into_iter().find(|cand| {
                    let cand_attrs = &graph.node(*cand).attrs;
                    dedup.iter().all(|(k, v)| cand_attrs.get(k) == Some(v))
                });
                let nid = match found {
                    Some(existing) => existing,
                    None => graph.insert_node(*type_, attrs.clone()),
                };
                minted.push(nid);
            }
            Write::AddEdge { src, edge_type, tgt, attrs } => {
                if let (Some(s), Some(t)) = (resolve(src, &minted), resolve(tgt, &minted)) {
                    let _ = graph.insert_edge(s, *edge_type, t, attrs.clone());
                }
            }
            Write::DelEdge { src, edge_type, tgt } => {
                if let (Some(s), Some(t)) = (resolve(src, &minted), resolve(tgt, &minted)) {
                    if let Some(idx) = graph.edge_idx(s, *edge_type, t) {
                        graph.delete_edge(idx);
                    }
                }
            }
            Write::SetAttr { node, key, value } => {
                if let Some(nid) = resolve(node, &minted) {
                    match value {
                        Some(v) => graph.set_node_attr(nid, *key, v.clone()),
                        None => graph.remove_node_attr(nid, *key),
                    }
                }
            }
        }
    }

}

#[cfg(test)]
mod tests {
    use super::*;

    /// Stage A must REFUSE a rule whose effect reads the key it writes.
    ///
    /// `STAGE_A_RESULTS.md` §5f falsified Stage A on exactly this: `mo_flood`'s
    /// proposals are write-disjoint and read-dependent, and `conflicts()`
    /// compares write sets, so no write-set relation can see it. Refusing needs
    /// no read-set instrumentation — the dependency is in the Term tree.
    #[test]
    fn a_rule_that_reads_the_key_it_writes_is_refused() {
        use crate::rewrite::{Effect, EffectArg, RewriteRule};
        let mut arena = crate::term::TermArena::new();
        let mut interner = crate::sym::Interner::default();
        let k = interner.intern("mlabel");
        let other = interner.intern("elsewhere");
        let v = interner.intern("R");

        let var = arena.add(crate::term::TermNode::Var { name: v });
        // reads `mlabel` — the FOLD/PROPAGATION shape
        let reads_same = arena.add(crate::term::TermNode::Attr { node: var, key: k });
        // reads a DIFFERENT key — independent, must stay derivable
        let reads_other = arena.add(crate::term::TermNode::Attr { node: var, key: other });

        let mk = |value| RewriteRule {
            effects: vec![Effect::SetAttr { var: v, key: k, value }],
            ..RewriteRule::default()
        };

        assert!(
            !rule_is_derivable(&mk(EffectArg::Computed(reads_same)), &arena),
            "a rule that reads the key it writes must be refused"
        );
        assert!(
            rule_is_derivable(&mk(EffectArg::Computed(reads_other)), &arena),
            "reading a DIFFERENT key is not a read-write dependency"
        );
        assert!(
            rule_is_derivable(&mk(EffectArg::Literal(crate::value::Value::Float(1.0))), &arena),
            "a literal write has nothing to read"
        );
    }
}
