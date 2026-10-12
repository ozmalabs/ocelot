//! SCALE AUDIT — split the measured scale wall into COUNTED buckets.
//!
//! # Why this exists
//!
//! `VISION_VIDEO_PROBE_RESULTS.md` (merged `40318951`) measured the wall on real
//! frames — exponent **1.887**, one 1080p frame extrapolating to **164 hours** —
//! and named the cause as *"the PyO3 boundary and then an O(N²) drive"*. That is
//! **two** causes, and there is a plausible third. They have different fixes:
//!
//! | term | what it is | the tool |
//! |---|---|---|
//! | **F** | PyO3/FFI boundary: marshalling, per-item crossings | async Rust-resident collapse |
//! | **C** | genuine pairwise comparison | a proposal net (distillation) |
//! | **R** | redundant recomputation | foveated / incremental evaluation |
//!
//! Distilling a net would be an expensive mistake if half the wall were FFI. So
//! this module counts, and the counts decide.
//!
//! # Why COUNTS and not wall-clock
//!
//! `ENGINE_WINNER_VALUE_RESULTS.md` (merged `62fadd1a`) reported cost as counted
//! operations and **refused** wall-clock, having measured two verdict-identical
//! runs differing by **85 s, 1.66×, on machine load alone**.
//! `VISION_VIDEO_PROBE_RESULTS.md` §0.1 learned the same thing the hard way: its
//! absolute timings were taken under another agent's `pytest` and are
//! contaminated. Counts are load-independent, reproducible to the integer, and
//! attributable by a rule written down before they are taken
//! (`VISION_SCALE_SPLIT_PREREG.md` §3).
//!
//! # Why process-global atomics
//!
//! The `selector_audit.rs` precedent, for the same reason: an `EvalCtx` field
//! would make coverage depend on every construction site opting in — the
//! "instrument that was never wired up" failure this project has been bitten by
//! repeatedly (VISION_PROTOCOL §12, §12.1: eleven inert instruments). A global
//! read inside the hot path itself makes coverage structural rather than
//! remembered.
//!
//! # Default
//!
//! **OFF** (VISION_PROTOCOL §9 — defaults preserve committed results). When off,
//! the entire cost is one `Relaxed` atomic load per instrumented site: no counter
//! is incremented, no epoch set is touched, no allocation occurs.

use crate::term_variants::{NUM_TERM_VARIANTS, TERM_VARIANT_NAMES};
use std::cell::Cell;
use std::collections::BTreeMap;
use std::sync::atomic::{AtomicBool, AtomicU32, AtomicU64, AtomicU8, Ordering};
use std::sync::{Mutex, OnceLock};

const MODE_OFF: u8 = 0;
const MODE_ON: u8 = 1;

