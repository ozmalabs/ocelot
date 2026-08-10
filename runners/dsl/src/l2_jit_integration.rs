//! L2 ↔ JIT end-to-end integration tests.
//!
//! Verifies that the dispatcher's TierUp surface (commit 6783650),
//! the code cache's epoch-stamped storage (commit f1f376f), and the
//! existing JIT (jit.rs) compose end-to-end:
//!
//!  1. Caller submits tasks of a given kind through the dispatcher.
//!  2. At the threshold submit, dispatcher returns `TierUp`.
//!  3. Caller responds by JIT-compiling the rule's Term-tree.
//!  4. Caller installs the `JittedFn` into the dispatcher's cache.
//!  5. Subsequent submits return `Cached`; worker code can pull the
//!     JIT'd fn out and call it directly.
//!  6. Γ mutation invalidates the cache (epoch bump); subsequent
//!     submits return `Queued` again until the caller recompiles.
//!
//! These tests exercise THE WHOLE L2-dynamic surface — the previous
//! commits proved each piece in isolation; this proves they compose
//! into a working JIT-cache-dispatch loop.

#![cfg(all(target_arch = "x86_64", target_os = "linux"))]
#![cfg(test)]

use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering as AtomicOrd};
use std::time::{Duration, Instant};

use rustc_hash::FxHashMap;

use crate::checker::ConsistencyChecker;
use crate::code_cache::CodeCacheConfig;
use crate::grammar::Grammar;
use crate::jit::{self, JittedFn};
use crate::l2_adaptive::{
    AdaptiveDispatcher, DispatchOutcome, TierUpPolicy, TypedTask,
};
use crate::l2_dispatch::{PriorityClass, Scheduler};
use crate::substrate::Substrate;
use crate::term::TermNode;
use crate::value::Value;

fn empty_substrate() -> Substrate {
    Substrate::new(ConsistencyChecker::new(Grammar::new()))
}

/// End-to-end: submit → TierUp → JIT compile → install → Cached →
/// pull JIT'd fn from cache → call → verify result.
#[test]
fn end_to_end_jit_compile_install_call() {
    let mut s = empty_substrate();
    let dispatcher: AdaptiveDispatcher<JittedFn> =
        AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(2),
            TierUpPolicy { threshold: 5, cooling_threshold: 3 },
            CodeCacheConfig::default(),
            s.gamma_epoch(),
        );

    // The "rule" we're going to JIT: pure-arithmetic Plus(Lit(2), Lit(3)).
    let two = s.terms.add(TermNode::Lit { value: Value::Int(2) });
    let three = s.terms.add(TermNode::Lit { value: Value::Int(3) });
    let plus = s.terms.add(TermNode::Plus { items: vec![two, three] });
    let kind = s.interner.intern("add_two_three");

    let counter = Arc::new(AtomicUsize::new(0));
    let submit_work = || -> Box<dyn FnOnce() + Send + 'static> {
        let c = Arc::clone(&counter);
        Box::new(move || { c.fetch_add(1, AtomicOrd::SeqCst); })
    };

    // Submits 1..4: each returns Queued.
    for n in 1..=4 {
        let outcome = dispatcher.submit(TypedTask {
            kind,
            deadline: Instant::now() + Duration::from_secs(60),
            class: PriorityClass::BestEffort,
            work: submit_work(),
        });
        match outcome {
            DispatchOutcome::Queued { count, .. } => assert_eq!(count, n),
            other => panic!("submit {} expected Queued, got {:?}", n, other),
        }
    }

    // Submit 5: TierUp.
    let outcome = dispatcher.submit(TypedTask {
        kind,
        deadline: Instant::now() + Duration::from_secs(60),
        class: PriorityClass::BestEffort,
        work: submit_work(),
    });
    match outcome {
        DispatchOutcome::TierUp { count, .. } => assert_eq!(count, 5),
        other => panic!("submit 5 expected TierUp, got {:?}", other),
    }

    // Caller's TierUp response: compile + install. (In production,
    // this would happen on a separate compile thread to avoid
    // blocking the dispatcher; here it's inline for test clarity.)
    let var_indices: FxHashMap<crate::sym::Sym, u32> = FxHashMap::default();
    let jitted = jit::compile(&s.terms, plus, &var_indices)
        .expect("JIT should compile a pure-arithmetic Plus(Lit, Lit)");
    let initial_code_len = jitted.code_len();
    assert!(initial_code_len > 0, "compile must produce code bytes");
    assert!(!jitted.needs_ctx(),
            "pure arithmetic shouldn't need a graph ctx");
    let evicted = dispatcher.install_compiled(kind, jitted);
    assert!(evicted.is_empty(),
            "fresh install shouldn't evict anything from an empty cache");

    // Subsequent submits return Cached.
    let outcome = dispatcher.submit(TypedTask {
        kind,
        deadline: Instant::now() + Duration::from_secs(60),
        class: PriorityClass::BestEffort,
        work: submit_work(),
    });
    assert!(matches!(outcome, DispatchOutcome::Cached { .. }),
            "after install, submit should return Cached, got {:?}", outcome);

    // Pull the JIT'd fn out and call it.
    let cached = dispatcher.get_compiled(kind).expect("Cached: must be present");
    let result = cached.inner.call_pure(&[]);
    assert_eq!(result, 5,
               "JIT'd Plus(Lit(2), Lit(3)) must return 5");

    // Wait for tasks to drain.
    std::thread::sleep(Duration::from_millis(100));
    assert_eq!(counter.load(AtomicOrd::SeqCst), 6,
               "all 6 submitted tasks should have run");
    dispatcher.drain_and_shutdown();
}

