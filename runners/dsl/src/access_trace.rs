//! Default-off, bounded concrete access trace for tractability measurements.
//!
//! Events are keyed by stable rule UID and concrete graph IDs. This is a
//! diagnostic trace, not a completeness proof: currently it records successful
//! pattern bindings, interpreted and selected JIT graph reads, adjacency Term
//! footprints, and selected native effects. Specialized graph-scanning Terms
//! remain partial. Enable only in isolated measurement workers.

use crate::graph::{NodeID, TypedGraph};
use crate::sym::Sym;
use std::cell::Cell;
use std::collections::BTreeMap;
use std::sync::atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering};
use std::sync::{Mutex, OnceLock};

pub const NO_ID: u32 = u32::MAX;
const MAX_DISTINCT_EVENTS: usize = 250_000;
const MAX_DISTINCT_WORK_EVENTS: usize = 100_000;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct AccessEvent {
    pub scope: usize,
    pub rule_uid: u64,
    pub kind: u8,
    pub node: u32,
    pub resource: u32,
    pub peer: u32,
}

/// One aggregated operation-work total inside a single `run_rules` call.
/// Unlike `AccessEvent`, these rows can have `rule_uid == 0`: scheduler scans
/// and queue drains run outside a rule match/effect context. `operation_id`
/// distinguishes consecutive fixpoint calls on the same substrate.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct WorkEvent {
    pub scope: usize,
    pub operation_id: u64,
    pub rule_uid: u64,
    pub kind: u8,
    pub subject: u32,
}

static ENABLED: AtomicBool = AtomicBool::new(false);
// Tracing is opt-in and process-global, but events are accepted only from the
// selected substrate graph. Rule UIDs and graph node IDs are local to a
// substrate, so omitting this scope can merge unrelated engines' events.
static ACTIVE_SCOPE: AtomicUsize = AtomicUsize::new(0);
static WORK_ENABLED: AtomicBool = AtomicBool::new(false);
static WORK_ALL_SCOPES: AtomicBool = AtomicBool::new(false);
static DROPPED: AtomicU64 = AtomicU64::new(0);
static EVENTS: OnceLock<Mutex<BTreeMap<AccessEvent, u64>>> = OnceLock::new();
static WORK_EVENTS: OnceLock<Mutex<BTreeMap<WorkEvent, u64>>> = OnceLock::new();
static NEXT_OPERATION_ID: AtomicU64 = AtomicU64::new(1);
static WORK_DROPPED: AtomicU64 = AtomicU64::new(0);

thread_local! {
    static CURRENT_RULE_UID: Cell<u64> = const { Cell::new(0) };
    static CURRENT_SCOPE: Cell<usize> = const { Cell::new(0) };
    static CURRENT_OPERATION_ID: Cell<u64> = const { Cell::new(0) };
    static CURRENT_OPERATION_SCOPE: Cell<usize> = const { Cell::new(0) };
}

fn events() -> &'static Mutex<BTreeMap<AccessEvent, u64>> {
    EVENTS.get_or_init(|| Mutex::new(BTreeMap::new()))
}

fn work_events() -> &'static Mutex<BTreeMap<WorkEvent, u64>> {
    WORK_EVENTS.get_or_init(|| Mutex::new(BTreeMap::new()))
}

pub fn set_enabled(on: bool, scope: usize) {
    ACTIVE_SCOPE.store(if on { scope } else { 0 }, Ordering::Relaxed);
    WORK_ALL_SCOPES.store(false, Ordering::Relaxed);
    WORK_ENABLED.store(on, Ordering::Relaxed);
    ENABLED.store(on, Ordering::Relaxed);
}

/// Enable operation-work capture for every graph scope in the process without
/// enabling concrete graph-access rows. Intended for isolated whole-request
/// instrumentation workers.
pub fn set_work_all_scopes_enabled(on: bool) {
    WORK_ALL_SCOPES.store(on, Ordering::Relaxed);
    WORK_ENABLED.store(on, Ordering::Relaxed);
}

#[inline]
pub fn work_capture_enabled_for_scope(scope: usize) -> bool {
    WORK_ENABLED.load(Ordering::Relaxed)
        && (WORK_ALL_SCOPES.load(Ordering::Relaxed)
            || scope == ACTIVE_SCOPE.load(Ordering::Relaxed))
}

#[inline]
pub fn is_enabled() -> bool {
    ENABLED.load(Ordering::Relaxed)
}

pub fn note_out_edges(graph: &TypedGraph, node: NodeID, edge_type: Option<Sym>) {
    if !is_enabled() {
        return;
    }
    for edge_idx in graph.out_edges_slice(node, edge_type) {
        let edge = graph.edge(*edge_idx);
        note(14, edge.src.0, edge.edge_type.0, edge.tgt.0);
    }
}