static MODE: AtomicU8 = AtomicU8::new(MODE_OFF);
static ENV_READ: OnceLock<()> = OnceLock::new();
static PER_RULE_MODE: AtomicBool = AtomicBool::new(false);
static RULE_STORE_STATE_CAPTURE_ENABLED: AtomicBool = AtomicBool::new(false);
static MODE_TRACE_ENABLED: AtomicBool = AtomicBool::new(false);
static MODE_TRACE: Mutex<Vec<String>> = Mutex::new(Vec::new());
static NEXT_AUDIT_STORE_ID: AtomicU64 = AtomicU64::new(1);
static NEXT_AUDIT_RULE_ID: AtomicU32 = AtomicU32::new(0);
static NAMESPACED_RULE_IDS: Mutex<BTreeMap<(u64, u32), u32>> = Mutex::new(BTreeMap::new());
static AUDIT_RULE_IDENTITIES: Mutex<BTreeMap<u32, (u64, u32)>> = Mutex::new(BTreeMap::new());
static PER_RULE_COUNTS: Mutex<BTreeMap<(u32, &'static str), u64>> = Mutex::new(BTreeMap::new());
static RULE_AUDIT_METADATA: Mutex<BTreeMap<u32, (u32, String, usize)>> =
    Mutex::new(BTreeMap::new());
/// Optional first-closure snapshots keyed by store instance. Each value holds
/// the graph and complete local rule-slot export observed at that store's first
/// instrumented execution in the current capture window.
static RULE_STORE_STATE_SNAPSHOTS: Mutex<BTreeMap<u64, serde_json::Value>> =
    Mutex::new(BTreeMap::new());
static AMBIGUOUS_RULE_AUDIT_IDS: Mutex<std::collections::BTreeSet<u32>> =
    Mutex::new(std::collections::BTreeSet::new());
/// Candidate tests keyed by `(native rule index, match-edge position)`. Kept
/// separate from the compact static-metric table because clause positions are
/// dynamic and this readout is only enabled for targeted matcher attribution.
static MATCH_CLAUSE_CANDIDATES: Mutex<BTreeMap<(u32, usize), u64>> = Mutex::new(BTreeMap::new());
/// Candidate expansions keyed by stable `(rule, src-var, edge-type, tgt-var)`
/// identity, so clause reordering does not change attribution.
static MATCH_EDGE_CANDIDATES: Mutex<BTreeMap<(u32, u32, u32, u32), (u64, u64)>> =
    Mutex::new(BTreeMap::new());
const NO_RULE: u32 = u32::MAX;

/// Allocate a process-unique identity for a rule-owning store. Forked
/// substrates intentionally receive a fresh identity even when their rules
/// and local indices are copied from the source.
pub fn new_rule_audit_store_id() -> u64 {
    NEXT_AUDIT_STORE_ID.fetch_add(1, Ordering::Relaxed)
}

/// Enable expensive, opt-in graph/rule state capture for matcher stores.
pub fn set_rule_store_state_capture_enabled(on: bool) {
    RULE_STORE_STATE_CAPTURE_ENABLED.store(on, Ordering::Relaxed);
}

pub fn rule_store_state_capture_enabled() -> bool {
    RULE_STORE_STATE_CAPTURE_ENABLED.load(Ordering::Relaxed)
}

pub fn reset_rule_store_state_snapshots() {
    if let Ok(mut snapshots) = RULE_STORE_STATE_SNAPSHOTS.lock() {
        snapshots.clear();
    }
}

pub fn rule_store_state_snapshot_needed(store_id: u64) -> bool {
    let _ = store_id;
    rule_store_state_capture_enabled()
}

/// Save the first graph and accumulate every distinct local rule slot observed
/// for a live store in this capture window. Scoped matcher calls can expose
/// disjoint slices of one persistent store, so a single first-call rule table
/// is not sufficient for identity reconciliation.
pub fn record_rule_store_state_snapshot(store_id: u64, state: serde_json::Value) {
    if !rule_store_state_capture_enabled() {
        return;
    }
    if let Ok(mut snapshots) = RULE_STORE_STATE_SNAPSHOTS.lock() {
        let Some(existing) = snapshots.get_mut(&store_id) else {
            snapshots.insert(store_id, state);
            return;
        };
        let Some(existing_rules) = existing
            .get_mut("rules")
            .and_then(serde_json::Value::as_array_mut)
        else {
            return;
        };
        let Some(incoming_rules) = state.get("rules").and_then(serde_json::Value::as_array) else {
            return;
        };
        for incoming in incoming_rules {
            let Some(local_index) = incoming.get("local_rule_index") else {
                continue;
            };
            if let Some(current) = existing_rules
                .iter_mut()
                .find(|row| row.get("local_rule_index") == Some(local_index))
            {
                let Some(definition) = incoming.get("definition") else {
                    continue;
                };
                if current.get("definition") == Some(definition) {
                    continue;
                }
                let initial = current
                    .get("definition")
                    .cloned()
                    .unwrap_or(serde_json::Value::Null);
                let observations = current.as_object_mut().map(|object| {
                    object
                        .entry("definition_observations")
                        .or_insert_with(|| serde_json::Value::Array(vec![initial]))
                });
                if let Some(serde_json::Value::Array(rows)) = observations {
                    if !rows.iter().any(|row| row == definition) {
                        rows.push(definition.clone());
                    }
                }
            } else {
                existing_rules.push(incoming.clone());
            }
        }
    }
}

pub fn rule_store_state_snapshots() -> Vec<(u64, String)> {
    RULE_STORE_STATE_SNAPSHOTS
        .lock()
        .map(|rows| {
            rows.iter()
                .map(|(&store, state)| (store, state.to_string()))
                .collect()
        })
        .unwrap_or_default()
}

fn namespaced_rule_id(store_id: u64, local_rule_i: u32) -> u32 {
    if let Ok(mut ids) = NAMESPACED_RULE_IDS.lock() {
        if let Some(&id) = ids.get(&(store_id, local_rule_i)) {
            return id;
        }
        let id = NEXT_AUDIT_RULE_ID.fetch_add(1, Ordering::Relaxed);
        if id != NO_RULE {
            ids.insert((store_id, local_rule_i), id);
            if let Ok(mut reverse) = AUDIT_RULE_IDENTITIES.lock() {
                reverse.insert(id, (store_id, local_rule_i));
            }
            return id;
        }
    }
    // Exhaustion or a poisoned lock must not silently alias another rule.
    NO_RULE
}

/// Return the process-local audit key for one store-qualified native rule.
pub fn rule_audit_id_for(store_id: u64, local_rule_i: u32) -> Option<u32> {
    let id = namespaced_rule_id(store_id, local_rule_i);
    (id != NO_RULE).then_some(id)
}

/// Source identity behind an exported audit ID: `(store_instance, local_rule_index)`.
pub fn rule_audit_identity_snapshot() -> Vec<(u32, u64, u32)> {
    AUDIT_RULE_IDENTITIES
        .lock()
        .map(|rows| {
            rows.iter()
                .map(|(&id, &(store, local))| (id, store, local))
                .collect()
        })
        .unwrap_or_default()
}

thread_local! {
/// Process-local audit ID currently being enumerated. Valid only inside a
/// rule attempt; exported identity snapshots map it to store plus local index.
    static CURRENT_RULE: Cell<u32> = const { Cell::new(NO_RULE) };
    /// Host-requested evaluation has no matcher owner and needs a separate cost
    /// category from a missing rule context inside matcher execution.
    static HOST_EVALUATION_DEPTH: Cell<u32> = const { Cell::new(0) };
}

pub struct HostEvaluationGuard;

impl Drop for HostEvaluationGuard {
    fn drop(&mut self) {
        HOST_EVALUATION_DEPTH.with(|depth| depth.set(depth.get().saturating_sub(1)));
    }
}

/// Mark a direct host-requested Term evaluation while per-rule tracking is
/// active. The instrumentation is inert in the default-off path.
pub fn host_evaluation_scope() -> Option<HostEvaluationGuard> {
    if !enabled() || !PER_RULE_MODE.load(Ordering::Relaxed) {
        return None;
    }
    HOST_EVALUATION_DEPTH.with(|depth| depth.set(depth.get().saturating_add(1)));
    Some(HostEvaluationGuard)
}

#[inline]
fn per_rule_bump(metric: &'static str, n: u64) {
    if n == 0 || !PER_RULE_MODE.load(Ordering::Relaxed) {
        return;
    }
    let rule = CURRENT_RULE.with(Cell::get);
    if rule == NO_RULE {
        return;
    }
    if AMBIGUOUS_RULE_AUDIT_IDS
        .lock()
        .map(|ids| ids.contains(&rule))
        .unwrap_or(true)
    {
        return;
    }
    if let Ok(mut counts) = PER_RULE_COUNTS.lock() {
        *counts.entry((rule, metric)).or_insert(0) += n;
    }
}

/// Enable attribution keyed by the native rule index. This is opt-in on top of
/// the ordinary scale audit because the exact per-event map updates add cost.
pub fn set_per_rule_enabled(on: bool) {
    PER_RULE_MODE.store(on, Ordering::Relaxed);
    trace_mode_transition("per_rule", on);
}

fn trace_mode_transition(gate: &str, on: bool) {
    if !MODE_TRACE_ENABLED.load(Ordering::Relaxed) {
        return;
    }
    if let Ok(mut rows) = MODE_TRACE.lock() {
        rows.push(format!(
            "{}:{on}:thread={:?}",
            gate,
            std::thread::current().id()
        ));
    }
}

pub fn mode_trace_set_enabled(on: bool) {
    MODE_TRACE_ENABLED.store(on, Ordering::Relaxed);
}

pub fn mode_trace_reset() {
    if let Ok(mut rows) = MODE_TRACE.lock() {
        rows.clear();
    }
}

pub fn mode_trace_snapshot() -> Vec<String> {
    MODE_TRACE
        .lock()
        .map(|rows| rows.clone())
        .unwrap_or_default()
}

/// `(rule_index, metric, count)` rows, sorted by rule index and metric.
pub fn per_rule_snapshot() -> Vec<(u32, String, u64)> {
    PER_RULE_COUNTS
        .lock()
        .map(|counts| {
            counts
                .iter()
                .map(|(&(rule, metric), &n)| (rule, metric.to_string(), n))
                .collect()
        })
        .unwrap_or_default()
}

/// Clear only the opt-in per-rule attribution table.
pub fn per_rule_reset() {
    if let Ok(mut counts) = PER_RULE_COUNTS.lock() {
        counts.clear();
    }
    CURRENT_RULE.with(|rule| rule.set(NO_RULE));
    if let Ok(mut counts) = MATCH_CLAUSE_CANDIDATES.lock() {
        counts.clear();
    }
    if let Ok(mut counts) = MATCH_EDGE_CANDIDATES.lock() {
        counts.clear();
    }
    if let Ok(mut metadata) = RULE_AUDIT_METADATA.lock() {
        metadata.clear();
    }
    if let Ok(mut ambiguous) = AMBIGUOUS_RULE_AUDIT_IDS.lock() {
        ambiguous.clear();
    }
    if let Ok(mut ids) = NAMESPACED_RULE_IDS.lock() {
        ids.clear();
    }
    if let Ok(mut identities) = AUDIT_RULE_IDENTITIES.lock() {
        identities.clear();
    }
}

/// `(rule_index, zero_based_match_edge_position, candidate_tests)` rows.
pub fn match_clause_candidate_snapshot() -> Vec<(u32, usize, u64)> {
    MATCH_CLAUSE_CANDIDATES
        .lock()
        .map(|counts| {
            counts
                .iter()
                .map(|(&(rule, clause), &n)| (rule, clause, n))
                .collect()
        })
        .unwrap_or_default()
}

/// `(rule, src-var sym, edge-type sym, tgt-var sym, expansion calls, candidates)`.
pub fn match_edge_candidate_snapshot() -> Vec<(u32, u32, u32, u32, u64, u64)> {
    MATCH_EDGE_CANDIDATES
        .lock()
        .map(|counts| {
            counts
                .iter()
                .map(|(&(rule, src, edge, tgt), &(calls, candidates))| {
                    (rule, src, edge, tgt, calls, candidates)
                })
                .collect()
        })
        .unwrap_or_default()
}

/// Attribute one `extend_each` candidate-set expansion to its semantic edge.
/// The edge identity remains stable when an anchor path changes join order.
#[inline]
pub fn match_edge_candidates(src: u32, edge: u32, tgt: u32, candidates: u64) {
    if !enabled() || !PER_RULE_MODE.load(Ordering::Relaxed) {
        return;
    }
    let rule = CURRENT_RULE.with(Cell::get);
    if rule == NO_RULE {
        return;
    }
    let valid = RULE_AUDIT_METADATA
        .lock()
        .ok()
        .and_then(|metadata| metadata.get(&rule).map(|(_, _, _)| ()))
        .is_some()
        && !AMBIGUOUS_RULE_AUDIT_IDS
            .lock()
            .map(|ids| ids.contains(&rule))
            .unwrap_or(true);
    if !valid {
        return;
    }
    if let Ok(mut counts) = MATCH_EDGE_CANDIDATES.lock() {
        let row = counts.entry((rule, src, edge, tgt)).or_insert((0, 0));
        row.0 = row.0.saturating_add(1);
        row.1 = row.1.saturating_add(candidates);
    }
}

// ---------------------------------------------------------------------------
// F — FFI / PyO3 BOUNDARY
//
// Charged ONLY what exists BECAUSE the call came from Python: the crossing, the
// argument unmarshalling, and the return-object construction. The underlying
// graph mutation is NOT charged here — it would happen in a Rust-resident loop
// too (see `GRAPH_WRITES`, which is deliberately outside the three-way split).
// ---------------------------------------------------------------------------

/// Entries into a `#[pymethods]` method from Python — boundary crossings.
static FFI_CALLS: AtomicU64 = AtomicU64::new(0);
/// Per-item units marshalled across: 1 for a scalar call, N for a bulk call.
static FFI_ITEMS: AtomicU64 = AtomicU64::new(0);
/// Python objects CONSTRUCTED to satisfy a return. This is the real marshalling
/// cost: `node()` materialises a full attribute dict (~10 objects) to read one
/// field, which is why the bulk accessors were added in the first place.
static FFI_PYOBJECTS: AtomicU64 = AtomicU64::new(0);

// ---------------------------------------------------------------------------
// C / R — MATCH ENUMERATION
//
// The C/R split is POSITIONAL and CONSERVATIVE (prereg §3): within one EPOCH
// (one Python→Rust call into a rule-running method) a rule's FIRST enumeration
// is charged to C, every LATER enumeration of the same rule in the same epoch to
// R. The mechanism targeted is `run_rules_opts`'s cold path, which enumerates
// EVERY binding, applies ONE, `break`s, and re-enumerates from scratch.
// ---------------------------------------------------------------------------

/// `(src, tgt)` candidate pairs produced by an `extend_each` expansion.
static CAND_ENUM: AtomicU64 = AtomicU64::new(0);
/// …of which reached via the both-unbound full scan of `edges_by_type`.
/// **Global by construction** — the hypothesis-(a) numerator.
static CAND_ENUM_SCAN: AtomicU64 = AtomicU64::new(0);
/// …of which reached by traversal from an already-bound node. **Local.**
static CAND_ENUM_LOCAL: AtomicU64 = AtomicU64::new(0);
/// …of which reached via the R10 `IndexJoinHint` probe. **Indexed.**
static CAND_ENUM_HINTED: AtomicU64 = AtomicU64::new(0);

/// Candidates enumerated on a rule's FIRST enumeration this epoch (→ C).
static CAND_ENUM_FIRST: AtomicU64 = AtomicU64::new(0);
/// Candidates enumerated on a REPEAT enumeration this epoch (→ R).
static CAND_ENUM_REPEAT: AtomicU64 = AtomicU64::new(0);

/// Candidate pairs actually tested in the `extend_each` loop.
static CAND_TESTED: AtomicU64 = AtomicU64::new(0);
/// Matcher candidate tests with no verified active rule identity.
static CAND_TESTED_UNATTRIBUTED: AtomicU64 = AtomicU64::new(0);
/// Candidates discarded by the bound-src/bound-tgt equality filter — enumerated
/// and then thrown away without any substantive test.
static CAND_REJECT_BOUND: AtomicU64 = AtomicU64::new(0);
/// Scoped matcher invocations routed through ownership-seeded candidate paths.
static SCOPED_LOCAL_RULE_MATCHES: AtomicU64 = AtomicU64::new(0);
static SCOPED_DECLARED_ANCHOR_MATCHES: AtomicU64 = AtomicU64::new(0);
static SCOPED_ANCHOR_REJECTED: AtomicU64 = AtomicU64::new(0);
static SCOPED_MT_SEEDED_RULE_MATCHES: AtomicU64 = AtomicU64::new(0);
static SCOPED_FULL_FALLBACK_RULE_MATCHES: AtomicU64 = AtomicU64::new(0);

/// Where-clause evaluations at the leaf (the substantive per-candidate test).
static WHERE_EVALS: AtomicU64 = AtomicU64::new(0);
/// …on a first enumeration (→ C).
static WHERE_EVALS_FIRST: AtomicU64 = AtomicU64::new(0);
/// …on a repeat enumeration (→ R).
static WHERE_EVALS_REPEAT: AtomicU64 = AtomicU64::new(0);
/// Where-clause evaluations that returned false.
static WHERE_REJECTS: AtomicU64 = AtomicU64::new(0);
/// Predicate-pushdown conjunct evaluations (prune before expanding).
static PUSHDOWN_EVALS: AtomicU64 = AtomicU64::new(0);
/// …that pruned the subtree.
static PUSHDOWN_PRUNES: AtomicU64 = AtomicU64::new(0);

/// Bindings that survived every filter and reached `visit` — the SURVIVORS.
/// `LEAF_VISITS / CAND_ENUM` is the selectivity that decides hypothesis (a).
static LEAF_VISITS: AtomicU64 = AtomicU64::new(0);
/// Bindings dropped because two vars collided on one node.
static VAR_COLLISIONS: AtomicU64 = AtomicU64::new(0);

/// `Binding` clones pushed into `run_rules_opts`'s collect-all vector — an
/// allocation count, reported under R.
static BINDINGS_CLONED: AtomicU64 = AtomicU64::new(0);
/// `apply_rule_full(record_undo = true)` applications that did NOT progress and
/// were rolled back — probe-then-rollback waste.
static APPLY_PROBE_ROLLBACKS: AtomicU64 = AtomicU64::new(0);
/// Rule enumerations begun (one per `match_rule_each` from the fixpoint).
static RULE_ENUMERATIONS: AtomicU64 = AtomicU64::new(0);
/// …of which were a REPEAT of a rule already enumerated this epoch.
static RULE_ENUMERATIONS_REPEAT: AtomicU64 = AtomicU64::new(0);

// ---------------------------------------------------------------------------
// OUTSIDE THE SPLIT — the irreducible substrate cost.
//
// Declared in the prereg as charged to NOTHING: a Rust-resident loop would
// perform these too, so folding them into any bucket would flatter that bucket.
// ---------------------------------------------------------------------------

/// Graph attribute writes performed via the Python boundary.
static GRAPH_WRITES: AtomicU64 = AtomicU64::new(0);
/// AddEdge effect insertion attempts inside the native rule executor. Kept
/// separate from GRAPH_WRITES, whose scope is graph mutations via the Python
/// boundary. Attempts include idempotent duplicate insertions.
static RULE_EFFECT_EDGE_INSERT_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
static RULE_EFFECT_EDGE_DELETES: AtomicU64 = AtomicU64::new(0);
static RULE_EFFECT_NODE_INSERTS: AtomicU64 = AtomicU64::new(0);
static RULE_EFFECT_NODE_DELETE_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
static RULE_EFFECT_ATTR_SET_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
static RULE_EFFECT_REPLACE_EDGE_DELETES: AtomicU64 = AtomicU64::new(0);
static RULE_EFFECT_REPLACE_EDGE_INSERT_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
static SCHEDULER_PASSES: AtomicU64 = AtomicU64::new(0);
static SCHEDULER_EXTERNAL_POLL_SLOTS: AtomicU64 = AtomicU64::new(0);
static SCHEDULER_FIXEDPOINT_PROBE_SLOTS: AtomicU64 = AtomicU64::new(0);
static SCHEDULER_DIRTY_VECTOR_SLOTS: AtomicU64 = AtomicU64::new(0);
static SCHEDULER_SELECTED_RULES: AtomicU64 = AtomicU64::new(0);
static SCHEDULER_PLAN_NS: AtomicU64 = AtomicU64::new(0);

/// Graph-scoped scheduler/deferred totals captured inside active run_rules
/// operations. Process-global audit counters remain available unchanged.
static SCOPED_WORK_AUDIT: Mutex<BTreeMap<(usize, &'static str), u64>> = Mutex::new(BTreeMap::new());

fn scoped_work_bump(name: &'static str, count: u64) {
    if count == 0 || !enabled() {
        return;
    }
    let scope = crate::access_trace::current_work_scope();
    if scope == 0 {
        return;
    }
    if let Ok(mut rows) = SCOPED_WORK_AUDIT.lock() {
        *rows.entry((scope, name)).or_insert(0) += count;
    }
}

pub fn scoped_work_snapshot(scope: usize) -> Vec<(String, u64)> {
    SCOPED_WORK_AUDIT
        .lock()
        .map(|rows| {
            rows.iter()
                .filter(|((row_scope, _), _)| *row_scope == scope)
                .map(|((_, name), count)| ((*name).to_string(), *count))
                .collect()
        })
        .unwrap_or_default()
}

pub fn scoped_work_snapshot_all() -> Vec<(usize, String, u64)> {
    SCOPED_WORK_AUDIT
        .lock()
        .map(|rows| {
            rows.iter()
                .map(|((scope, name), count)| (*scope, (*name).to_string(), *count))
                .collect()
        })
        .unwrap_or_default()
}

/// Record one entered monolithic fixpoint pass when the scale audit is on.
#[inline]
pub fn scheduler_pass_started() {
    crate::access_trace::note_work(19, crate::access_trace::NO_ID, 1);
    scoped_work_bump("scheduler_passes", 1);
    if enabled() {
        bump(&SCHEDULER_PASSES, 1);
    }
}

/// Record exact rule-slot inspections and dirty-rule selection work for one
/// monolithic scheduler decision. External polling scans the full live rule
/// vector; the fixed-point probe short-circuits; the dirty vector scan visits
/// every slot when the probe finds work.
#[inline]
pub fn scheduler_plan_completed(
    external_poll_slots: usize,
    fixedpoint_probe_slots: usize,
    dirty_vector_slots: usize,
    selected_rules: usize,
    elapsed_ns: u64,
) {
    crate::access_trace::note_work(20, crate::access_trace::NO_ID, external_poll_slots as u64);
    crate::access_trace::note_work(
        21,
        crate::access_trace::NO_ID,
        fixedpoint_probe_slots as u64,
    );
    crate::access_trace::note_work(22, crate::access_trace::NO_ID, dirty_vector_slots as u64);
    crate::access_trace::note_work(23, crate::access_trace::NO_ID, selected_rules as u64);
    scoped_work_bump("scheduler_external_poll_slots", external_poll_slots as u64);
    scoped_work_bump(
        "scheduler_fixedpoint_probe_slots",
        fixedpoint_probe_slots as u64,
    );
    scoped_work_bump("scheduler_dirty_vector_slots", dirty_vector_slots as u64);
    scoped_work_bump("scheduler_selected_rules", selected_rules as u64);
    if !enabled() {
        return;
    }
    bump(&SCHEDULER_EXTERNAL_POLL_SLOTS, external_poll_slots as u64);
    bump(
        &SCHEDULER_FIXEDPOINT_PROBE_SLOTS,
        fixedpoint_probe_slots as u64,
    );
    bump(&SCHEDULER_DIRTY_VECTOR_SLOTS, dirty_vector_slots as u64);
    bump(&SCHEDULER_SELECTED_RULES, selected_rules as u64);
    bump(&SCHEDULER_PLAN_NS, elapsed_ns);
}

/// Family/action counters for work deferred from a rule firing and drained
/// between fixpoint passes. These are populated only while the scale audit is
/// enabled; family-level drain timing is separate from per-rule enqueue counts.
static DEFERRED_QUEUE_AUDIT: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());

fn deferred_bump(name: &'static str, count: u64) {
    if count == 0 || !enabled() {
        return;
    }
    if let Ok(mut rows) = DEFERRED_QUEUE_AUDIT.lock() {
        *rows.entry(name).or_insert(0) += count;
    }
}

/// Count one item enqueued by the currently enumerated rule, with a global
/// family total as well. Rule identity applies only to the producer; queue
/// drains are reported separately because current entries carry no origin UID.
pub fn deferred_queue_enqueued(family: &'static str) {
    crate::access_trace::note_work(24, deferred_family_id(family), 1);
    if !enabled() {
        return;
    }
    let name = match family {
        "rule_edits" => "deferred_queue:rule_edits:enqueued_items",
        "rule_patches" => "deferred_queue:rule_patches:enqueued_items",
        "fb_samples" => "deferred_queue:fb_samples:enqueued_items",
        "track_identity" => "deferred_queue:track_identity:enqueued_items",
        "net_collapses" => "deferred_queue:net_collapses:enqueued_items",
        _ => "deferred_queue:unknown:enqueued_items",
    };
    scoped_work_bump(name, 1);
    deferred_bump(name, 1);
    match family {
        "rule_edits" => per_rule_bump("deferred_queue_enqueued:rule_edits", 1),
        "rule_patches" => per_rule_bump("deferred_queue_enqueued:rule_patches", 1),
        "fb_samples" => per_rule_bump("deferred_queue_enqueued:fb_samples", 1),
        "track_identity" => per_rule_bump("deferred_queue_enqueued:track_identity", 1),
        "net_collapses" => per_rule_bump("deferred_queue_enqueued:net_collapses", 1),
        _ => per_rule_bump("deferred_queue_enqueued:unknown", 1),
    }
}

/// Record a completed between-pass drain. `items` counts dequeued records,
/// including records that are stale or rejected during application.
pub fn deferred_queue_drained(family: &'static str, items: usize, elapsed_ns: u64) {
    crate::access_trace::note_work(25, deferred_family_id(family), 1);
    crate::access_trace::note_work(26, deferred_family_id(family), items as u64);
    if !enabled() {
        return;
    }
    let (batches, drained, nanos) = match family {
        "rule_edits" => (
            "deferred_queue:rule_edits:drain_batches",
            "deferred_queue:rule_edits:drained_items",
            "deferred_queue:rule_edits:drain_ns",
        ),
        "rule_patches" => (
            "deferred_queue:rule_patches:drain_batches",
            "deferred_queue:rule_patches:drained_items",
            "deferred_queue:rule_patches:drain_ns",
        ),
        "fb_samples" => (
            "deferred_queue:fb_samples:drain_batches",
            "deferred_queue:fb_samples:drained_items",
            "deferred_queue:fb_samples:drain_ns",
        ),
        "track_identity" => (
            "deferred_queue:track_identity:drain_batches",
            "deferred_queue:track_identity:drained_items",
            "deferred_queue:track_identity:drain_ns",
        ),
        "net_collapses" => (
            "deferred_queue:net_collapses:drain_batches",
            "deferred_queue:net_collapses:drained_items",
            "deferred_queue:net_collapses:drain_ns",
        ),
        _ => (
            "deferred_queue:unknown:drain_batches",
            "deferred_queue:unknown:drained_items",
            "deferred_queue:unknown:drain_ns",
        ),
    };
    scoped_work_bump(batches, 1);
    scoped_work_bump(drained, items as u64);
    deferred_bump(batches, 1);
    deferred_bump(drained, items as u64);
    deferred_bump(nanos, elapsed_ns);
}

#[inline]
fn deferred_family_id(family: &'static str) -> u32 {
    match family {
        "rule_edits" => 1,
        "rule_patches" => 2,
        "fb_samples" => 3,
        "track_identity" => 4,
        "net_collapses" => 5,
        _ => u32::MAX,
    }
}

// ---------------------------------------------------------------------------
// T — TERM EVALUATION  (VISION_TERM_EVAL_COUNTER_PREREG.md §2)
//
// THE FOURTH TERM, AND THE REASON THIS MODULE WAS BLIND.
//
// Everything above counts GRAPH-LEVEL rule matching. `VISION_VIDEO_PROBE_RERUN_
// RESULTS.md` §3.1 measured what that misses: **a signature is an ATTRIBUTE, not
// a subgraph**, so on the sd/identity workload the matched graph is CONSTANT in
// N, every counter above is byte-identical across an 11.8x range of N, and
// wall-clock grows 13x anyway. The cost is inside Term evaluation. All four of
// that arm's pre-declared gates passed and the answer was still wrong.
//
// TWO FAMILIES, and the split is the whole point:
//
//   term_eval:<Variant>  INVOCATIONS. Charged at term.rs::evaluate's single
//                        dispatch point, so coverage is structural for all 175
//                        variants rather than dependent on per-variant opt-in.
//
//   term_unit:<Variant>  INTERIOR WORK UNITS. Sites define a unit locally
//                        (comparison, inspected neighbour/edge, predicate
//                        item, or sequence item) and attribute it to the
//                        INNERMOST variant currently evaluating. Compare a
//                        unit only within the same variant/site semantics.
//
// Why both: for a leaf (`Plus`, `Attr`) interior work is O(1), so invocations
// ARE the cost and `term_unit` is legitimately zero. For an aggregate
// (`ShapeDecode`) ONE invocation performs O(N*K) work, so an invocation count is
// ITSELF insensitive to N — it would reproduce the exact disease this instrument
// treats, one level finer. The prereg predicts (P1) that `term_eval:ShapeDecode`
// FAILS G5 on the sd axis, and that prediction is part of the design rather than
// a defect discovered afterwards.
// ---------------------------------------------------------------------------

/// Per-variant Term-evaluation invocation counts. Length is the enum's own
/// arity (`term_variants.rs`, generated) — not a chosen constant.
static TERM_EVALS: [AtomicU64; NUM_TERM_VARIANTS] =
    [const { AtomicU64::new(0) }; NUM_TERM_VARIANTS];
/// Term evaluations that could not be assigned to one verified rule identity.
/// Meaningful when per-rule auditing is enabled; otherwise zero by design.
static TERM_EVALS_UNATTRIBUTED: AtomicU64 = AtomicU64::new(0);
static TERM_EVALS_UNATTRIBUTED_HOST_API: AtomicU64 = AtomicU64::new(0);
static TERM_EVALS_UNATTRIBUTED_NO_RULE: AtomicU64 = AtomicU64::new(0);
static TERM_EVALS_UNATTRIBUTED_AMBIGUOUS: AtomicU64 = AtomicU64::new(0);
/// Per-variant interior work units, with site-defined units.
static TERM_UNITS: [AtomicU64; NUM_TERM_VARIANTS] =
    [const { AtomicU64::new(0) }; NUM_TERM_VARIANTS];

/// Sentinel for "no Term variant is currently evaluating" — a unit charged with
/// this on the stack has no innermost variant to attribute to and is counted in
/// `term_units_unattributed` rather than silently dropped or misfiled.
const NO_VARIANT: u16 = u16::MAX;

/// Units charged while no Term evaluation was in progress. Should be 0; a
/// non-zero value means an interior loop is reached from outside `evaluate` and
/// the attribution model needs revisiting. Reported, never hidden.
static TERM_UNITS_UNATTRIBUTED: AtomicU64 = AtomicU64::new(0);

thread_local! {
    /// The innermost `TermNode` variant currently being evaluated on THIS
    /// thread. Thread-local rather than atomic: it is a per-evaluation-stack
    /// fact, and the engine evaluates under the GIL, so an atomic would buy
    /// nothing and cost a contended write on the hottest path in the engine.
    static CURRENT_VARIANT: Cell<u16> = const { Cell::new(NO_VARIANT) };
}

/// RAII guard restoring the enclosing variant. A guard rather than a manual
/// restore because `evaluate` has early `return`s inside its match arms — a
/// hand-placed restore would be correct today and silently wrong the first time
/// somebody adds another one.
pub struct VariantGuard(u16);

impl Drop for VariantGuard {
    #[inline]
    fn drop(&mut self) {
        CURRENT_VARIANT.with(|c| c.set(self.0));
    }
}

/// Charge one Term-evaluation invocation to `variant`, and make it the innermost
/// variant for the duration of the returned guard. Returns `None` when the audit
/// is off, so the disabled cost is one relaxed load and no thread-local touch.
#[inline]
pub fn term_eval(variant: u16) -> Option<VariantGuard> {
    if !enabled() {
        return None;
    }
    if PER_RULE_MODE.load(Ordering::Relaxed) {
        let rule = CURRENT_RULE.with(Cell::get);
        if rule == NO_RULE {
            bump(&TERM_EVALS_UNATTRIBUTED, 1);
            if HOST_EVALUATION_DEPTH.with(|depth| depth.get() > 0) {
                bump(&TERM_EVALS_UNATTRIBUTED_HOST_API, 1);
            } else {
                bump(&TERM_EVALS_UNATTRIBUTED_NO_RULE, 1);
            }
        } else if AMBIGUOUS_RULE_AUDIT_IDS
            .lock()
            .map(|ids| ids.contains(&rule))
            .unwrap_or(true)
        {
            bump(&TERM_EVALS_UNATTRIBUTED, 1);
            bump(&TERM_EVALS_UNATTRIBUTED_AMBIGUOUS, 1);
        }
    }
    per_rule_bump("term_evaluations", 1);
    let i = variant as usize;
    if i < NUM_TERM_VARIANTS {
        bump(&TERM_EVALS[i], 1);
        per_rule_bump(TERM_VARIANT_NAMES[i], 1);
    }
    let prev = CURRENT_VARIANT.with(|c| {
        let p = c.get();
        c.set(variant);
        p
    });
    Some(VariantGuard(prev))
}

/// Charge `n` site-defined interior work units to the innermost variant currently
/// evaluating. Call once per loop with the count, not once per iteration — an
/// atomic per iteration would dominate the very work it is measuring. Unit
/// meanings are site-specific and should only be compared within that site.
#[inline]
pub fn term_units(n: u64) {
    if !enabled() || n == 0 {
        return;
    }
    per_rule_bump("term_units", n);
    let v = CURRENT_VARIANT.with(|c| c.get());
    if v == NO_VARIANT {
        bump(&TERM_UNITS_UNATTRIBUTED, n);
        return;
    }
    let i = v as usize;
    if i < NUM_TERM_VARIANTS {
        bump(&TERM_UNITS[i], n);
    }
}

// ---------------------------------------------------------------------------
// D — DISTINCT `DimInfer` ARGUMENTS  (VISION_DIM_INFER_ARGS_PREREG.md §2)
//
// THE QUESTION THIS ANSWERS. `VISION_IDENTITY_COST_ANATOMY_RESULTS.md` §5.4
// closed with the identity coefficient's one unexplained factor: `I` = 17
// invocations of `DimInfer` per recognising fixpoint, measured INVARIANT across
// 11.8x of N and 16x of K, and 2 on the novel path. Because the recognising
// path spends 8.5x more invocations than the failing one, `I` is what holds
// compute-proportional-to-surprise down to a magnitude of 1.33 even though the
// codebook fix corrected its SIGN. It is either 17 real decodes (irreducible)
// or 16 re-derivations (removable) and no existing counter can tell them apart:
// `term_eval:DimInfer` counts invocations, and every invocation counts the same
// whether or not it recomputes a value already computed.
//
// WHY A SET AND NOT A HASH. The specified test said "a hash of (residual,
// codebook, epoch)". A hash can COLLIDE, and a collision UNDER-counts distinct,
// which biases the measurement toward the re-derivation answer -- the more
// interesting one. This stores the EXACT canonical encoding, so under-counting
// is impossible by construction. The audit is off by default and the tuples are
// tens of KB, so the memory is irrelevant.
//
// WHY TWO SETS. Attempt ORDER genuinely affects `eval_dim_infer`'s answer
// (`best` is selected by `<`, first-seen wins on equality), so the ordered
// encoding is the complete determinant set. But codebook LOAD order is a
// graph-iteration fact that could churn with no semantic change, and encoding
// that churn would OVER-count -- biasing toward "irreducible". The unordered
// form (parts and generators canonically sorted) is therefore a LOWER BOUND,
// and both are reported. Neither is chosen after the fact.
//
// WHAT IS DELIBERATELY NOT IN THE TUPLE: `codebook_epoch`. It does not enter
// `eval_dim_infer` -- it is read by the RULES' `where` guards to decide whether
// to fire, never by the decode. Two invocations with identical decode arguments
// and different epochs return the SAME VALUE, so the second is redundant work
// regardless. Including it would inflate `distinct` for a reason unrelated to
// redundancy. This exclusion makes the "irreducible" verdict HARDER to reach,
// not easier.
// ---------------------------------------------------------------------------

/// Invocations reaching the `DimInfer` argument-recording site. MUST equal
/// `term_eval:DimInfer` (prereg §3.1) — if it does not, the site is not on the
/// path the invocation counter counts and the comparison to `I` is meaningless.
static DIM_INFER_ARG_CALLS: AtomicU64 = AtomicU64::new(0);

/// The distinct ORDERED argument encodings seen. Primary statistic.
static DIM_INFER_ARGS_ORDERED: Mutex<Vec<Vec<u8>>> = Mutex::new(Vec::new());
/// The distinct UNORDERED (canonically sorted) encodings. Lower bound.
static DIM_INFER_ARGS_UNORDERED: Mutex<Vec<Vec<u8>>> = Mutex::new(Vec::new());

// GenInfer search attribution. These sit at the operation itself rather than
// in EvalCtx: production rewrite effects construct EvalCtx at several paths,
// and an EvalCtx-only probe can silently miss the rule engine entirely.
static GEN_INFER_REQUESTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_CACHE_HITS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_KERNEL_CALLS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_ELIGIBLE_BASES: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_MATRIX_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_APPLY_REJECTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_CANDIDATE_REJECTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_RESIDUAL_REJECTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_CANDIDATE_SURVIVORS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_BASES_BY_BOUND: Mutex<BTreeMap<i64, u64>> = Mutex::new(BTreeMap::new());
static GEN_INFER_FULL_RANK_BASES: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_FULL_RANK_REFUSALS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_FULL_RANK_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_FULL_RANK_APPLY_REJECTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_FULL_RANK_CANDIDATE_REJECTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_FULL_RANK_RESIDUAL_REJECTS: AtomicU64 = AtomicU64::new(0);
static GEN_INFER_FULL_RANK_SURVIVORS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_SOLVED: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_NO_FIT: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_FALLBACK: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_INPUT_RELATIONS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_IDENTITY_VALUE_COMPARISONS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_EXACT_ARITHMETIC_CHECKS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_NO_FIT_REASONS: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_PREFILTER_FALLBACK_REASONS: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_ROWF_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_ROWF_SOLVED: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_ROWF_NO_CANDIDATE: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_ROWF_FALLBACK: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_ROWF_ROW_EVALUATIONS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_ROWF_NO_CANDIDATE_REASONS: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_ROWF_FALLBACK_REASONS: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_FOUND: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_NO_CANDIDATE: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_FALLBACK: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_HYPOTHESES: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_VALIDATIONS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_NO_CANDIDATE_REASONS: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());
#[cfg(feature = "geninfer_linear_exact_prefilter")]
static GEN_INFER_CORR_FALLBACK_REASONS: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());
#[cfg(feature = "geninfer_quadratic_map_solver")]
static GEN_INFER_QUADRATIC_ENABLED_CALLS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_quadratic_map_solver")]
static GEN_INFER_QUADRATIC_ATTEMPTS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_quadratic_map_solver")]
static GEN_INFER_QUADRATIC_VALIDATION_REJECTS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_quadratic_map_solver")]
static GEN_INFER_QUADRATIC_SURVIVORS: AtomicU64 = AtomicU64::new(0);
#[cfg(feature = "geninfer_quadratic_map_solver")]
static GEN_INFER_QUADRATIC_REFUSALS: Mutex<BTreeMap<&'static str, u64>> = Mutex::new(BTreeMap::new());
#[cfg(feature = "geninfer_full_rank_identity_join_work_audit")]
static GEN_INFER_FULL_RANK_IDENTITY_KEY_COMPARISONS: AtomicU64 = AtomicU64::new(0);