/// Γ mutation after JIT install invalidates the cached artefact.
/// Realises the full Mt rule `gamma_change_must_bump_epoch` end-to-end
/// through actual JIT'd code.
#[test]
fn gamma_mutation_invalidates_jit_cache_end_to_end() {
    let mut s = empty_substrate();
    let dispatcher: AdaptiveDispatcher<JittedFn> =
        AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy { threshold: 2, cooling_threshold: 3 },
            CodeCacheConfig::default(),
            s.gamma_epoch(),
        );

    // Compile a different Term to exercise: Times(Lit(7), Lit(6)) = 42.
    let seven = s.terms.add(TermNode::Lit { value: Value::Int(7) });
    let six   = s.terms.add(TermNode::Lit { value: Value::Int(6) });
    let times = s.terms.add(TermNode::Times { items: vec![seven, six] });
    let kind  = s.interner.intern("seven_times_six");

    // Tier up + install.
    for _ in 0..2 { dispatcher.hot_counter().record(kind); }
    let jitted = jit::compile(&s.terms, times, &FxHashMap::default())
        .expect("compile Times(Lit, Lit)");
    dispatcher.install_compiled(kind, jitted);

    // Call it once via cache.
    let cached = dispatcher.get_compiled(kind).expect("present");
    assert_eq!(cached.inner.call_pure(&[]), 42);
    drop(cached);

    // Now mutate Γ: add a rule. Per substrate.rs invariant
    // (verified in commit f81559e), add_rule bumps gamma_epoch,
    // which the dispatcher shares via with_shared_epoch.
    let name = s.interner.intern("noop_rule");
    let et = s.interner.intern("any_edge");
    let a = s.interner.intern("a");
    let b = s.interner.intern("b");
    s.add_rule(crate::rewrite::RewriteRule {
        name,
        match_edges: vec![crate::rewrite::MatchEdge {
            src_var: a, edge_type: et, tgt_var: b,
        }],
        where_: None,
        effects: vec![],
        ..Default::default()
    });

    // Cache lookup now misses (artefact stamped at old epoch).
    assert!(dispatcher.get_compiled(kind).is_none(),
            "Γ mutation must invalidate JIT'd cache entry");
    assert!(!dispatcher.has_fresh_cached(kind));

    dispatcher.shutdown();
}

