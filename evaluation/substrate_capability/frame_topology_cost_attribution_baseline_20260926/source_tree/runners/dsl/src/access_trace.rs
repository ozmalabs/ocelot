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
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};

pub const NO_ID: u32 = u32::MAX;
const MAX_DISTINCT_EVENTS: usize = 250_000;

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct AccessEvent {
    pub rule_uid: u64,
    pub kind: u8,
    pub node: u32,
    pub resource: u32,
    pub peer: u32,
}

static ENABLED: AtomicBool = AtomicBool::new(false);
static DROPPED: AtomicU64 = AtomicU64::new(0);
static EVENTS: OnceLock<Mutex<BTreeMap<AccessEvent, u64>>> = OnceLock::new();

thread_local! {
    static CURRENT_RULE_UID: Cell<u64> = const { Cell::new(0) };
}

fn events() -> &'static Mutex<BTreeMap<AccessEvent, u64>> {
    EVENTS.get_or_init(|| Mutex::new(BTreeMap::new()))
}

pub fn set_enabled(on: bool) {
    ENABLED.store(on, Ordering::Relaxed);
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
}

pub fn snapshot() -> (Vec<(AccessEvent, u64)>, u64) {
    let rows = events()
        .lock()
        .map(|map| map.iter().map(|(&event, &count)| (event, count)).collect())
        .unwrap_or_default();
    (rows, DROPPED.load(Ordering::Relaxed))
}

pub struct RuleGuard(u64);

impl Drop for RuleGuard {
    fn drop(&mut self) {
        CURRENT_RULE_UID.with(|current| current.set(self.0));
    }
}

pub fn enter_rule(rule_uid: u64) -> RuleGuard {
    let previous = CURRENT_RULE_UID.with(|current| {
        let previous = current.get();
        current.set(rule_uid);
        previous
    });
    RuleGuard(previous)
}

#[inline]
pub fn note(kind: u8, node: u32, resource: u32, peer: u32) {
    if !ENABLED.load(Ordering::Relaxed) {
        return;
    }
    let rule_uid = CURRENT_RULE_UID.with(Cell::get);
    if rule_uid == 0 {
        return;
    }
    let event = AccessEvent {
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
        _ => "unknown",
    }
}