#[inline]
pub fn gen_infer_request() {
    if enabled() { bump(&GEN_INFER_REQUESTS, 1); }
}

#[inline]
pub fn gen_infer_cache_hit() {
    if enabled() { bump(&GEN_INFER_CACHE_HITS, 1); }
}

#[inline]
pub fn gen_infer_kernel_call() {
    if enabled() { bump(&GEN_INFER_KERNEL_CALLS, 1); }
}

pub fn gen_infer_search_result(
    eligible_bases: u64,
    matrix_attempts: u64,
    apply_rejects: u64,
    candidate_rejects: u64,
    residual_rejects: u64,
    candidate_survivors: u64,
    bases_by_bound: &rustc_hash::FxHashMap<i64, u64>,
) {
    if !enabled() { return; }
    bump(&GEN_INFER_ELIGIBLE_BASES, eligible_bases);
    bump(&GEN_INFER_MATRIX_ATTEMPTS, matrix_attempts);
    bump(&GEN_INFER_APPLY_REJECTS, apply_rejects);
    bump(&GEN_INFER_CANDIDATE_REJECTS, candidate_rejects);
    bump(&GEN_INFER_RESIDUAL_REJECTS, residual_rejects);
    bump(&GEN_INFER_CANDIDATE_SURVIVORS, candidate_survivors);
    if let Ok(mut totals) = GEN_INFER_BASES_BY_BOUND.lock() {
        for (bound, count) in bases_by_bound {
            *totals.entry(*bound).or_insert(0) += count;
        }
    }
}

