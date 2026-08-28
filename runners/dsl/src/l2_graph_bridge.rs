//! L2 ↔ Graph bridge — materialises `DispatcherSnapshot` into the
//! substrate's typed graph so reflexes can introspect dispatcher
//! state.
//!
//! ## What this realises
//!
//! The `second_order_scheduler_state_as_graph` component of the
//! `adaptive_tiered_dispatch` Mt (commit e9b607a). The Mt:
//!
//! > "The scheduler's runtime state (current epoch, hot counters,
//! >  cached artefacts metadata, current load) is graph data the
//! >  substrate's reflexes can observe and rules can mutate. A
//! >  reflex can adjust the tier-up threshold based on observed
//! >  hot-counter distribution (gain scheduling); a rule can bump
//! >  the epoch manually for testing. Axiom 3 + cybernetics'
//! >  second_order_cybernetics applied to the dispatcher itself."
//!
//! ## Schema
//!
//! - `Dispatcher` — root node per dispatcher. Attrs:
//!     - `label: Str`
//!     - `epoch: Int`
//!     - `total_cache_bytes: Int`
//! - `DispatcherPolicy` — policy params. Attrs:
//!     - `threshold: Int`
//!     - `cooling_threshold: Int`
//!     - `cache_max_bytes: Int`
//! - `HotCounterEntry` — one per kind. Attrs:
//!     - `kind: Str` (interned name)
//!     - `count: Int`
//! - `CachedArtefact` — one per cached entry. Attrs:
//!     - `kind: Str`
//!     - `epoch_at_compile: Int`
//!     - `code_size_bytes: Int`
//!
//! Edges:
//! - `Dispatcher -[has_policy]-> DispatcherPolicy`
//! - `Dispatcher -[has_hot]-> HotCounterEntry`
//! - `Dispatcher -[has_cached]-> CachedArtefact`
//!
//! ## Lifecycle
//!
//! 1. Call `register_dispatcher_schema(substrate)` ONCE at startup
//!    (before any dispatcher snapshot installs). This adds the
//!    productions admitting the four edge types above. The
//!    registration bumps `gamma_epoch` once — caller should
//!    register before installing any dispatcher.
//! 2. Call `install_snapshot_into_graph(substrate, &snapshot, label)`
//!    whenever the substrate wants to expose dispatcher state.
//!    Typical cadence: per major tick.
//! 3. To re-snapshot, either call `remove_snapshot(substrate, node)`
//!    first or call `install_snapshot_into_graph` with a fresh label
//!    and let the prior snapshot persist (mirrors event-log shape).

use rustc_hash::FxHashMap;

use crate::grammar::{NodePattern, Production};
use crate::graph::NodeID;
use crate::l2_adaptive::{CachedEntrySummary, DispatcherSnapshot};
use crate::substrate::Substrate;
use crate::sym::Sym;
use crate::value::Value;

/// Register the productions admitting `Dispatcher -[has_policy]->
/// DispatcherPolicy` and the two other edges. Bumps `gamma_epoch`
/// once. Call at startup, before any dispatcher state is installed.
///
/// Idempotent-ish: re-calling will re-add the productions (the
/// grammar accepts duplicates). For tests this is fine; production
/// code should call exactly once.
pub fn register_dispatcher_schema(substrate: &mut Substrate) {
    let (
        dispatcher_t,
        policy_t,
        hot_t,
        cached_t,
        has_policy,
        has_hot,
        has_cached,
        src_var,
        tgt_var,
        prov,
    ) = {
        let i = &mut substrate.interner;
        (
            i.intern("Dispatcher"),
            i.intern("DispatcherPolicy"),
            i.intern("HotCounterEntry"),
            i.intern("CachedArtefact"),
            i.intern("has_policy"),
            i.intern("has_hot"),
            i.intern("has_cached"),
            i.intern("src"),
            i.intern("tgt"),
            i.intern("l2_graph_bridge:schema"),
        )
    };
    let w = crate::grammar::Grammar::default_weight(&mut substrate.terms);
    for (et, tgt_type) in [
        (has_policy, policy_t),
        (has_hot, hot_t),
        (has_cached, cached_t),
    ] {
        substrate.add_production(Production {
            src: NodePattern {
                type_: dispatcher_t,
                var: src_var,
            },
            edge_type: et,
            tgt: NodePattern {
                type_: tgt_type,
                var: tgt_var,
            },
            where_: None,
            weight: w,
            provenance: prov,
        });
    }
}

