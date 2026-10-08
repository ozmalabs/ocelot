//! `effect_audit` — the failed-effect instrument.
//!
//! # What this measures
//!
//! `apply_rule_full` applied effects and DISCARDED the result of the graph
//! mutation. At the `AddEdge` site (`rewrite.rs`) the sequence was:
//!
//! ```ignore
//! let pre_exists = graph.has_edge(s, edge_type, t);
//! let _ = graph.insert_edge(s, edge_type, t, attr_map);   // Result dropped
//! if !pre_exists { progressed = true; undo.push(AddedEdge(key)); }
//! ```
//!
//! `insert_edge` returns `Err(MissingSrc | MissingTgt)` when an endpoint does
//! not exist (`graph.rs`), which is REACHABLE inside one firing: an earlier
//! effect in the same rule may have deleted the node the later `AddEdge`
//! binds. When that happens the discarded `Err` produces three distinct
//! wrongs at once, not one:
//!
//! 1. the failure is SILENT — no error, no counter, no row;
//! 2. `pre_exists` is false, so the rule reports `progressed = true` for a
//!    mutation that did not occur — false progress, which the `run_rules`
//!    fixpoint reads as a reason to keep iterating;
//! 3. an `UndoStep::AddedEdge` is pushed for an edge that was never created —
//!    undo bookkeeping that does not correspond to graph state.
//!
//! (2) is the one with teeth: a rule that always fails this way always claims
//! progress, so the fixpoint runs to `max_steps` instead of settling.
//!
//! # Counting is unconditional; the CORRECTION is not
//!
//! The failure path is rare, so the counters below are incremented
//! unconditionally — one `Relaxed` add on a path that, in a healthy run,
//! never executes. A coverage gap must be a number, not an assumption.
//!
//! The behavioural correction — withholding `progressed` and the undo step on
//! a failed insert — is gated behind [`correct_failed_effects`]. It landed
//! **OFF**, per VISION_PROTOCOL §9, and was flipped **ON** only after the
//! measurement said the path does not fire: zero failed inserts and zero false
//! progress across a conversational workload and a 47-test rule-heavy slice
//! (`DECISION_LAYER_PREREG.md` §4.2). Because the corrected branch is reachable
//! only when an insert actually fails, a measured zero makes enabling it inert
//! on those paths by construction rather than by observation.
//!
//! # Testing the detector
//!
//! Per the `selector_audit.rs` principle — *a detector that has never fired
//! has not been tested* — this instrument needs no fault injector, because
//! the failure is directly constructible: a rule whose effect list deletes a
//! node and then adds an edge to it fires it on real machinery. See
//! `rewrite.rs::effect_audit_tests`.

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Mutex;

/// Edge insertions that returned `Err` and were discarded by the caller.
static FAILED_EDGE_INSERTS: AtomicU64 = AtomicU64::new(0);

/// The subset of the above that ALSO produced false progress: the edge did
/// not pre-exist, so the applier credited `progressed = true` and pushed an
/// undo step for a mutation that never happened. This is the count that
/// matters for fixpoint behaviour.
static FALSE_PROGRESS: AtomicU64 = AtomicU64::new(0);

/// First failure seen, retained verbatim for diagnosis.
static FIRST_ROW: Mutex<Option<String>> = Mutex::new(None);

/// When true, a failed insert withholds `progressed` and the undo step.
/// **Default false** — see the module note.
/// **Default ON as of the measurement in `DECISION_LAYER_PREREG.md` §4.2.** Measured
/// zero failed inserts and zero false progress across a conversational workload and a
/// 47-test rule-heavy slice, so enabling the correction changes no exercised behaviour
/// while removing a source of spurious fixpoint iteration. `rewrite.rs`'s red test still
/// proves the path fires when an effect list deletes an endpoint, so this is "no seed
/// rule does that today", not "unreachable".
static CORRECT: AtomicBool = AtomicBool::new(true);

/// Record a failed edge insertion. `false_progress` is true when the caller
/// would otherwise have credited progress for it.
pub fn record_failed_edge_insert(false_progress: bool, row: impl FnOnce() -> String) {
    FAILED_EDGE_INSERTS.fetch_add(1, Ordering::Relaxed);
    if false_progress {
        FALSE_PROGRESS.fetch_add(1, Ordering::Relaxed);
    }
    if let Ok(mut slot) = FIRST_ROW.lock() {
        if slot.is_none() {
            *slot = Some(row());
        }
    }
}

/// Whether the behavioural correction is enabled. Off by default.
pub fn correct_failed_effects() -> bool {
    CORRECT.load(Ordering::Relaxed)
}

/// Enable or disable the correction. Off preserves committed results exactly.
pub fn set_correct_failed_effects(on: bool) {
    CORRECT.store(on, Ordering::Relaxed);
}

/// `(failed_edge_inserts, false_progress, first_row)`.
pub fn stats() -> (u64, u64, Option<String>) {
    (
        FAILED_EDGE_INSERTS.load(Ordering::Relaxed),
        FALSE_PROGRESS.load(Ordering::Relaxed),
        FIRST_ROW.lock().ok().and_then(|s| s.clone()),
    )
}

pub fn reset() {
    FAILED_EDGE_INSERTS.store(0, Ordering::Relaxed);
    FALSE_PROGRESS.store(0, Ordering::Relaxed);
    if let Ok(mut slot) = FIRST_ROW.lock() {
        *slot = None;
    }
}