pub fn gen_infer_full_rank_result(
    bases: u64,
    refusals: u64,
    attempts: u64,
    apply_rejects: u64,
    candidate_rejects: u64,
    residual_rejects: u64,
    survivors: u64,
) {
    if !enabled() { return; }
    bump(&GEN_INFER_FULL_RANK_BASES, bases);
    bump(&GEN_INFER_FULL_RANK_REFUSALS, refusals);
    bump(&GEN_INFER_FULL_RANK_ATTEMPTS, attempts);
    bump(&GEN_INFER_FULL_RANK_APPLY_REJECTS, apply_rejects);
    bump(&GEN_INFER_FULL_RANK_CANDIDATE_REJECTS, candidate_rejects);
    bump(&GEN_INFER_FULL_RANK_RESIDUAL_REJECTS, residual_rejects);
    bump(&GEN_INFER_FULL_RANK_SURVIVORS, survivors);
}

#[cfg(feature = "geninfer_linear_exact_prefilter")]
pub fn gen_infer_linear_prefilter_result(attempts: u64, solved: u64, no_fit: u64, fallback: u64, input_relations: u64,
    identity_comparisons: u64, arithmetic_checks: u64,
    no_fit_reasons: &rustc_hash::FxHashMap<&'static str,u64>, fallback_reasons: &rustc_hash::FxHashMap<&'static str,u64>) {
    if !enabled() { return; }
    bump(&GEN_INFER_PREFILTER_ATTEMPTS, attempts);
    bump(&GEN_INFER_PREFILTER_SOLVED, solved);
    bump(&GEN_INFER_PREFILTER_NO_FIT, no_fit);
    bump(&GEN_INFER_PREFILTER_FALLBACK, fallback);
    bump(&GEN_INFER_PREFILTER_INPUT_RELATIONS, input_relations);
    bump(&GEN_INFER_PREFILTER_IDENTITY_VALUE_COMPARISONS, identity_comparisons);
    bump(&GEN_INFER_PREFILTER_EXACT_ARITHMETIC_CHECKS, arithmetic_checks);
    if let Ok(mut totals)=GEN_INFER_PREFILTER_NO_FIT_REASONS.lock() { for (reason,count) in no_fit_reasons { *totals.entry(reason).or_insert(0)+=count; } }
    if let Ok(mut totals)=GEN_INFER_PREFILTER_FALLBACK_REASONS.lock() { for (reason,count) in fallback_reasons { *totals.entry(reason).or_insert(0)+=count; } }
}

#[cfg(feature = "geninfer_linear_exact_prefilter")]
pub fn gen_infer_row_factorized_result(attempts: u64, solved: u64, no_candidate: u64, fallback: u64, row_evaluations: u64,
    no_candidate_reasons: &rustc_hash::FxHashMap<&'static str,u64>, fallback_reasons: &rustc_hash::FxHashMap<&'static str,u64>) {
    if !enabled() { return; }
    bump(&GEN_INFER_ROWF_ATTEMPTS, attempts);
    bump(&GEN_INFER_ROWF_SOLVED, solved);
    bump(&GEN_INFER_ROWF_NO_CANDIDATE, no_candidate);
    bump(&GEN_INFER_ROWF_FALLBACK, fallback);
    bump(&GEN_INFER_ROWF_ROW_EVALUATIONS, row_evaluations);
    if let Ok(mut totals)=GEN_INFER_ROWF_NO_CANDIDATE_REASONS.lock() { for (reason,count) in no_candidate_reasons { *totals.entry(reason).or_insert(0)+=count; } }
    if let Ok(mut totals)=GEN_INFER_ROWF_FALLBACK_REASONS.lock() { for (reason,count) in fallback_reasons { *totals.entry(reason).or_insert(0)+=count; } }
}

#[cfg(feature = "geninfer_linear_exact_prefilter")]
#[allow(clippy::too_many_arguments)]
pub fn gen_infer_correspondence_result(attempts: u64, found: u64, no_candidate: u64, fallback: u64, hypotheses: u64, validations: u64,
    no_candidate_reasons: &rustc_hash::FxHashMap<&'static str,u64>, fallback_reasons: &rustc_hash::FxHashMap<&'static str,u64>) {
    if !enabled() { return; }
    bump(&GEN_INFER_CORR_ATTEMPTS, attempts);
    bump(&GEN_INFER_CORR_FOUND, found);
    bump(&GEN_INFER_CORR_NO_CANDIDATE, no_candidate);
    bump(&GEN_INFER_CORR_FALLBACK, fallback);
    bump(&GEN_INFER_CORR_HYPOTHESES, hypotheses);
    bump(&GEN_INFER_CORR_VALIDATIONS, validations);
    if let Ok(mut totals)=GEN_INFER_CORR_NO_CANDIDATE_REASONS.lock() { for (reason,count) in no_candidate_reasons { *totals.entry(reason).or_insert(0)+=count; } }
    if let Ok(mut totals)=GEN_INFER_CORR_FALLBACK_REASONS.lock() { for (reason,count) in fallback_reasons { *totals.entry(reason).or_insert(0)+=count; } }
}

#[cfg(feature = "geninfer_quadratic_map_solver")]
pub fn gen_infer_quadratic_result(
    quadratic_enabled: bool,
    attempts: u64,
    refusals: &rustc_hash::FxHashMap<&'static str, u64>,
    validation_rejects: u64,
    survivors: u64,
) {
    if !quadratic_enabled || !enabled() { return; }
    bump(&GEN_INFER_QUADRATIC_ENABLED_CALLS, 1);
    bump(&GEN_INFER_QUADRATIC_ATTEMPTS, attempts);
    bump(&GEN_INFER_QUADRATIC_VALIDATION_REJECTS, validation_rejects);
    bump(&GEN_INFER_QUADRATIC_SURVIVORS, survivors);
    if let Ok(mut totals) = GEN_INFER_QUADRATIC_REFUSALS.lock() {
        for (reason, count) in refusals { *totals.entry(reason).or_insert(0) += *count; }
    }
}

#[cfg(feature = "geninfer_full_rank_identity_join_work_audit")]
pub fn gen_infer_full_rank_identity_key_comparisons(comparisons: u64) {
    if enabled() { bump(&GEN_INFER_FULL_RANK_IDENTITY_KEY_COMPARISONS, comparisons); }
}

/// Record one `DimInfer` invocation's exact argument encoding, in both forms.
///
/// A `Vec<Vec<u8>>` with a linear membership test rather than a `HashSet`: `I`
/// is 17, the sets never exceed a few dozen entries in any measured workload,
/// and a linear scan over a handful of byte vectors keeps the structure exact
/// and trivially auditable. Should a workload ever push this to thousands of
/// distinct tuples, that fact is ITSELF the answer to the reducibility question
/// and the cost of finding it out is irrelevant.
pub fn dim_infer_args(ordered: Vec<u8>, unordered: Vec<u8>) {
    if !enabled() {
        return;
    }
    bump(&DIM_INFER_ARG_CALLS, 1);
    if let Ok(mut s) = DIM_INFER_ARGS_ORDERED.lock() {
        let idx = match s.iter().position(|e| *e == ordered) {
            Some(i) => i,
            None => {
                s.push(ordered);
                s.len() - 1
            }
        };
        if let Ok(mut t) = DIM_INFER_ARG_TRACE.lock() {
            t.push(idx as u32);
        }
    }
    if let Ok(mut s) = DIM_INFER_ARGS_UNORDERED.lock() {
        if !s.iter().any(|e| *e == unordered) {
            s.push(unordered);
        }
    }
}