/// Demonstrates the full L2 second-order observability path:
/// dispatch → JIT → cache → snapshot → install into graph →
/// reflex-style introspection.
#[test]
fn dispatch_jit_snapshot_introspect_round_trip() {
    use crate::l2_graph_bridge::{
        install_snapshot_into_graph, register_dispatcher_schema,
    };

    let mut s = empty_substrate();
    register_dispatcher_schema(&mut s);
    let dispatcher: AdaptiveDispatcher<JittedFn> =
        AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy { threshold: 3, cooling_threshold: 3 },
            CodeCacheConfig::default(),
            s.gamma_epoch(),
        );

    // Compile + install JIT for two different kinds.
    let l1 = s.terms.add(TermNode::Lit { value: Value::Int(1) });
    let l9 = s.terms.add(TermNode::Lit { value: Value::Int(9) });
    let plus_one_nine = s.terms.add(TermNode::Plus { items: vec![l1, l9] });
    let kind_a = s.interner.intern("rule_a_plus_one_nine");

    let l4 = s.terms.add(TermNode::Lit { value: Value::Int(4) });
    let l5 = s.terms.add(TermNode::Lit { value: Value::Int(5) });
    let plus_four_five = s.terms.add(TermNode::Plus { items: vec![l4, l5] });
    let kind_b = s.interner.intern("rule_b_plus_four_five");

    for _ in 0..3 { dispatcher.hot_counter().record(kind_a); }
    for _ in 0..3 { dispatcher.hot_counter().record(kind_b); }
    let jit_a = jit::compile(&s.terms, plus_one_nine, &FxHashMap::default())
        .expect("compile a");
    let jit_b = jit::compile(&s.terms, plus_four_five, &FxHashMap::default())
        .expect("compile b");
    let size_a = jit_a.code_len();
    let size_b = jit_b.code_len();
    dispatcher.install_compiled(kind_a, jit_a);
    dispatcher.install_compiled(kind_b, jit_b);

    // Snapshot + install into graph.
    let snap = dispatcher.snapshot();
    assert_eq!(snap.cached.len(), 2);
    assert_eq!(snap.total_cache_bytes, size_a + size_b);
    let dispatcher_node = install_snapshot_into_graph(
        &mut s, &snap, "live_dispatcher");

    // Walk the graph: find the CachedArtefact for rule_a, verify
    // its code_size_bytes attr matches the JIT'd size.
    let cached_t = s.interner.lookup("CachedArtefact").unwrap();
    let kind_sym_attr = s.interner.lookup("kind").unwrap();
    let code_size_attr = s.interner.lookup("code_size_bytes").unwrap();
    let mut found_a_size: Option<i64> = None;
    for nid in s.graph.nodes_of_type(cached_t) {
        let nd = s.graph.node(nid);
        if let Some(Value::Str(ks)) = nd.attrs.get(&kind_sym_attr) {
            if *ks == kind_a {
                if let Some(Value::Int(sz)) = nd.attrs.get(&code_size_attr) {
                    found_a_size = Some(*sz);
                }
            }
        }
    }
    assert_eq!(found_a_size, Some(size_a as i64),
               "graph-side introspection should find rule_a's JIT'd size");

    // Calling the cached JIT through the dispatcher still works.
    let cached_a = dispatcher.get_compiled(kind_a).expect("a cached");
    assert_eq!(cached_a.inner.call_pure(&[]), 10);
    drop(cached_a);
    let cached_b = dispatcher.get_compiled(kind_b).expect("b cached");
    assert_eq!(cached_b.inner.call_pure(&[]), 9);
    drop(cached_b);

    let _ = dispatcher_node;
    dispatcher.shutdown();
}