// ---------------------------------------------------------------------------
// PROBE EXACTNESS — is derivation already non-mutating?
//
// `run_rules`' cold path decides whether a binding progresses by APPLYING it
// and undoing when it did not (`rewrite.rs`). `DECISION_LAYER_PREREG.md` Stage
// A calls that mutate-during-derivation and proposes rebuilding the applier
// around an immutable base.
//
// Whether that rebuild is warranted turns on ONE fact nobody had measured:
// bindings are collected BEFORE any apply, so enumeration is already immutable,
// and the only cross-binding exposure left is whether `undo_apply` restores the
// graph EXACTLY. If it does, derivation is already effectively non-mutating and
// Stage A's case rests on the proposal-as-value, not on correctness. If it does
// not, there is a live state-corruption bug and the priority inverts.
//
// So: fingerprint before the probe apply, fingerprint after the undo, compare.
// `state_fingerprint` is the same whole-graph hash cycle detection trusts.
// OFF by default — it hashes the entire graph twice per rolled-back binding,
// which is far too expensive for the committed loop. This is an instrument, not
// a mode.
static PROBE_EXACTNESS: AtomicBool = AtomicBool::new(false);
static PROBES_CHECKED: AtomicU64 = AtomicU64::new(0);
static PROBES_DIRTY: AtomicU64 = AtomicU64::new(0);
/// Every rule whose rollback failed to restore the graph, deduped, in
/// first-seen order. An ENUMERATION, not a count: the prereg's own NO-GO
/// condition is that a semantic delta which cannot be listed rule-by-rule kills
/// the stage, and this repo's retracted-baseline lesson says a characterisation
/// can be held while a list has to be read.
static DIRTY_RULES: Mutex<Vec<String>> = Mutex::new(Vec::new());

pub fn probe_exactness() -> bool {
    PROBE_EXACTNESS.load(Ordering::Relaxed)
}

pub fn set_probe_exactness(on: bool) {
    PROBE_EXACTNESS.store(on, Ordering::Relaxed);
}

/// Record one rolled-back probe. `before`/`after` are whole-graph fingerprints
/// taken immediately before the speculative apply and immediately after the
/// undo.
pub fn record_probe_rollback(before: u64, after: u64, rule: impl FnOnce() -> String) {
    PROBES_CHECKED.fetch_add(1, Ordering::Relaxed);
    if before == after {
        return;
    }
    PROBES_DIRTY.fetch_add(1, Ordering::Relaxed);
    if let Ok(mut names) = DIRTY_RULES.lock() {
        let name = rule();
        if !names.iter().any(|n| n == &name) {
            names.push(name);
        }
    }
}

/// `(probes_checked, probes_dirty, dirty_rule_names)`.
pub fn probe_stats() -> (u64, u64, Vec<String>) {
    (
        PROBES_CHECKED.load(Ordering::Relaxed),
        PROBES_DIRTY.load(Ordering::Relaxed),
        DIRTY_RULES.lock().map(|n| n.clone()).unwrap_or_default(),
    )
}

pub fn probe_reset() {
    PROBES_CHECKED.store(0, Ordering::Relaxed);
    PROBES_DIRTY.store(0, Ordering::Relaxed);
    if let Ok(mut names) = DIRTY_RULES.lock() {
        names.clear();
    }
}

// ---------------------------------------------------------------------------
// SAME-ROUND VISIBILITY — the population Stage A would actually change.
//
// The probe-exactness measurement above found rollback exact on every probe, so
// apply-then-undo is wasteful rather than wrong. What genuinely mutates during
// derivation is the drain loop in `Substrate`: it applies EVERY progressing
// binding of a rule without breaking, so binding N+1's effect terms evaluate
// against binding N's committed writes.
//
// Stage A would make each pass derive against one immutable base, which changes
// behaviour for exactly those rules that drain more than one progressing
// binding in a single pass. `DECISION_LAYER_PREREG.md` §A.4 fixes the NO-GO at
// more than 20 such rules, so this counts them BY NAME.
//
// A rule appearing here is at RISK, not necessarily changed: two bindings may
// touch disjoint state and be order-independent. This is the upper bound on the
// affected population, which is the right thing to check a NO-GO against.
static MULTI_BINDING_RULES: Mutex<Vec<(String, u64)>> = Mutex::new(Vec::new());
static MULTI_BINDING_DRAINS: AtomicU64 = AtomicU64::new(0);

/// One drain of `rule` committed `n` progressing bindings (only called for n>=2).
pub fn record_multi_binding_drain(rule: &str, n: u64) {
    MULTI_BINDING_DRAINS.fetch_add(1, Ordering::Relaxed);
    if let Ok(mut rows) = MULTI_BINDING_RULES.lock() {
        if let Some(row) = rows.iter_mut().find(|(name, _)| name == rule) {
            if n > row.1 {
                row.1 = n;
            }
        } else {
            rows.push((rule.to_string(), n));
        }
    }
}

/// `(drains, [(rule_name, max_bindings_in_one_drain)])`.
pub fn multi_binding_stats() -> (u64, Vec<(String, u64)>) {
    (
        MULTI_BINDING_DRAINS.load(Ordering::Relaxed),
        MULTI_BINDING_RULES
            .lock()
            .map(|r| r.clone())
            .unwrap_or_default(),
    )
}

pub fn multi_binding_reset() {
    MULTI_BINDING_DRAINS.store(0, Ordering::Relaxed);
    if let Ok(mut rows) = MULTI_BINDING_RULES.lock() {
        rows.clear();
    }
}