/// DIAGNOSTIC, NOT A STATISTIC. Which distinct tuple each successive call
/// carried, in call order — so `[0,0,1,2,2,…]` says calls 1–2 shared a tuple,
/// call 3 introduced a second, and so on.
///
/// Added AFTER the headline (`distinct` = 10 against `I` = 17) was measured
/// and committed, so it can explain that number but cannot have shaped it.
/// It exists to answer the "name the mechanism" half of the brief: a
/// redundancy fraction with no account of WHICH invocations repeat is a number
/// nobody can act on.
static DIM_INFER_ARG_TRACE: Mutex<Vec<u32>> = Mutex::new(Vec::new());

/// The call-order trace of distinct-tuple indices.
pub fn dim_infer_arg_trace() -> Vec<u32> {
    DIM_INFER_ARG_TRACE
        .lock()
        .map(|t| t.clone())
        .unwrap_or_default()
}

/// The distinct ORDERED encodings themselves, so a diagnostic can diff them
/// and report WHICH determinant moved.
pub fn dim_infer_arg_encodings() -> Vec<Vec<u8>> {
    DIM_INFER_ARGS_ORDERED
        .lock()
        .map(|s| s.clone())
        .unwrap_or_default()
}

// ---------------------------------------------------------------------------
// EPOCHS
// ---------------------------------------------------------------------------

/// Python→Rust entries into a rule-running method (`tick` / `run_rules` /
/// `apply_rule_once`). One epoch = one such call.
static EPOCHS: AtomicU64 = AtomicU64::new(0);
/// …of which were `apply_rule_once` — the adapter's `_drive_phase` loop.
static EPOCHS_APPLY_ONCE: AtomicU64 = AtomicU64::new(0);
/// Candidates enumerated inside an `apply_rule_once` epoch. THE CROSS-EPOCH
/// REDUNDANCY MADE EXACT: `_drive_phase` runs `while apply_rule_once(idx): pass`,
/// so it makes ~M calls to apply M bindings and EVERY call re-derives the set
/// from scratch. The prereg keeps this OUT of R (so R stays a lower bound) and
/// requires it be reported SEPARATELY — this counter is that report, measured
/// rather than inferred.
static CAND_ENUM_APPLY_ONCE: AtomicU64 = AtomicU64::new(0);
/// Whether the epoch now open is an `apply_rule_once` epoch.
static IN_APPLY_ONCE: AtomicBool = AtomicBool::new(false);

/// Rules already enumerated in the CURRENT epoch. Touched only when enabled.
static EPOCH_RULES: Mutex<Vec<u32>> = Mutex::new(Vec::new());
/// Whether the enumeration now running is a REPEAT. Set by
/// `begin_rule_enumeration`, read by `extend_each`.
static CURRENT_IS_REPEAT: AtomicBool = AtomicBool::new(false);

fn init_from_env() {
    ENV_READ.get_or_init(|| {
        if let Ok(v) = std::env::var("OZMA_SCALE_AUDIT") {
            let m = match v.trim().to_ascii_lowercase().as_str() {
                "1" | "on" | "true" | "warn" => MODE_ON,
                _ => MODE_OFF,
            };
            MODE.store(m, Ordering::Relaxed);
        }
    });
}

/// The one hot-path read. `false` by default, so the disabled cost is a single
/// relaxed load per instrumented site.
#[inline(always)]
thread_local! {
    /// Per-thread enablement. See `set_enabled_for_thread`.
    static THREAD_ENABLED: std::cell::Cell<bool> = const { std::cell::Cell::new(false) };
}

pub fn enabled() -> bool {
    if THREAD_ENABLED.with(|c| c.get()) {
        return true;
    }
    init_from_env();
    MODE.load(Ordering::Relaxed) != MODE_OFF
}

/// Diagnostic state for proving which audit gates are active on the calling
/// thread. The tuple is `(process_mode, thread_override, per_rule_mode)`.
/// `enabled()` remains the authoritative effective process-or-thread gate.
pub fn mode_snapshot() -> (bool, bool, bool) {
    init_from_env();
    let process_mode = MODE.load(Ordering::Relaxed) != MODE_OFF;
    let thread_override = THREAD_ENABLED.with(Cell::get);
    let per_rule_mode = PER_RULE_MODE.load(Ordering::Relaxed);
    (process_mode, thread_override, per_rule_mode)
}

/// Enable recording FOR THE CALLING THREAD ONLY.
///
/// `set_enabled` flips a process-global mode, which is right for a real
/// measurement run and wrong for a test: every other thread in the process
/// starts recording into the same counters, so the reading measures whatever
/// the harness happened to be doing concurrently. Guarding the ENABLERS does
/// not fix that — the contributors are not the enablers, and there are ~780 of
/// them in this binary.
///
/// Thread enablement plus `exclusive()` is sound in-process: the guard
/// serialises the enabling tests against each other, and thread scope excludes
/// everyone else. Both are required; neither suffices alone.
///
/// Caveat, stated because it is a real limit and not a footnote: work a
/// measured call farms out to other threads (rayon) is NOT recorded under this
/// mode. It is therefore correct for the synthetic, single-threaded assertions
/// in this module's tests and NOT a substitute for `set_enabled` when
/// measuring real whole-process cost.
pub fn set_enabled_for_thread(on: bool) {
    THREAD_ENABLED.with(|c| c.set(on));
    trace_mode_transition("thread", on);
}

/// Test-facing setter (the harness's §6.1 zero-when-off gate flips this rather
/// than relying on process env, so ON and OFF are measurable in one process).
/// EXCLUSIVE ACCESS for anything that enables, resets, or snapshots this
/// instrument.
///
/// # Why a lock here and a witness elsewhere
///
/// These counters measure the process: FFI crossings, candidate enumeration,
/// per-variant Term evaluations. That is what they are FOR, so the reading is
/// only meaningful if it covers everything the process did — which means
/// storage cannot be made private per caller without destroying the
/// measurement. A whole-process measurement needs EXCLUSIVE ACCESS.
///
/// Contrast `DimInferWitness` (`term.rs`), which replaced this instrument for
/// the per-call distinct-argument measurement. That reading is a property of
/// ONE call, so attribution belongs with the call and private storage is
/// exactly right. Two different measurements, two different correct
/// mechanisms; the mistake was using process-global storage for the per-call
/// one.
///
/// # The invariant this guard depends on
///
/// It is sound only while EVERY enabler takes it. A lock covering some
/// enablers is worse than none, because it looks handled: the predecessor of
/// this arrangement was a module-local mutex in `dim_infer_tests` that
/// serialised six tests while thirty-nine others in the same module recorded
/// freely, and the gate failed intermittently for a year's worth of runs
/// without anyone reading it as contamination.
///
/// Current enablers: this module's own tests, the residual
/// `shape_decode` audit-silence test, and `py.rs`'s Python-facing setter
/// (production, never concurrent with tests). If you add one, take this guard.
pub fn exclusive() -> std::sync::MutexGuard<'static, ()> {
    static EXCLUSIVE: Mutex<()> = Mutex::new(());
    EXCLUSIVE.lock().unwrap_or_else(|e| e.into_inner())
}

pub fn set_enabled(on: bool) {
    init_from_env();
    MODE.store(if on { MODE_ON } else { MODE_OFF }, Ordering::Relaxed);
    trace_mode_transition("process", on);
}

#[inline(always)]
fn bump(c: &AtomicU64, n: u64) {
    c.fetch_add(n, Ordering::Relaxed);
}

// --- F ---------------------------------------------------------------------

/// One PyO3 boundary crossing carrying `items` marshalled units and
/// constructing `pyobjects` Python objects for the return.
#[inline]
pub fn ffi(items: u64, pyobjects: u64) {
    if !enabled() {
        return;
    }
    bump(&FFI_CALLS, 1);
    bump(&FFI_ITEMS, items);
    bump(&FFI_PYOBJECTS, pyobjects);
}

/// Graph writes performed under a boundary call — counted, but OUTSIDE the split.
#[inline]
pub fn graph_writes(n: u64) {
    if enabled() {
        bump(&GRAPH_WRITES, n);
    }
}

#[inline]
pub fn scoped_match_path(path: ScopedMatchPath) {
    if !enabled() {
        return;
    }
    match path {
        ScopedMatchPath::LocalOwnedEdge => {
            bump(&SCOPED_LOCAL_RULE_MATCHES, 1);
            per_rule_bump("scoped_path_local_owned_edge", 1);
        }
        ScopedMatchPath::DeclaredAnchor => {
            bump(&SCOPED_DECLARED_ANCHOR_MATCHES, 1);
            per_rule_bump("scoped_path_declared_anchor", 1);
        }
        ScopedMatchPath::AnchorRejected => {
            bump(&SCOPED_ANCHOR_REJECTED, 1);
            per_rule_bump("scoped_path_anchor_rejected", 1);
        }
        ScopedMatchPath::MicrotheorySeed => {
            bump(&SCOPED_MT_SEEDED_RULE_MATCHES, 1);
            per_rule_bump("scoped_path_microtheory_seed", 1);
        }
        ScopedMatchPath::FullFallback => {
            bump(&SCOPED_FULL_FALLBACK_RULE_MATCHES, 1);
            per_rule_bump("scoped_path_full_fallback", 1);
        }
    }
}

#[derive(Copy, Clone)]
pub enum ScopedMatchPath {
    LocalOwnedEdge,
    DeclaredAnchor,
    AnchorRejected,
    MicrotheorySeed,
    FullFallback,
}

#[inline]
pub fn rule_effect_edge_insert_attempt() {
    if enabled() {
        bump(&RULE_EFFECT_EDGE_INSERT_ATTEMPTS, 1);
        per_rule_bump("effect_edge_insert_attempts", 1);
    }
}

#[inline]
pub fn rule_effect_edge_delete() {
    if enabled() {
        bump(&RULE_EFFECT_EDGE_DELETES, 1);
        per_rule_bump("effect_edge_deletes", 1);
    }
}
#[inline]
pub fn rule_effect_node_insert() {
    if enabled() {
        bump(&RULE_EFFECT_NODE_INSERTS, 1);
        per_rule_bump("effect_node_inserts", 1);
    }
}
#[inline]
pub fn rule_effect_node_delete_attempt() {
    if enabled() {
        bump(&RULE_EFFECT_NODE_DELETE_ATTEMPTS, 1);
        per_rule_bump("effect_node_delete_attempts", 1);
    }
}
#[inline]
pub fn rule_effect_attr_set_attempt() {
    if enabled() {
        bump(&RULE_EFFECT_ATTR_SET_ATTEMPTS, 1);
        per_rule_bump("effect_attr_set_attempts", 1);
    }
}
#[inline]
pub fn rule_effect_replace_edge_delete() {
    if enabled() {
        bump(&RULE_EFFECT_REPLACE_EDGE_DELETES, 1);
        per_rule_bump("effect_replace_edge_deletes", 1);
    }
}
#[inline]
pub fn rule_effect_replace_edge_insert_attempt() {
    if enabled() {
        bump(&RULE_EFFECT_REPLACE_EDGE_INSERT_ATTEMPTS, 1);
        per_rule_bump("effect_replace_edge_insert_attempts", 1);
    }
}

// --- epochs ----------------------------------------------------------------

/// Open a new epoch: a Python→Rust call into a rule-running method.
pub fn begin_epoch() {
    begin_epoch_kind(false)
}

/// Open a new epoch, recording whether it is an `apply_rule_once` entry.
pub fn begin_epoch_kind(apply_once: bool) {
    if !enabled() {
        return;
    }
    bump(&EPOCHS, 1);
    IN_APPLY_ONCE.store(apply_once, Ordering::Relaxed);
    if apply_once {
        bump(&EPOCHS_APPLY_ONCE, 1);
    }
    if let Ok(mut s) = EPOCH_RULES.lock() {
        s.clear();
    }
    CURRENT_IS_REPEAT.store(false, Ordering::Relaxed);
}

/// Declare that `rule_i`'s bindings are about to be enumerated. Decides whether
/// the enumeration that follows is charged to C (first this epoch) or R (repeat).
pub fn begin_rule_enumeration(rule_i: u32) {
    begin_rule_enumeration_in_store(0, rule_i);
}

/// Begin enumeration for a local rule index owned by a specific store.
pub fn begin_rule_enumeration_in_store(store_id: u64, local_rule_i: u32) {
    if !enabled() {
        return;
    }
    let rule_i = if PER_RULE_MODE.load(Ordering::Relaxed) {
        namespaced_rule_id(store_id, local_rule_i)
    } else {
        local_rule_i
    };
    if rule_i == NO_RULE {
        CURRENT_RULE.with(|current| current.set(NO_RULE));
        return;
    }
    CURRENT_RULE.with(|current| current.set(rule_i));
    bump(&RULE_ENUMERATIONS, 1);
    per_rule_bump("rule_enumerations", 1);
    let repeat = match EPOCH_RULES.lock() {
        Ok(mut s) => {
            if s.contains(&rule_i) {
                true
            } else {
                s.push(rule_i);
                false
            }
        }
        // A poisoned lock must not silently re-classify work. Treat as FIRST —
        // the conservative direction, which understates R (prereg §3).
        Err(_) => false,
    };
    if repeat {
        bump(&RULE_ENUMERATIONS_REPEAT, 1);
    }
    CURRENT_IS_REPEAT.store(repeat, Ordering::Relaxed);
}