pub fn note_in_edges(graph: &TypedGraph, node: NodeID, edge_type: Option<Sym>) {
    if !is_enabled() {
        return;
    }
    for edge_idx in graph.in_edges_slice(node, edge_type) {
        let edge = graph.edge(*edge_idx);
        note(14, edge.src.0, edge.edge_type.0, edge.tgt.0);
    }
}

pub fn note_node_type_and_attrs(graph: &TypedGraph, node: NodeID) {
    if !is_enabled() {
        return;
    }
    let data = graph.node(node);
    note(3, node.0, data.type_.0, NO_ID);
    for (key, _) in data.attrs.iter() {
        note(2, node.0, key.0, NO_ID);
    }
}

pub fn reset() {
    if let Ok(mut rows) = events().lock() {
        rows.clear();
    }
    DROPPED.store(0, Ordering::Relaxed);
    if let Ok(mut rows) = work_events().lock() {
        rows.clear();
    }
    WORK_DROPPED.store(0, Ordering::Relaxed);
}

pub struct WorkOperationGuard(u64, usize);

impl Drop for WorkOperationGuard {
    fn drop(&mut self) {
        CURRENT_OPERATION_ID.with(|current| current.set(self.0));
        CURRENT_OPERATION_SCOPE.with(|current| current.set(self.1));
    }
}

/// Start a separately identified operation-work interval. It is inert unless
/// access tracing is enabled for this substrate scope.
pub fn begin_work_operation(scope: usize) -> WorkOperationGuard {
    begin_work_operation_kind(scope, 1)
}

/// Start a separately identified operation with a small operation-kind code:
/// 1=`run_rules`, 2=`apply_rule_once`, 3=`apply_rule_batch`.
pub fn begin_work_operation_kind(scope: usize, operation_kind: u32) -> WorkOperationGuard {
    let all_scopes = WORK_ALL_SCOPES.load(Ordering::Relaxed);
    if !WORK_ENABLED.load(Ordering::Relaxed)
        || scope == 0
        || (!all_scopes && scope != ACTIVE_SCOPE.load(Ordering::Relaxed))
    {
        return WorkOperationGuard(
            CURRENT_OPERATION_ID.with(Cell::get),
            CURRENT_OPERATION_SCOPE.with(Cell::get),
        );
    }
    let operation_id = NEXT_OPERATION_ID.fetch_add(1, Ordering::Relaxed);
    let previous_id = CURRENT_OPERATION_ID.with(|current| {
        let previous = current.get();
        current.set(operation_id);
        previous
    });
    let previous_scope = CURRENT_OPERATION_SCOPE.with(|current| {
        let previous = current.get();
        current.set(scope);
        previous
    });
    note_work(27, operation_kind, 1);
    WorkOperationGuard(previous_id, previous_scope)
}

/// Current graph scope for operation work, or zero when execution is outside a
/// traced `run_rules` operation. Scoped scale-audit counters use this identity.
#[inline]
pub fn current_work_scope() -> usize {
    let operation_id = CURRENT_OPERATION_ID.with(Cell::get);
    let scope = CURRENT_OPERATION_SCOPE.with(Cell::get);
    let all_scopes = WORK_ALL_SCOPES.load(Ordering::Relaxed);
    if WORK_ENABLED.load(Ordering::Relaxed) && operation_id != 0 && scope != 0
        && (all_scopes || scope == ACTIVE_SCOPE.load(Ordering::Relaxed))
    {
        scope
    } else {
        0
    }
}

/// Add `amount` units to a scoped operation-work event. `subject` is a stable
/// small enum for family-specific events, or `NO_ID` when not applicable.
#[inline]
pub fn note_work(kind: u8, subject: u32, amount: u64) {
    if amount == 0 || !WORK_ENABLED.load(Ordering::Relaxed) {
        return;
    }
    let operation_id = CURRENT_OPERATION_ID.with(Cell::get);
    let scope = CURRENT_OPERATION_SCOPE.with(Cell::get);
    let all_scopes = WORK_ALL_SCOPES.load(Ordering::Relaxed);
    if operation_id == 0 || scope == 0
        || (!all_scopes && scope != ACTIVE_SCOPE.load(Ordering::Relaxed))
    {
        return;
    }
    let rule_scope = CURRENT_SCOPE.with(Cell::get);
    let rule_uid = if rule_scope == scope { CURRENT_RULE_UID.with(Cell::get) } else { 0 };
    let event = WorkEvent { scope, operation_id, rule_uid, kind, subject };
    if let Ok(mut rows) = work_events().lock() {
        if let Some(count) = rows.get_mut(&event) {
            *count = count.saturating_add(amount);
        } else if rows.len() < MAX_DISTINCT_WORK_EVENTS {
            rows.insert(event, amount);
        } else {
            WORK_DROPPED.fetch_add(1, Ordering::Relaxed);
        }
    } else {
        WORK_DROPPED.fetch_add(1, Ordering::Relaxed);
    }
}

