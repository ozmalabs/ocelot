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
//! a failed insert — is gated behind [`correct_failed_effects`] and defaults
//! **OFF**, per VISION_PROTOCOL §9 (defaults preserve committed results) and
//! the `*_unsound` flag precedent in `substrate.rs`. Today's default is
//! byte-identical to the previous behaviour. Flipping it is a separate,
//! measured change: run with counting on, find whether the path fires at all,
//! and only then decide.
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
static CORRECT: AtomicBool = AtomicBool::new(false);

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