/// Register the pattern shape for a rule in the legacy namespace. New owners
/// should use `register_rule_audit_metadata_in_store` to prevent cross-store
/// collisions in process-global counters.
pub fn register_rule_audit_metadata(rule_i: u32, name_sym: u32, name: &str, match_arity: usize) {
    register_rule_audit_metadata_in_store(0, rule_i, name_sym, name, match_arity);
}

/// Register matcher metadata under a store-qualified local rule identity.
pub fn register_rule_audit_metadata_in_store(
    store_id: u64,
    local_rule_i: u32,
    name_sym: u32,
    name: &str,
    match_arity: usize,
) {
    if !enabled() || !PER_RULE_MODE.load(Ordering::Relaxed) {
        return;
    }
    let rule_i = namespaced_rule_id(store_id, local_rule_i);
    if rule_i == NO_RULE {
        return;
    }
    if let Ok(mut metadata) = RULE_AUDIT_METADATA.lock() {
        let next = (name_sym, name.to_owned(), match_arity);
        if let Some(previous) = metadata.get(&rule_i) {
            if previous != &next {
                if let Ok(mut ambiguous) = AMBIGUOUS_RULE_AUDIT_IDS.lock() {
                    ambiguous.insert(rule_i);
                }
                let mut invalidated = 0u64;
                if let Ok(mut clauses) = MATCH_CLAUSE_CANDIDATES.lock() {
                    let keys: Vec<_> = clauses
                        .keys()
                        .filter(|(id, _)| *id == rule_i)
                        .copied()
                        .collect();
                    for key in keys {
                        invalidated = invalidated.saturating_add(clauses.remove(&key).unwrap_or(0));
                    }
                }
                if let Ok(mut edges) = MATCH_EDGE_CANDIDATES.lock() {
                    edges.retain(|(id, _, _, _), _| *id != rule_i);
                }
                if let Ok(mut counts) = PER_RULE_COUNTS.lock() {
                    let keys: Vec<_> = counts
                        .keys()
                        .filter(|(id, _)| *id == rule_i)
                        .copied()
                        .collect();
                    let mut invalidated_terms = 0u64;
                    for key in keys {
                        let value = counts.remove(&key).unwrap_or(0);
                        if key.1 == "term_evaluations" {
                            invalidated_terms = invalidated_terms.saturating_add(value);
                        }
                    }
                    if invalidated_terms > 0 {
                        bump(&TERM_EVALS_UNATTRIBUTED, invalidated_terms);
                    }
                }
                if invalidated > 0 {
                    bump(&CAND_TESTED_UNATTRIBUTED, invalidated);
                }
            }
        } else {
            metadata.insert(rule_i, next);
        }
    }
}

/// Read metadata for the identities represented in the current audit window.
pub fn rule_audit_metadata_snapshot() -> Vec<(u32, u32, String, usize, bool)> {
    RULE_AUDIT_METADATA
        .lock()
        .map(|rows| {
            rows.iter()
                .map(|(&id, (name_sym, name, arity))| {
                    let ambiguous = AMBIGUOUS_RULE_AUDIT_IDS
                        .lock()
                        .map(|set| set.contains(&id))
                        .unwrap_or(true);
                    (id, *name_sym, name.clone(), *arity, ambiguous)
                })
                .collect()
        })
        .unwrap_or_default()
}

/// Return the rule context on this thread, if per-rule auditing is active.
/// Parallel matcher workers capture this before Rayon dispatch and rebind it
/// while evaluating their partition; reading a coordinator's thread-local
/// value from a worker would otherwise return that worker's stale context.
#[inline]
pub fn current_rule_index() -> Option<u32> {
    if !PER_RULE_MODE.load(Ordering::Relaxed) {
        return None;
    }
    CURRENT_RULE.with(|current| {
        let rule = current.get();
        (rule != NO_RULE).then_some(rule)
    })
}

/// Run work with an explicit native rule attribution on the current thread,
/// restoring the worker's prior context even when the callback unwinds.
#[inline]
pub fn with_rule_index<R>(rule_i: u32, f: impl FnOnce() -> R) -> R {
    struct RestoreRule(u32);
    impl Drop for RestoreRule {
        fn drop(&mut self) {
            CURRENT_RULE.with(|current| current.set(self.0));
        }
    }
    let previous = CURRENT_RULE.with(|current| current.replace(rule_i));
    let _restore = RestoreRule(previous);
    f()
}

/// Stop attributing work to the most recently enumerated rule. Call at the
/// end of each rule attempt so unrelated term evaluation cannot leak in.
#[inline]
pub fn end_rule_enumeration() {
    CURRENT_RULE.with(|current| current.set(NO_RULE));
}

#[inline(always)]
fn is_repeat() -> bool {
    CURRENT_IS_REPEAT.load(Ordering::Relaxed)
}

// --- C / R -----------------------------------------------------------------

/// How an `extend_each` expansion reached its candidate set.
pub enum CandPath {
    /// Traversal from an already-bound node (`neighbours` / `in_neighbours`).
    Local,
    /// The R10 `IndexJoinHint` probe.
    Hinted,
    /// The both-unbound full scan of `edges_by_type` — global by construction.
    Scan,
}

/// `n` candidates enumerated by one expansion, via `path`.
#[inline]
pub fn candidates(n: u64, path: CandPath) {
    if !enabled() || n == 0 {
        return;
    }
    bump(&CAND_ENUM, n);
    per_rule_bump("candidate_pairs", n);
    match path {
        CandPath::Local => bump(&CAND_ENUM_LOCAL, n),
        CandPath::Hinted => bump(&CAND_ENUM_HINTED, n),
        CandPath::Scan => bump(&CAND_ENUM_SCAN, n),
    }
    if is_repeat() {
        bump(&CAND_ENUM_REPEAT, n);
    } else {
        bump(&CAND_ENUM_FIRST, n);
    }
    if IN_APPLY_ONCE.load(Ordering::Relaxed) {
        bump(&CAND_ENUM_APPLY_ONCE, n);
    }
}

#[inline]
pub fn cand_tested(match_edge_position: usize, name_sym: u32, match_arity: usize) {
    if enabled() {
        bump(&CAND_TESTED, 1);
        if PER_RULE_MODE.load(Ordering::Relaxed) {
            let rule = CURRENT_RULE.with(Cell::get);
            let registered_identity = RULE_AUDIT_METADATA
                .lock()
                .ok()
                .and_then(|metadata| {
                    metadata
                        .get(&rule)
                        .map(|(expected_name, _, expected_arity)| {
                            *expected_name == name_sym && *expected_arity == match_arity
                        })
                })
                .unwrap_or(false);
            let ambiguous = AMBIGUOUS_RULE_AUDIT_IDS
                .lock()
                .map(|set| set.contains(&rule))
                .unwrap_or(true);
            let valid_identity = registered_identity && !ambiguous;
            if rule != NO_RULE && valid_identity && match_edge_position < match_arity {
                per_rule_bump("candidate_tests", 1);
                if let Ok(mut counts) = MATCH_CLAUSE_CANDIDATES.lock() {
                    *counts.entry((rule, match_edge_position)).or_insert(0) += 1;
                }
            } else {
                bump(&CAND_TESTED_UNATTRIBUTED, 1);
            }
        }
    }
}

#[inline]
pub fn cand_reject_bound() {
    if enabled() {
        bump(&CAND_REJECT_BOUND, 1);
    }
}

#[inline]
pub fn where_eval(passed: bool) {
    if !enabled() {
        return;
    }
    bump(&WHERE_EVALS, 1);
    per_rule_bump("where_evaluations", 1);
    if is_repeat() {
        bump(&WHERE_EVALS_REPEAT, 1);
    } else {
        bump(&WHERE_EVALS_FIRST, 1);
    }
    if !passed {
        bump(&WHERE_REJECTS, 1);
        per_rule_bump("where_rejections", 1);
    }
}

#[inline]
pub fn pushdown_eval(pruned: bool) {
    if !enabled() {
        return;
    }
    bump(&PUSHDOWN_EVALS, 1);
    per_rule_bump("pushdown_evaluations", 1);
    if pruned {
        bump(&PUSHDOWN_PRUNES, 1);
        per_rule_bump("pushdown_prunes", 1);
    }
}

#[inline]
pub fn leaf_visit() {
    if enabled() {
        bump(&LEAF_VISITS, 1);
        per_rule_bump("binding_leaves", 1);
    }
}

#[inline]
pub fn var_collision() {
    if enabled() {
        bump(&VAR_COLLISIONS, 1);
    }
}

#[inline]
pub fn binding_cloned() {
    if enabled() {
        bump(&BINDINGS_CLONED, 1);
        per_rule_bump("binding_clones", 1);
    }
}

#[inline]
pub fn apply_probe_rollback() {
    if enabled() {
        bump(&APPLY_PROBE_ROLLBACKS, 1);
    }
}

// --- readout ---------------------------------------------------------------

macro_rules! all_counters {
    ($f:ident) => {
        $f! {
            ffi_calls => FFI_CALLS,
            ffi_items => FFI_ITEMS,
            ffi_pyobjects => FFI_PYOBJECTS,
            cand_enum => CAND_ENUM,
            cand_enum_scan => CAND_ENUM_SCAN,
            cand_enum_local => CAND_ENUM_LOCAL,
            cand_enum_hinted => CAND_ENUM_HINTED,
            cand_enum_first => CAND_ENUM_FIRST,
            cand_enum_repeat => CAND_ENUM_REPEAT,
            cand_tested => CAND_TESTED,
            cand_tested_unattributed => CAND_TESTED_UNATTRIBUTED,
            term_evals_unattributed => TERM_EVALS_UNATTRIBUTED,
            term_evals_unattributed_host_api => TERM_EVALS_UNATTRIBUTED_HOST_API,
            term_evals_unattributed_no_rule => TERM_EVALS_UNATTRIBUTED_NO_RULE,
            term_evals_unattributed_ambiguous => TERM_EVALS_UNATTRIBUTED_AMBIGUOUS,
            cand_reject_bound => CAND_REJECT_BOUND,
            scoped_local_rule_matches => SCOPED_LOCAL_RULE_MATCHES,
            scoped_declared_anchor_rule_matches => SCOPED_DECLARED_ANCHOR_MATCHES,
            scoped_anchor_rejected_rule_matches => SCOPED_ANCHOR_REJECTED,
            scoped_mt_seeded_rule_matches => SCOPED_MT_SEEDED_RULE_MATCHES,
            scoped_full_fallback_rule_matches => SCOPED_FULL_FALLBACK_RULE_MATCHES,
            where_evals => WHERE_EVALS,
            where_evals_first => WHERE_EVALS_FIRST,
            where_evals_repeat => WHERE_EVALS_REPEAT,
            where_rejects => WHERE_REJECTS,
            pushdown_evals => PUSHDOWN_EVALS,
            pushdown_prunes => PUSHDOWN_PRUNES,
            leaf_visits => LEAF_VISITS,
            var_collisions => VAR_COLLISIONS,
            bindings_cloned => BINDINGS_CLONED,
            apply_probe_rollbacks => APPLY_PROBE_ROLLBACKS,
            rule_enumerations => RULE_ENUMERATIONS,
            rule_enumerations_repeat => RULE_ENUMERATIONS_REPEAT,
            graph_writes => GRAPH_WRITES,
            rule_effect_edge_insert_attempts => RULE_EFFECT_EDGE_INSERT_ATTEMPTS,
            rule_effect_edge_deletes => RULE_EFFECT_EDGE_DELETES,
            rule_effect_node_inserts => RULE_EFFECT_NODE_INSERTS,
            rule_effect_node_delete_attempts => RULE_EFFECT_NODE_DELETE_ATTEMPTS,
            rule_effect_attr_set_attempts => RULE_EFFECT_ATTR_SET_ATTEMPTS,
            rule_effect_replace_edge_deletes => RULE_EFFECT_REPLACE_EDGE_DELETES,
            rule_effect_replace_edge_insert_attempts => RULE_EFFECT_REPLACE_EDGE_INSERT_ATTEMPTS,
            scheduler_passes => SCHEDULER_PASSES,
            scheduler_external_poll_slots => SCHEDULER_EXTERNAL_POLL_SLOTS,
            scheduler_fixedpoint_probe_slots => SCHEDULER_FIXEDPOINT_PROBE_SLOTS,
            scheduler_dirty_vector_slots => SCHEDULER_DIRTY_VECTOR_SLOTS,
            scheduler_selected_rules => SCHEDULER_SELECTED_RULES,
            scheduler_plan_ns => SCHEDULER_PLAN_NS,
            epochs => EPOCHS,
            epochs_apply_once => EPOCHS_APPLY_ONCE,
            cand_enum_apply_once => CAND_ENUM_APPLY_ONCE,
            term_units_unattributed => TERM_UNITS_UNATTRIBUTED,
            dim_infer_arg_calls => DIM_INFER_ARG_CALLS,
        }
    };
}