/// Materialise `snapshot` into the substrate's graph. Returns the
/// `NodeID` of the created `Dispatcher` root.
///
/// Caller must have called [`register_dispatcher_schema`] before
/// the first snapshot install, else edge admissibility will fail.
pub fn install_snapshot_into_graph(
    substrate: &mut Substrate,
    snapshot: &DispatcherSnapshot,
    label: &str,
) -> NodeID {
    // Pre-intern all syms we'll use, to avoid borrow conflicts
    // inside the add_node / add_edge calls.
    let label_sym = substrate.interner.intern("label");
    let epoch_sym = substrate.interner.intern("epoch");
    let total_bytes_sym = substrate.interner.intern("total_cache_bytes");
    let threshold_sym = substrate.interner.intern("threshold");
    let cooling_threshold_sym = substrate.interner.intern("cooling_threshold");
    let cache_max_bytes_sym = substrate.interner.intern("cache_max_bytes");
    let kind_sym = substrate.interner.intern("kind");
    let count_sym = substrate.interner.intern("count");
    let epoch_at_compile_sym = substrate.interner.intern("epoch_at_compile");
    let code_size_bytes_sym = substrate.interner.intern("code_size_bytes");
    let dispatcher_t = substrate.interner.intern("Dispatcher");
    let policy_t = substrate.interner.intern("DispatcherPolicy");
    let hot_t = substrate.interner.intern("HotCounterEntry");
    let cached_t = substrate.interner.intern("CachedArtefact");
    let has_policy = substrate.interner.intern("has_policy");
    let has_hot = substrate.interner.intern("has_hot");
    let has_cached = substrate.interner.intern("has_cached");
    let prov_sym = substrate.interner.intern("l2_graph_bridge:snapshot");

    // Re-use the kind syms directly as attribute values — Value::Str
    // wraps a Sym, so the kind sym IS the value (no re-interning).
    // For the label attr we intern the user-supplied string.
    let label_value_sym = substrate.interner.intern(label);

    // Dispatcher root.
    let dispatcher_node = {
        let mut a = FxHashMap::default();
        a.insert(label_sym, Value::Str(label_value_sym));
        a.insert(epoch_sym, Value::Int(snapshot.epoch as i64));
        a.insert(
            total_bytes_sym,
            Value::Int(snapshot.total_cache_bytes as i64),
        );
        substrate.add_node(dispatcher_t, a)
    };

    // Policy.
    let policy_node = {
        let mut a = FxHashMap::default();
        a.insert(threshold_sym, Value::Int(snapshot.policy.threshold as i64));
        a.insert(
            cooling_threshold_sym,
            Value::Int(snapshot.policy.cooling_threshold as i64),
        );
        a.insert(
            cache_max_bytes_sym,
            Value::Int(snapshot.cache_max_bytes as i64),
        );
        substrate.add_node(policy_t, a)
    };
    let mut edge_attrs = FxHashMap::default();
    let _ = substrate.add_edge(
        dispatcher_node,
        has_policy,
        policy_node,
        std::mem::take(&mut edge_attrs),
    );

    // Hot counters. kind is stored AS the kind's Sym wrapped in
    // Value::Str — reflexes resolving the Sym get the rule name.
    for (kind, count) in &snapshot.hot_counters {
        let mut a = FxHashMap::default();
        a.insert(kind_sym, Value::Str(*kind));
        a.insert(count_sym, Value::Int(*count as i64));
        let h = substrate.add_node(hot_t, a);
        let _ = substrate.add_edge(dispatcher_node, has_hot, h, std::mem::take(&mut edge_attrs));
    }

    // Cached artefacts.
    for entry in &snapshot.cached {
        let mut a = FxHashMap::default();
        a.insert(kind_sym, Value::Str(entry.kind));
        a.insert(
            epoch_at_compile_sym,
            Value::Int(entry.epoch_at_compile as i64),
        );
        a.insert(
            code_size_bytes_sym,
            Value::Int(entry.code_size_bytes as i64),
        );
        let c = substrate.add_node(cached_t, a);
        let _ = substrate.add_edge(
            dispatcher_node,
            has_cached,
            c,
            std::mem::take(&mut edge_attrs),
        );
    }

    let _ = prov_sym; // currently unused; reserved for provenance attr
    dispatcher_node
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::checker::ConsistencyChecker;
    use crate::code_cache::{CodeCacheConfig, CodeSize};
    use crate::grammar::Grammar;
    use crate::l2_adaptive::{AdaptiveDispatcher, TierUpPolicy, TypedTask};
    use crate::l2_dispatch::{PriorityClass, Scheduler};
    use std::sync::atomic::{AtomicUsize, Ordering as AtomicOrd};
    use std::sync::Arc;
    use std::time::{Duration, Instant};

    struct FakeJit {
        size: usize,
    }
    impl CodeSize for FakeJit {
        fn code_size_bytes(&self) -> usize {
            self.size
        }
    }

    fn empty_substrate() -> Substrate {
        Substrate::new(ConsistencyChecker::new(Grammar::new()))
    }

    /// Snapshot reflects dispatcher state accurately.
    #[test]
    fn snapshot_captures_dispatcher_state() {
        let mut s = empty_substrate();
        let dispatcher: AdaptiveDispatcher<FakeJit> = AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy {
                threshold: 50,
                cooling_threshold: 4,
            },
            CodeCacheConfig { max_bytes: 2048 },
            s.gamma_epoch(),
        );
        let k1 = s.interner.intern("hot_rule");
        let k2 = s.interner.intern("cold_rule");
        for _ in 0..10 {
            dispatcher.hot_counter().record(k1);
        }
        for _ in 0..3 {
            dispatcher.hot_counter().record(k2);
        }
        dispatcher.install_compiled(k1, FakeJit { size: 256 });

        let snap = dispatcher.snapshot();
        assert_eq!(snap.epoch, s.gamma_epoch().current());
        assert_eq!(snap.policy.threshold, 50);
        assert_eq!(snap.policy.cooling_threshold, 4);
        assert_eq!(snap.cache_max_bytes, 2048);
        assert_eq!(snap.total_cache_bytes, 256);

        let counts: std::collections::HashMap<Sym, u64> =
            snap.hot_counters.iter().copied().collect();
        assert_eq!(counts.get(&k1), Some(&10));
        assert_eq!(counts.get(&k2), Some(&3));
        assert_eq!(snap.cached.len(), 1);
        assert_eq!(snap.cached[0].kind, k1);
        assert_eq!(snap.cached[0].code_size_bytes, 256);

        dispatcher.shutdown();
    }

    /// install_snapshot_into_graph creates the Dispatcher root +
    /// policy + per-kind entries with correct attrs.
    #[test]
    fn install_snapshot_materialises_into_graph() {
        let mut s = empty_substrate();
        register_dispatcher_schema(&mut s);

        let dispatcher: AdaptiveDispatcher<FakeJit> = AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy {
                threshold: 100,
                cooling_threshold: 3,
            },
            CodeCacheConfig { max_bytes: 1024 },
            s.gamma_epoch(),
        );
        let k = s.interner.intern("rule_a");
        dispatcher.hot_counter().record(k);
        dispatcher.hot_counter().record(k);
        dispatcher.install_compiled(k, FakeJit { size: 128 });
        let snap = dispatcher.snapshot();

        let dispatcher_node = install_snapshot_into_graph(&mut s, &snap, "test_dispatcher");

        // Verify the root Dispatcher node exists with correct attrs.
        assert!(s.graph.has_node(dispatcher_node));
        let nd = s.graph.node(dispatcher_node);
        let label_sym = s.interner.lookup("label").unwrap();
        let epoch_sym = s.interner.lookup("epoch").unwrap();
        match nd.attrs.get(&label_sym) {
            Some(Value::Str(sym)) => {
                assert_eq!(s.interner.resolve(*sym), "test_dispatcher");
            }
            other => panic!("label wrong: {:?}", other),
        }
        match nd.attrs.get(&epoch_sym) {
            Some(Value::Int(e)) => assert_eq!(*e, snap.epoch as i64),
            other => panic!("epoch wrong: {:?}", other),
        }

        // Walk has_policy → exactly one DispatcherPolicy node.
        let has_policy = s.interner.lookup("has_policy").unwrap();
        let policy_nodes: Vec<_> = s
            .graph
            .out_edges_idx(dispatcher_node, Some(has_policy))
            .into_iter()
            .collect();
        assert_eq!(policy_nodes.len(), 1);

        // Walk has_hot → one HotCounterEntry per kind in the snapshot.
        let has_hot = s.interner.lookup("has_hot").unwrap();
        let hot_edges = s.graph.out_edges_idx(dispatcher_node, Some(has_hot));
        assert_eq!(hot_edges.len(), snap.hot_counters.len());

        // Walk has_cached → one CachedArtefact per cached entry.
        let has_cached = s.interner.lookup("has_cached").unwrap();
        let cached_edges = s.graph.out_edges_idx(dispatcher_node, Some(has_cached));
        assert_eq!(cached_edges.len(), snap.cached.len());

        dispatcher.shutdown();
    }

    /// A reflex (or external introspection) can find the hot counter
    /// for a specific kind by walking the graph + reading the kind
    /// attr. Demonstrates the Mt's claim that dispatcher state is
    /// queryable just like any other graph data.
    #[test]
    fn graph_introspection_finds_specific_hot_counter() {
        let mut s = empty_substrate();
        register_dispatcher_schema(&mut s);

        let dispatcher: AdaptiveDispatcher<FakeJit> = AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy::default(),
            CodeCacheConfig::default(),
            s.gamma_epoch(),
        );
        let k_alpha = s.interner.intern("rule_alpha");
        let k_beta = s.interner.intern("rule_beta");
        for _ in 0..7 {
            dispatcher.hot_counter().record(k_alpha);
        }
        for _ in 0..2 {
            dispatcher.hot_counter().record(k_beta);
        }
        let snap = dispatcher.snapshot();
        let _ = install_snapshot_into_graph(&mut s, &snap, "d");

        // Now introspect from the graph side: find the
        // HotCounterEntry whose kind == "rule_alpha".
        let hot_t = s.interner.lookup("HotCounterEntry").unwrap();
        let kind_sym = s.interner.lookup("kind").unwrap();
        let count_sym = s.interner.lookup("count").unwrap();
        let mut alpha_count: Option<i64> = None;
        for nid in s.graph.nodes_of_type(hot_t) {
            let nd = s.graph.node(nid);
            if let Some(Value::Str(ks)) = nd.attrs.get(&kind_sym) {
                if s.interner.resolve(*ks) == "rule_alpha" {
                    if let Some(Value::Int(c)) = nd.attrs.get(&count_sym) {
                        alpha_count = Some(*c);
                    }
                }
            }
        }
        assert_eq!(
            alpha_count,
            Some(7),
            "reflex-style introspection should find rule_alpha's count"
        );
        dispatcher.shutdown();
    }

    /// Submitting through the dispatcher + then snapshotting shows
    /// updated counters in the graph — demonstrating that the
    /// dispatcher's runtime behaviour is observable via snapshot
    /// cycles.
    #[test]
    fn snapshot_after_submit_shows_updated_counts() {
        let mut s = empty_substrate();
        register_dispatcher_schema(&mut s);
        let dispatcher: AdaptiveDispatcher<FakeJit> = AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(2),
            TierUpPolicy::default(),
            CodeCacheConfig::default(),
            s.gamma_epoch(),
        );
        let k = s.interner.intern("rule");
        let counter = Arc::new(AtomicUsize::new(0));
        for _ in 0..15 {
            let c = Arc::clone(&counter);
            dispatcher.submit(TypedTask {
                kind: k,
                deadline: Instant::now() + Duration::from_secs(60),
                class: PriorityClass::BestEffort,
                work: Box::new(move || {
                    c.fetch_add(1, AtomicOrd::SeqCst);
                }),
            });
        }
        std::thread::sleep(Duration::from_millis(50));

        let snap = dispatcher.snapshot();
        // 15 records on the hot counter for this kind.
        let count = snap
            .hot_counters
            .iter()
            .find(|(s, _)| *s == k)
            .map(|(_, c)| *c);
        assert_eq!(count, Some(15));
        dispatcher.drain_and_shutdown();
    }
}