pub fn work_snapshot(scope: usize) -> (Vec<(WorkEvent, u64)>, u64) {
    let rows = work_events()
        .lock()
        .map(|map| map.iter().filter(|(event, _)| event.scope == scope).map(|(&event, &count)| (event, count)).collect())
        .unwrap_or_default();
    (rows, WORK_DROPPED.load(Ordering::Relaxed))
}

pub fn work_snapshot_all() -> (Vec<(WorkEvent, u64)>, u64) {
    let rows = work_events().lock().map(|map| map.iter().map(|(&event, &count)| (event, count)).collect()).unwrap_or_default();
    (rows, WORK_DROPPED.load(Ordering::Relaxed))
}

pub fn snapshot(scope: usize) -> (Vec<(AccessEvent, u64)>, u64) {
    let rows = events()
        .lock()
        .map(|map| map.iter().filter(|(event, _)| event.scope == scope).map(|(&event, &count)| (event, count)).collect())
        .unwrap_or_default();
    (rows, DROPPED.load(Ordering::Relaxed))
}

pub struct RuleGuard(u64, usize);

impl Drop for RuleGuard {
    fn drop(&mut self) {
        CURRENT_RULE_UID.with(|current| current.set(self.0));
        CURRENT_SCOPE.with(|current| current.set(self.1));
    }
}

pub fn enter_rule(rule_uid: u64, scope: usize) -> RuleGuard {
    let previous = CURRENT_RULE_UID.with(|current| {
        let previous = current.get();
        current.set(rule_uid);
        previous
    });
    let previous_scope = CURRENT_SCOPE.with(|current| {
        let previous = current.get();
        current.set(scope);
        previous
    });
    RuleGuard(previous, previous_scope)
}

#[inline]
pub fn note(kind: u8, node: u32, resource: u32, peer: u32) {
    if !ENABLED.load(Ordering::Relaxed) {
        return;
    }
    let rule_uid = CURRENT_RULE_UID.with(Cell::get);
    let scope = CURRENT_SCOPE.with(Cell::get);
    if rule_uid == 0 || scope == 0 || scope != ACTIVE_SCOPE.load(Ordering::Relaxed) {
        return;
    }
    let event = AccessEvent {
        scope,
        rule_uid,
        kind,
        node,
        resource,
        peer,
    };
    if let Ok(mut rows) = events().lock() {
        if let Some(count) = rows.get_mut(&event) {
            *count = count.saturating_add(1);
        } else if rows.len() < MAX_DISTINCT_EVENTS {
            rows.insert(event, 1);
        } else {
            DROPPED.fetch_add(1, Ordering::Relaxed);
        }
    } else {
        DROPPED.fetch_add(1, Ordering::Relaxed);
    }
}

pub fn kind_name(kind: u8) -> &'static str {
    match kind {
        1 => "pattern_edge",
        2 => "term_attr_read",
        3 => "term_type_read",
        4 => "effect_attr_write",
        5 => "effect_edge_upsert",
        6 => "effect_edge_delete",
        7 => "effect_node_mint",
        8 => "effect_node_delete",
        9 => "effect_type_query",
        10 => "effect_type_candidate_read",
        11 => "effect_replace_edge",
        12 => "jit_attr_read",
        13 => "jit_type_read",
        14 => "term_edge_read",
        15 => "term_edge_attr_read",
        16 => "term_index_query",
        17 => "effect_attr_compare_read",
        18 => "term_tool_dispatch",
        19 => "scheduler_pass",
        20 => "scheduler_external_poll_slots",
        21 => "scheduler_fixedpoint_probe_slots",
        22 => "scheduler_dirty_vector_slots",
        23 => "scheduler_selected_rules",
        24 => "deferred_queue_enqueue_items",
        25 => "deferred_queue_drain_batches",
        26 => "deferred_queue_drained_items",
        27 => "operation_kind",
        28 => "effect_edge_compare_read",
        30 => "term_index_scan_candidate",
        31 => "term_index_result_candidate",
        32 => "term_index_query_indexed",
        33 => "term_index_query_fallback",
        34 => "term_typed_population_query",
        35 => "term_typed_population_candidate",
        _ => "unknown",
    }
}