/// The two distinct-argument cardinalities. Emitted UNCONDITIONALLY (unlike the
/// per-variant rows, which suppress zeros): "the site was never reached" and
/// "the family is missing" must stay distinguishable, and a distinctness gate
/// that silently omits its own row when it reads zero is the inert-instrument
/// failure in a new costume.
fn dim_infer_arg_rows(out: &mut Vec<(String, u64)>) {
    let o = DIM_INFER_ARGS_ORDERED.lock().map(|s| s.len()).unwrap_or(0) as u64;
    let u = DIM_INFER_ARGS_UNORDERED
        .lock()
        .map(|s| s.len())
        .unwrap_or(0) as u64;
    out.push(("dim_infer_arg_distinct_ordered".to_string(), o));
    out.push(("dim_infer_arg_distinct_unordered".to_string(), u));
}

/// Per-variant rows for the snapshot: `term_eval:<Variant>` /
/// `term_unit:<Variant>`.
///
/// **Only NON-ZERO cells are emitted.** 175 variants x 2 families is 350 rows,
/// of which a typical workload touches a couple of dozen; emitting the zeros
/// would bury the signal and make every readout O(350) to scan. The totals below
/// are emitted unconditionally, so "the family is present but everything is
/// zero" remains distinguishable from "the family is missing".
fn term_rows(out: &mut Vec<(String, u64)>) {
    let mut evals_total = 0u64;
    let mut units_total = 0u64;
    for i in 0..NUM_TERM_VARIANTS {
        let e = TERM_EVALS[i].load(Ordering::Relaxed);
        let u = TERM_UNITS[i].load(Ordering::Relaxed);
        evals_total += e;
        units_total += u;
        if e != 0 {
            out.push((format!("term_eval:{}", TERM_VARIANT_NAMES[i]), e));
        }
        if u != 0 {
            out.push((format!("term_unit:{}", TERM_VARIANT_NAMES[i]), u));
        }
    }
    out.push(("term_evals_total".to_string(), evals_total));
    out.push(("term_units_total".to_string(), units_total));
}

/// Every counter as `(name, value)`, sorted by name. The harness asserts the
/// prereg §6.4 conservation identities over this.
pub fn snapshot() -> Vec<(String, u64)> {
    macro_rules! collect {
        ($($name:ident => $st:ident,)*) => {{
            let mut v: Vec<(String, u64)> = vec![
                $((stringify!($name).to_string(), $st.load(Ordering::Relaxed)),)*
            ];
            term_rows(&mut v);
            dim_infer_arg_rows(&mut v);
            v.extend([
                ("gen_infer_requests".to_string(), GEN_INFER_REQUESTS.load(Ordering::Relaxed)),
                ("gen_infer_cache_hits".to_string(), GEN_INFER_CACHE_HITS.load(Ordering::Relaxed)),
                ("gen_infer_kernel_calls".to_string(), GEN_INFER_KERNEL_CALLS.load(Ordering::Relaxed)),
                ("gen_infer_eligible_bases".to_string(), GEN_INFER_ELIGIBLE_BASES.load(Ordering::Relaxed)),
                ("gen_infer_matrix_attempts".to_string(), GEN_INFER_MATRIX_ATTEMPTS.load(Ordering::Relaxed)),
                ("gen_infer_apply_rejects".to_string(), GEN_INFER_APPLY_REJECTS.load(Ordering::Relaxed)),
                ("gen_infer_candidate_rejects".to_string(), GEN_INFER_CANDIDATE_REJECTS.load(Ordering::Relaxed)),
                ("gen_infer_residual_rejects".to_string(), GEN_INFER_RESIDUAL_REJECTS.load(Ordering::Relaxed)),
                ("gen_infer_candidate_survivors".to_string(), GEN_INFER_CANDIDATE_SURVIVORS.load(Ordering::Relaxed)),
                ("gen_infer_full_rank_bases".to_string(), GEN_INFER_FULL_RANK_BASES.load(Ordering::Relaxed)),
                ("gen_infer_full_rank_refusals".to_string(), GEN_INFER_FULL_RANK_REFUSALS.load(Ordering::Relaxed)),
                ("gen_infer_full_rank_attempts".to_string(), GEN_INFER_FULL_RANK_ATTEMPTS.load(Ordering::Relaxed)),
                ("gen_infer_full_rank_apply_rejects".to_string(), GEN_INFER_FULL_RANK_APPLY_REJECTS.load(Ordering::Relaxed)),
                ("gen_infer_full_rank_candidate_rejects".to_string(), GEN_INFER_FULL_RANK_CANDIDATE_REJECTS.load(Ordering::Relaxed)),
                ("gen_infer_full_rank_residual_rejects".to_string(), GEN_INFER_FULL_RANK_RESIDUAL_REJECTS.load(Ordering::Relaxed)),
                ("gen_infer_full_rank_survivors".to_string(), GEN_INFER_FULL_RANK_SURVIVORS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_prefilter_attempts".to_string(), GEN_INFER_PREFILTER_ATTEMPTS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_prefilter_solved".to_string(), GEN_INFER_PREFILTER_SOLVED.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_prefilter_proven_no_fit".to_string(), GEN_INFER_PREFILTER_NO_FIT.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_prefilter_fallback".to_string(), GEN_INFER_PREFILTER_FALLBACK.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_prefilter_input_relations".to_string(), GEN_INFER_PREFILTER_INPUT_RELATIONS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_prefilter_identity_value_comparisons".to_string(), GEN_INFER_PREFILTER_IDENTITY_VALUE_COMPARISONS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_prefilter_exact_arithmetic_checks".to_string(), GEN_INFER_PREFILTER_EXACT_ARITHMETIC_CHECKS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_row_factorized_attempts".to_string(), GEN_INFER_ROWF_ATTEMPTS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_row_factorized_solved".to_string(), GEN_INFER_ROWF_SOLVED.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_row_factorized_no_candidate".to_string(), GEN_INFER_ROWF_NO_CANDIDATE.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_row_factorized_fallback".to_string(), GEN_INFER_ROWF_FALLBACK.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_row_factorized_row_evaluations".to_string(), GEN_INFER_ROWF_ROW_EVALUATIONS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_correspondence_attempts".to_string(), GEN_INFER_CORR_ATTEMPTS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_correspondence_found".to_string(), GEN_INFER_CORR_FOUND.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_correspondence_no_candidate".to_string(), GEN_INFER_CORR_NO_CANDIDATE.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_correspondence_fallback".to_string(), GEN_INFER_CORR_FALLBACK.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_correspondence_hypotheses".to_string(), GEN_INFER_CORR_HYPOTHESES.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_linear_exact_prefilter")]
                ("gen_infer_correspondence_validations".to_string(), GEN_INFER_CORR_VALIDATIONS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_quadratic_map_solver")]
                ("gen_infer_quadratic_enabled_calls".to_string(), GEN_INFER_QUADRATIC_ENABLED_CALLS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_quadratic_map_solver")]
                ("gen_infer_quadratic_attempts".to_string(), GEN_INFER_QUADRATIC_ATTEMPTS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_quadratic_map_solver")]
                ("gen_infer_quadratic_validation_rejects".to_string(), GEN_INFER_QUADRATIC_VALIDATION_REJECTS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_quadratic_map_solver")]
                ("gen_infer_quadratic_survivors".to_string(), GEN_INFER_QUADRATIC_SURVIVORS.load(Ordering::Relaxed)),
                #[cfg(feature = "geninfer_full_rank_identity_join_work_audit")]
                ("gen_infer_full_rank_identity_key_comparisons".to_string(), GEN_INFER_FULL_RANK_IDENTITY_KEY_COMPARISONS.load(Ordering::Relaxed)),
            ]);
            if let Ok(bounds) = GEN_INFER_BASES_BY_BOUND.lock() {
                v.extend(bounds.iter().map(|(bound, count)| (format!("gen_infer_bases_by_bound:{bound}"), *count)));
            }
            #[cfg(feature = "geninfer_linear_exact_prefilter")]
            if let Ok(reasons)=GEN_INFER_PREFILTER_NO_FIT_REASONS.lock() { v.extend(reasons.iter().map(|(r,n)|(format!("gen_infer_prefilter_proven_no_fit_reason:{r}"),*n))); }
            #[cfg(feature = "geninfer_linear_exact_prefilter")]
            if let Ok(reasons)=GEN_INFER_PREFILTER_FALLBACK_REASONS.lock() { v.extend(reasons.iter().map(|(r,n)|(format!("gen_infer_prefilter_fallback_reason:{r}"),*n))); }
            #[cfg(feature = "geninfer_linear_exact_prefilter")]
            if let Ok(reasons)=GEN_INFER_ROWF_NO_CANDIDATE_REASONS.lock() { v.extend(reasons.iter().map(|(r,n)|(format!("gen_infer_row_factorized_no_candidate_reason:{r}"),*n))); }
            #[cfg(feature = "geninfer_linear_exact_prefilter")]
            if let Ok(reasons)=GEN_INFER_ROWF_FALLBACK_REASONS.lock() { v.extend(reasons.iter().map(|(r,n)|(format!("gen_infer_row_factorized_fallback_reason:{r}"),*n))); }
            #[cfg(feature = "geninfer_linear_exact_prefilter")]
            if let Ok(reasons)=GEN_INFER_CORR_NO_CANDIDATE_REASONS.lock() { v.extend(reasons.iter().map(|(r,n)|(format!("gen_infer_correspondence_no_candidate_reason:{r}"),*n))); }
            #[cfg(feature = "geninfer_linear_exact_prefilter")]
            if let Ok(reasons)=GEN_INFER_CORR_FALLBACK_REASONS.lock() { v.extend(reasons.iter().map(|(r,n)|(format!("gen_infer_correspondence_fallback_reason:{r}"),*n))); }
            #[cfg(feature = "geninfer_quadratic_map_solver")]
            if let Ok(refusals) = GEN_INFER_QUADRATIC_REFUSALS.lock() {
                v.extend(refusals.iter().map(|(reason, count)| (format!("gen_infer_quadratic_refusal:{reason}"), *count)));
            }
            if let Ok(rows) = DEFERRED_QUEUE_AUDIT.lock() {
                v.extend(rows.iter().map(|(name, count)| ((*name).to_string(), *count)));
            }
            v.sort_by(|a, b| a.0.cmp(&b.0));
            v
        }};
    }
    all_counters!(collect)
}

/// Zero every counter and close any open epoch.
pub fn reset() {
    macro_rules! zero {
        ($($name:ident => $st:ident,)*) => {{
            $($st.store(0, Ordering::Relaxed);)*
        }};
    }
    all_counters!(zero);
    for counter in [
        &GEN_INFER_REQUESTS,
        &GEN_INFER_CACHE_HITS,
        &GEN_INFER_KERNEL_CALLS,
        &GEN_INFER_ELIGIBLE_BASES,
        &GEN_INFER_MATRIX_ATTEMPTS,
        &GEN_INFER_APPLY_REJECTS,
        &GEN_INFER_CANDIDATE_REJECTS,
        &GEN_INFER_RESIDUAL_REJECTS,
        &GEN_INFER_CANDIDATE_SURVIVORS,
        &GEN_INFER_FULL_RANK_BASES,
        &GEN_INFER_FULL_RANK_REFUSALS,
        &GEN_INFER_FULL_RANK_ATTEMPTS,
        &GEN_INFER_FULL_RANK_APPLY_REJECTS,
        &GEN_INFER_FULL_RANK_CANDIDATE_REJECTS,
        &GEN_INFER_FULL_RANK_RESIDUAL_REJECTS,
        &GEN_INFER_FULL_RANK_SURVIVORS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_PREFILTER_ATTEMPTS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_PREFILTER_SOLVED,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_PREFILTER_NO_FIT,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_PREFILTER_FALLBACK,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_PREFILTER_INPUT_RELATIONS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_PREFILTER_IDENTITY_VALUE_COMPARISONS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_PREFILTER_EXACT_ARITHMETIC_CHECKS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_ROWF_ATTEMPTS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_ROWF_SOLVED,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_ROWF_NO_CANDIDATE,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_ROWF_FALLBACK,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_ROWF_ROW_EVALUATIONS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_CORR_ATTEMPTS,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_CORR_FOUND,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_CORR_NO_CANDIDATE,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_CORR_FALLBACK,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_CORR_HYPOTHESES,
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        &GEN_INFER_CORR_VALIDATIONS,
        #[cfg(feature = "geninfer_quadratic_map_solver")]
        &GEN_INFER_QUADRATIC_ENABLED_CALLS,
        #[cfg(feature = "geninfer_quadratic_map_solver")]
        &GEN_INFER_QUADRATIC_ATTEMPTS,
        #[cfg(feature = "geninfer_quadratic_map_solver")]
        &GEN_INFER_QUADRATIC_VALIDATION_REJECTS,
        #[cfg(feature = "geninfer_quadratic_map_solver")]
        &GEN_INFER_QUADRATIC_SURVIVORS,
        #[cfg(feature = "geninfer_full_rank_identity_join_work_audit")]
        &GEN_INFER_FULL_RANK_IDENTITY_KEY_COMPARISONS,
    ] {
        counter.store(0, Ordering::Relaxed);
    }
    if let Ok(mut bounds) = GEN_INFER_BASES_BY_BOUND.lock() { bounds.clear(); }
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    if let Ok(mut reasons)=GEN_INFER_PREFILTER_NO_FIT_REASONS.lock() { reasons.clear(); }
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    if let Ok(mut reasons)=GEN_INFER_PREFILTER_FALLBACK_REASONS.lock() { reasons.clear(); }
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    if let Ok(mut reasons)=GEN_INFER_ROWF_NO_CANDIDATE_REASONS.lock() { reasons.clear(); }
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    if let Ok(mut reasons)=GEN_INFER_ROWF_FALLBACK_REASONS.lock() { reasons.clear(); }
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    if let Ok(mut reasons)=GEN_INFER_CORR_NO_CANDIDATE_REASONS.lock() { reasons.clear(); }
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    if let Ok(mut reasons)=GEN_INFER_CORR_FALLBACK_REASONS.lock() { reasons.clear(); }
    #[cfg(feature = "geninfer_quadratic_map_solver")]
    if let Ok(mut refusals) = GEN_INFER_QUADRATIC_REFUSALS.lock() { refusals.clear(); }
    for i in 0..NUM_TERM_VARIANTS {
        TERM_EVALS[i].store(0, Ordering::Relaxed);
        TERM_UNITS[i].store(0, Ordering::Relaxed);
    }
    CURRENT_VARIANT.with(|c| c.set(NO_VARIANT));
    if let Ok(mut s) = EPOCH_RULES.lock() {
        s.clear();
    }
    CURRENT_IS_REPEAT.store(false, Ordering::Relaxed);
    per_rule_reset();
    if let Ok(mut rows) = DEFERRED_QUEUE_AUDIT.lock() {
        rows.clear();
    }
    if let Ok(mut rows) = SCOPED_WORK_AUDIT.lock() {
        rows.clear();
    }
    IN_APPLY_ONCE.store(false, Ordering::Relaxed);
    if let Ok(mut s) = DIM_INFER_ARGS_ORDERED.lock() {
        s.clear();
    }
    if let Ok(mut s) = DIM_INFER_ARGS_UNORDERED.lock() {
        s.clear();
    }
    if let Ok(mut t) = DIM_INFER_ARG_TRACE.lock() {
        t.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mode_snapshot_distinguishes_process_and_thread_gates() {
        let _x = super::exclusive();
        set_enabled(false);
        set_enabled_for_thread(false);
        set_per_rule_enabled(false);
        assert_eq!(mode_snapshot(), (false, false, false));
        set_enabled_for_thread(true);
        assert_eq!(mode_snapshot(), (false, true, false));
        set_per_rule_enabled(true);
        assert_eq!(mode_snapshot(), (false, true, true));
        set_enabled_for_thread(false);
        set_enabled(true);
        assert_eq!(mode_snapshot(), (true, false, true));
        set_per_rule_enabled(false);
        set_enabled(false);
        assert_eq!(mode_snapshot(), (false, false, false));
    }

    #[test]
    fn host_term_evaluation_is_separate_from_missing_rule_context() {
        let _x = super::exclusive();
        set_enabled(true);
        set_per_rule_enabled(true);
        reset();
        {
            let _host = host_evaluation_scope().expect("audit is enabled");
            let _term = term_eval(0);
        }
        let counts: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(counts["term_evals_unattributed"], 1);
        assert_eq!(counts["term_evals_unattributed_host_api"], 1);
        assert_eq!(counts["term_evals_unattributed_no_rule"], 0);
        reset();
        let _term = term_eval(0);
        let counts: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(counts["term_evals_unattributed"], 1);
        assert_eq!(counts["term_evals_unattributed_host_api"], 0);
        assert_eq!(counts["term_evals_unattributed_no_rule"], 1);
        set_per_rule_enabled(false);
        set_enabled(false);
        reset();
    }

    /// §6.1 — every counter reads zero when the audit is off, and the sites are
    /// inert. A counter that moves while disabled would contaminate every
    /// committed result (PROTOCOL §9).
    #[test]
    fn disabled_counts_nothing() {
        let _x = super::exclusive();
        set_enabled(false);
        reset();
        ffi(100, 100);
        candidates(50, CandPath::Scan);
        where_eval(true);
        leaf_visit();
        for (_, v) in snapshot() {
            assert_eq!(v, 0, "a counter moved while the audit was OFF");
        }
        set_enabled(false);
    }

    /// §6.2 — a KNOWN-COUNT workload must produce EXACTLY the known integer.
    /// A counter that has only ever been seen to move has not been tested.
    #[test]
    fn known_counts_are_exact() {
        let _x = super::exclusive();
        set_enabled_for_thread(true);
        reset();
        begin_epoch();
        begin_rule_enumeration(0);
        candidates(7, CandPath::Scan);
        candidates(3, CandPath::Local);
        // Same rule again in the SAME epoch ⇒ every candidate is a REPEAT.
        begin_rule_enumeration(0);
        candidates(7, CandPath::Scan);
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["cand_enum"], 17);
        assert_eq!(m["cand_enum_scan"], 14);
        assert_eq!(m["cand_enum_local"], 3);
        assert_eq!(m["cand_enum_first"], 10);
        assert_eq!(m["cand_enum_repeat"], 7);
        assert_eq!(m["rule_enumerations"], 2);
        assert_eq!(m["rule_enumerations_repeat"], 1);
        // §6.4 conservation, on both axes.
        assert_eq!(m["cand_enum_first"] + m["cand_enum_repeat"], m["cand_enum"]);
        assert_eq!(
            m["cand_enum_scan"] + m["cand_enum_local"] + m["cand_enum_hinted"],
            m["cand_enum"]
        );
        set_enabled_for_thread(false);
        reset();
    }

    #[test]
    fn namespaced_rule_identity_separates_overlapping_indices_across_threads() {
        let _x = super::exclusive();
        set_enabled(true);
        set_per_rule_enabled(true);
        reset();
        per_rule_reset();
        begin_epoch();

        let store_a = new_rule_audit_store_id();
        let store_b = new_rule_audit_store_id();
        assert_ne!(store_a, store_b);
        for store in [store_a, store_b] {
            begin_rule_enumeration_in_store(store, 7);
            register_rule_audit_metadata_in_store(store, 7, 41, "same_rule", 1);
        }

        let id_a = rule_audit_id_for(store_a, 7).unwrap();
        let id_b = rule_audit_id_for(store_b, 7).unwrap();
        assert_ne!(id_a, id_b);
        with_rule_index(id_a, || cand_tested(0, 41, 1));
        std::thread::spawn(move || {
            with_rule_index(id_b, || cand_tested(0, 41, 1));
        })
        .join()
        .unwrap();

        let global: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(global["cand_tested"], 2);
        assert_eq!(global["cand_tested_unattributed"], 0);
        let per_rule = per_rule_snapshot();
        let candidate_rows: Vec<_> = per_rule
            .iter()
            .filter(|(_, metric, _)| metric == "candidate_tests")
            .collect();
        assert_eq!(candidate_rows.len(), 2);
        assert!(candidate_rows
            .iter()
            .any(|(id, _, n)| *id == id_a && *n == 1));
        assert!(candidate_rows
            .iter()
            .any(|(id, _, n)| *id == id_b && *n == 1));
        let clauses = match_clause_candidate_snapshot();
        assert_eq!(clauses, vec![(id_a, 0, 1), (id_b, 0, 1)]);
        let identities = rule_audit_identity_snapshot();
        assert!(identities.contains(&(id_a, store_a, 7)));
        assert!(identities.contains(&(id_b, store_b, 7)));
        assert!(rule_audit_metadata_snapshot()
            .iter()
            .all(|(_, _, _, arity, ambiguous)| *arity == 1 && !ambiguous));

        set_enabled(false);
        reset();
        per_rule_reset();
        cand_tested(0, 41, 1);
        assert!(per_rule_snapshot().is_empty());
        assert!(match_clause_candidate_snapshot().is_empty());
        set_per_rule_enabled(false);
    }

    /// §6.1 for the TERM family: the per-variant cells and the interior-unit
    /// cells are inert when the audit is off, and the guard is `None` so no
    /// thread-local is touched either.
    #[test]
    fn term_counters_are_inert_when_disabled() {
        let _x = super::exclusive();
        set_enabled(false);
        reset();
        let g = term_eval(0);
        assert!(
            g.is_none(),
            "the guard must not be constructed when disabled"
        );
        term_units(1000);
        for (name, v) in snapshot() {
            assert_eq!(v, 0, "{name} moved while the audit was OFF");
        }
        set_enabled(false);
    }

    /// §6.2 for the TERM family: a KNOWN workload produces EXACTLY the known
    /// integers, per variant, and units attribute to the INNERMOST variant.
    #[test]
    fn term_units_attribute_to_the_innermost_variant() {
        let _x = super::exclusive();
        set_enabled_for_thread(true);
        reset();
        {
            let _outer = term_eval(0); // Var
            term_units(5); // -> Var
            {
                let _inner = term_eval(3); // Attr
                term_units(7); // -> Attr, NOT Var
            }
            term_units(2); // guard dropped ⇒ back to Var
        }
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["term_eval:Var"], 1);
        assert_eq!(m["term_eval:Attr"], 1);
        assert_eq!(
            m["term_unit:Var"], 7,
            "5 + 2 after the inner guard is dropped"
        );
        assert_eq!(m["term_unit:Attr"], 7);
        assert_eq!(m["term_evals_total"], 2);
        assert_eq!(m["term_units_total"], 14);
        assert_eq!(m["term_units_unattributed"], 0);
        set_enabled_for_thread(false);
        reset();
    }

    /// A unit charged with no Term evaluation in progress is REPORTED, not
    /// silently dropped and not misfiled onto whichever variant ran last.
    #[test]
    fn units_outside_any_evaluation_are_reported_not_hidden() {
        let _x = super::exclusive();
        set_enabled_for_thread(true);
        reset();
        term_units(9);
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["term_units_unattributed"], 9);
        assert_eq!(m["term_units_total"], 0);
        set_enabled_for_thread(false);
        reset();
    }

    /// G4 TABLE INTEGRITY. `term_variants.rs` is GENERATED from the enum; if a
    /// variant is added without regenerating, `variant_index()` stops being
    /// exhaustive and this fails. The name table and the counter arrays must
    /// agree in length with the enum's own arity — which is where
    /// `NUM_TERM_VARIANTS` comes FROM (PROTOCOL §13: it falls out).
    #[test]
    fn variant_table_covers_the_enum() {
        let _x = super::exclusive();
        assert_eq!(TERM_VARIANT_NAMES.len(), NUM_TERM_VARIANTS);
        assert_eq!(TERM_EVALS.len(), NUM_TERM_VARIANTS);
        assert_eq!(TERM_UNITS.len(), NUM_TERM_VARIANTS);
        // Names are unique — two variants sharing a name would silently merge
        // two cost profiles into one row.
        let uniq: std::collections::HashSet<&str> = TERM_VARIANT_NAMES.iter().cloned().collect();
        assert_eq!(
            uniq.len(),
            NUM_TERM_VARIANTS,
            "duplicate variant name in the table"
        );
        // Every index in range maps to a distinct, non-empty name.
        assert!(TERM_VARIANT_NAMES.iter().all(|n| !n.is_empty()));
    }

    /// Only NON-ZERO per-variant cells are emitted, but the TOTALS are always
    /// present — so "the family is there and everything is zero" stays
    /// distinguishable from "the family is missing", which is exactly the
    /// confusion that lets a missing instrument read as a clean result.
    #[test]
    fn totals_are_always_emitted_even_when_every_cell_is_zero() {
        let _x = super::exclusive();
        set_enabled_for_thread(true);
        reset();
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["term_evals_total"], 0);
        assert_eq!(m["term_units_total"], 0);
        assert!(
            !m.contains_key("term_eval:Var"),
            "zero cells are not emitted"
        );
        set_enabled_for_thread(false);
        reset();
    }

    /// A NEW epoch re-arms the first/repeat classification: the same rule
    /// enumerated in a later epoch is a FIRST again, because the graph it reads
    /// may have changed between Python calls.
    #[test]
    fn epoch_rearms_first_repeat() {
        let _x = super::exclusive();
        set_enabled_for_thread(true);
        reset();
        begin_epoch();
        begin_rule_enumeration(4);
        candidates(5, CandPath::Scan);
        begin_epoch();
        begin_rule_enumeration(4);
        candidates(5, CandPath::Scan);
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["cand_enum_first"], 10, "a new epoch must re-arm FIRST");
        assert_eq!(m["cand_enum_repeat"], 0);
        assert_eq!(m["epochs"], 2);
        set_enabled_for_thread(false);
        reset();
    }
}
