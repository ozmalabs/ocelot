//! Full-stack substrate integration tests.
//!
//! Wires every layer's realised pieces into one coherent runtime +
//! exercises end-to-end scenarios to verify the cross-layer signals
//! actually close their loops.
//!
//! Components composed:
//!
//! - L1: `Substrate` (typed graph) + `gamma_epoch`
//! - L2: `Scheduler` + `AdaptiveDispatcher` + `CodeCache`
//! - L3: `Drive` + `PidController` + `KalmanFilter1D` +
//!       `TableLookupGainScheduler`
//! - L4: `SubsystemRegistry` + `MetaShape` tagging
//! - L5: `jit::compile` of Term-trees → `JittedFn`
//! - L6: `EssentialVariableMonitor` + `CyberneticFeedbackLoop` +
//!       `RecommendationApplier` + `AshbyVarietyCheck`
//! - Shared: `code_cache::CodeCache` reclamation
//!
//! These tests are the strongest empirical claim about substrate_rs
//! to date — not "each piece works in isolation" but "the whole
//! composition holds together when a substrate-level scenario
//! exercises it".

#![cfg(all(target_arch = "x86_64", target_os = "linux"))]
#![cfg(test)]

use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

use rustc_hash::FxHashMap;

use crate::checker::ConsistencyChecker;
use crate::code_cache::{CodeCacheConfig, CodeSize};
use crate::grammar::Grammar;
use crate::jit::{self, JittedFn};
use crate::l2_adaptive::{
    AdaptiveDispatcher, DispatchOutcome, TierUpPolicy, TypedTask,
};
use crate::l2_dispatch::{PriorityClass, Scheduler};
use crate::l3_drives::{
    Controller, Drive, KalmanFilter1D, MultiDriveSystem, PidController,
};
use crate::l3_gain_scheduling::{InterpolatingGainScheduler, GainScheduler};
use crate::l4_subsystem_boundaries::{MetaShape, SubsystemRegistry};
use crate::l6_ashby_variety::AshbyVarietyCheck;
use crate::l6_cybernetic_feedback::{
    CyberneticFeedbackLoop, EssentialVariableChannel,
    FeedbackConsumer, RecommendationApplier,
};
use crate::l6_essential_variables::{
    DeadlineMeetRate, DriveStarvation, EssentialVariableMonitor,
    WorkingSetFit,
};
use crate::substrate::Substrate;
use crate::term::TermNode;
use crate::value::Value;

fn empty_substrate() -> Substrate {
    Substrate::new(ConsistencyChecker::new(Grammar::new()))
}

// =======================================================================
// Test 1: Full stack composition smoke test
// =======================================================================

/// Construct one of everything + verify they connect without panic.
/// Realistic startup sequence the substrate's runtime entry point
/// would execute.
#[test]
fn full_stack_constructs_without_panic() {
    // L1 substrate.
    let mut s = empty_substrate();

    // L2 dispatcher (sharing substrate's gamma_epoch).
    let mut dispatcher: AdaptiveDispatcher<JittedFn> =
        AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(2),
            TierUpPolicy { threshold: 10, cooling_threshold: 3 },
            CodeCacheConfig { max_bytes: 1024 * 1024 },
            s.gamma_epoch(),
        );
    let threshold_knob = dispatcher.install_threshold_knob();

    // L3 drives.
    let mut drives = MultiDriveSystem::new();
    let kf = KalmanFilter1D::new(0.0, 10.0, 0.01, 1.0);
    let pid = PidController::new(1.0, 0.1, 0.05);
    drives.add(Drive::new("curiosity", 0.5, kf, Box::new(pid))
                .with_weight(1.0));

    // L4 subsystem registry.
    let mut subsys = SubsystemRegistry::new();
    subsys.register("dispatch", MetaShape::SelectiveGating);
    subsys.register("drive_step", MetaShape::FeedbackControl);
    subsys.register_bridge("gain_scheduling",
        MetaShape::SelectiveGating,
        MetaShape::FeedbackControl);
    assert!(subsys.enforce("dispatch", "drive_step").is_ok());

    // L6 essential variables.
    let dmr: Arc<DeadlineMeetRate> =
        Arc::new(DeadlineMeetRate::new("deadline_meet_rate", 100, 0.95));
    let wsf: Arc<WorkingSetFit> =
        Arc::new(WorkingSetFit::new("working_set_fit", 32 * 1024 * 1024, 0.9));
    let mut mon = EssentialVariableMonitor::new(0.1);
    mon.add(Arc::clone(&dmr) as _);
    mon.add(Arc::clone(&wsf) as _);

    // L6 cybernetic feedback loop.
    let mut feedback = CyberneticFeedbackLoop::new();
    feedback.add(Box::new(EssentialVariableChannel::new(
        "dmr_to_L2", Arc::clone(&dmr) as _,
        "L2_dispatch", "lower_tier_up_threshold",
        5.0, 1.0,
    )));

    // L6 recommendation applier wired to the threshold knob.
    let mut applier = RecommendationApplier::new();
    applier.register_knob_u64(
        "lower_tier_up_threshold", "L2_dispatch",
        Arc::clone(&threshold_knob));

    // L6 Ashby variety check.
    let mut ashby = AshbyVarietyCheck::new();
    ashby.register_regulator("L2_dispatch");
    ashby.register_regulator("L3_drives");
    ashby.register_disturbance("deadline_meet_rate");
    ashby.register_disturbance("working_set_fit");
    ashby.register_coverage("L2_dispatch", "deadline_meet_rate");
    ashby.register_coverage("L3_drives", "working_set_fit");
    assert!(ashby.variety_match_holds());

    // Smoke: one tick through each layer.
    let kind = s.interner.intern("test_kind");
    let _ = dispatcher.submit(TypedTask {
        kind,
        deadline: Instant::now() + Duration::from_millis(100),
        class: PriorityClass::BestEffort,
        work: Box::new(|| {}),
    });
    let _ = drives.step_weighted_average(0.01);
    let _ = mon.tick();
    let _ = feedback.tick_with_consumer(&mut applier);

    dispatcher.shutdown();
}

// =======================================================================
// Test 2: Cybernetic loop actually closes — breach drives knob change
// =======================================================================

/// Demonstrate the FULL cybernetic loop closing:
///   1. Substrate misses deadlines → DMR records misses
///   2. EssentialVariable status → Breach
///   3. CyberneticFeedbackLoop channel emits recommendation
///   4. RecommendationApplier writes new value to threshold_knob
///   5. AdaptiveDispatcher's effective_threshold reads the new value
///   6. Subsequent submit at the new threshold gets TierUp
#[test]
fn cybernetic_loop_closes_breach_changes_threshold() {
    let mut s = empty_substrate();
    let mut dispatcher: AdaptiveDispatcher<JittedFn> =
        AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy { threshold: 100, cooling_threshold: 3 },
            CodeCacheConfig::default(),
            s.gamma_epoch(),
        );
    let threshold_knob = dispatcher.install_threshold_knob();

    // L6 — DMR + channel + applier.
    let dmr: Arc<DeadlineMeetRate> =
        Arc::new(DeadlineMeetRate::new("dmr", 10, 0.95));
    let mut feedback = CyberneticFeedbackLoop::new();
    feedback.add(Box::new(EssentialVariableChannel::new(
        "dmr_to_L2", Arc::clone(&dmr) as _,
        "L2_dispatch", "lower_tier_up_threshold",
        50.0,  // near_edge_scalar
        5.0,   // breach_scalar — drops threshold from 100 to 5
    )));
    let mut applier = RecommendationApplier::new();
    applier.register_knob_u64(
        "lower_tier_up_threshold", "L2_dispatch",
        Arc::clone(&threshold_knob));

    // Initial threshold.
    assert_eq!(threshold_knob.load(Ordering::Acquire), 100);

    // Simulate substrate missing deadlines → DMR records misses.
    for _ in 0..10 { dmr.record(false); }

    // Cybernetic feedback tick: channel emits Breach → applier writes 5.
    let n_applied = feedback.tick_with_consumer(&mut applier);
    assert_eq!(n_applied, 1);
    assert_eq!(threshold_knob.load(Ordering::Acquire), 5);

    // Verify the new threshold takes effect: submit 5 tasks; on
    // the 5th, dispatcher should signal TierUp at the NEW threshold.
    let kind = s.interner.intern("hot_kind");
    let mut outcomes = Vec::new();
    for _ in 0..6 {
        outcomes.push(dispatcher.submit(TypedTask {
            kind,
            deadline: Instant::now() + Duration::from_secs(60),
            class: PriorityClass::BestEffort,
            work: Box::new(|| {}),
        }));
    }
    // 1-4: Queued; 5: TierUp; 6: Queued (post-tier-up).
    for (idx, o) in outcomes.iter().enumerate() {
        let n = (idx + 1) as u64;
        match (n, *o) {
            (5, DispatchOutcome::TierUp { count, .. }) => {
                assert_eq!(count, 5);
            }
            (_, DispatchOutcome::Queued { count, .. }) => {
                assert_eq!(count, n);
            }
            _ => panic!("submit {} unexpected: {:?}", n, o),
        }
    }
    std::thread::sleep(Duration::from_millis(20));
    dispatcher.drain_and_shutdown();
}

// =======================================================================
// Test 3: Cross-layer signal — L2 hot counter feeds L3 gain scheduler
// =======================================================================

/// Verifies the L2↔L3 bridge from commit 148c339 works in the full
/// stack: L2 records hot counts; L3 gain scheduler reads them; PID
/// gains track the dominant kind.
#[test]
fn l2_hot_counter_feeds_l3_gain_scheduler() {
    let s = empty_substrate();
    let dispatcher: AdaptiveDispatcher<JittedFn> =
        AdaptiveDispatcher::new(
            Scheduler::new(1),
            TierUpPolicy::default(),
            CodeCacheConfig::default(),
        );

    // L3 PID controller + gain scheduler.
    let mut pid = PidController::new(1.0, 0.5, 0.1);
    let mut sched = InterpolatingGainScheduler::new((1.0, 0.5, 0.1));
    let mut interner = s.interner;
    let k_calm = interner.intern("calm");
    let k_volatile = interner.intern("volatile");
    sched.insert(k_calm,     (5.0, 0.5, 0.05));
    sched.insert(k_volatile, (1.0, 0.0, 0.5));

    let hot = dispatcher.hot_counter();
    // Push calm dominant.
    for _ in 0..100 { hot.record(k_calm); }
    pid.apply_scheduled(&mut sched, &hot);
    // Calm gains.
    assert!((pid.kp - 5.0).abs() < 1e-9);

    // Push volatile to dominant.
    for _ in 0..200 { hot.record(k_volatile); }
    pid.apply_scheduled(&mut sched, &hot);
    // Blend: 100 calm + 200 volatile → 1/3 calm, 2/3 volatile.
    let expected_kp = (1.0 / 3.0) * 5.0 + (2.0 / 3.0) * 1.0;
    assert!((pid.kp - expected_kp).abs() < 1e-9,
            "blended kp expected {}, got {}", expected_kp, pid.kp);
    dispatcher.shutdown();
}

// =======================================================================
// Test 4: Γ mutation propagates through dispatcher → invalidates JIT
// =======================================================================

/// Verifies the L1→L2 signal via Substrate::gamma_epoch end-to-end
/// through actual JIT-compiled code.
#[test]
fn gamma_mutation_propagates_to_jit_cache_invalidation() {
    let mut s = empty_substrate();
    let dispatcher: AdaptiveDispatcher<JittedFn> =
        AdaptiveDispatcher::with_shared_epoch(
            Scheduler::new(1),
            TierUpPolicy { threshold: 2, cooling_threshold: 3 },
            CodeCacheConfig::default(),
            s.gamma_epoch(),
        );
    // Build + JIT-compile a Term-tree.
    let l3 = s.terms.add(TermNode::Lit { value: Value::Int(3) });
    let l4 = s.terms.add(TermNode::Lit { value: Value::Int(4) });
    let plus = s.terms.add(TermNode::Plus { items: vec![l3, l4] });
    let kind = s.interner.intern("plus_three_four");

    // Pump up hot counter + install JIT.
    for _ in 0..2 { dispatcher.hot_counter().record(kind); }
    let jit_fn = jit::compile(&s.terms, plus, &FxHashMap::default())
        .expect("compile");
    dispatcher.install_compiled(kind, jit_fn);
    let cached = dispatcher.get_compiled(kind).expect("cached");
    assert_eq!(cached.inner.call_pure(&[]), 7);
    drop(cached);

    // Substrate-side Γ mutation: add a rule. Bumps gamma_epoch via
    // shared Arc. Dispatcher sees stale on next lookup.
    let name = s.interner.intern("noop");
    let et = s.interner.intern("e");
    let av = s.interner.intern("a");
    let bv = s.interner.intern("b");
    s.add_rule(crate::rewrite::RewriteRule {
        name,
        match_edges: vec![crate::rewrite::MatchEdge {
            src_var: av, edge_type: et, tgt_var: bv,
        }],
        where_: None,
        effects: vec![],
        ..Default::default()
    });
    // Cache now miss — Γ has changed.
    assert!(dispatcher.get_compiled(kind).is_none());
    dispatcher.shutdown();
}

// =======================================================================
// Test 5: L4 subsystem boundary catches misregistered cross-call
// =======================================================================

#[test]
fn l4_boundary_catches_implicit_cross_subsystem_call() {
    let mut r = SubsystemRegistry::new();
    r.register("dispatch_submit", MetaShape::SelectiveGating);
    r.register("drive_step",      MetaShape::FeedbackControl);
    r.register("kalman_update",   MetaShape::PredictionMinusObservation);
    // Register the L2→L3 gain-scheduling bridge.
    r.register_bridge("gain_scheduling",
        MetaShape::SelectiveGating,
        MetaShape::FeedbackControl);
    // L2 calling L3 via gain scheduling — allowed (bridge exists).
    assert!(r.enforce("dispatch_submit", "drive_step").is_ok());
    // L2 calling Kalman directly — bridge NOT registered. Caught.
    let result = r.enforce("dispatch_submit", "kalman_update");
    assert!(result.is_err());
}

// =======================================================================
// Test 6: Ashby variety check over the realistic substrate setup
// =======================================================================

#[test]
fn ashby_check_passes_with_realistic_coverage() {
    let mut a = AshbyVarietyCheck::new();
    // Regulators (the layers that can act).
    a.register_regulator("L2_dispatch");
    a.register_regulator("L3_drives");
    a.register_regulator("L5_codegen");
    a.register_regulator("L6_feedback");
    // Disturbances (essential variables).
    a.register_disturbance("deadline_meet_rate");
    a.register_disturbance("working_set_fit");
    a.register_disturbance("gamma_epoch_coherence");
    a.register_disturbance("drive_starvation");
    // Coverage: each disturbance covered by at least one regulator.
    a.register_coverage("L2_dispatch", "deadline_meet_rate");
    a.register_coverage("L5_codegen",  "working_set_fit");
    a.register_coverage("L2_dispatch", "gamma_epoch_coherence");
    a.register_coverage("L3_drives",   "drive_starvation");
    assert!(a.variety_match_holds(),
            "V(R)={} >= V(D)={}",
            a.regulator_variety(), a.disturbance_variety());
    assert!(a.unregulated_disturbances().is_empty(),
            "all disturbances should be covered");
}

// =======================================================================
// Test 7: Multi-drive system with mixed controller types
// =======================================================================

/// Demonstrates substrate's drive surface composing PID + LQR drives
/// in one MultiDriveSystem. The Controller trait makes both types
/// plug-compatible.
#[test]
fn multi_drive_system_mixes_pid_and_lqr() {
    use crate::l3_lqr::ScalarLqrController;
    let mut sys = MultiDriveSystem::new();
    // PID drive.
    let kf1 = KalmanFilter1D::new(0.0, 10.0, 0.01, 1.0);
    let pid = PidController::new(1.0, 0.1, 0.05);
    sys.add(Drive::new("pid_drive", 5.0, kf1, Box::new(pid))
                .with_weight(1.0));
    // LQR drive.
    let kf2 = KalmanFilter1D::new(0.0, 10.0, 0.01, 1.0);
    let lqr = ScalarLqrController::from_scalar(1.0, 1.0, 1.0, 1.0)
        .expect("LQR construct");
    sys.add(Drive::new("lqr_drive", 3.0, kf2, Box::new(lqr))
                .with_weight(2.0));
    // Run one tick. Both drives' errors are positive (state < setpoint).
    let u = sys.step_weighted_average(0.1);
    // Both PID and LQR produce positive u for positive error.
    assert!(u > 0.0,
            "weighted average should be positive; got {}", u);
}

// =======================================================================
// Test 8: Subsystem operation count respects the analogy-weight
// dominance ordering
// =======================================================================

#[test]
fn subsystem_allocation_respects_analogy_weight_dominance() {
    // The substrate's expected baseline at startup: primary
    // subsystem (HIERARCHICAL_INVARIANCE_BUILDUP, weight 3078)
    // gets the most operations; FEEDBACK_CONTROL (weight 81)
    // gets the fewest.
    let mut r = SubsystemRegistry::new();
    // Allocate proportionally to analogy weights (rough integer divs).
    let allocations = [
        (MetaShape::HierarchicalInvarianceBuildup, 10),
        (MetaShape::SelectiveGating, 4),
        (MetaShape::GlobalMessagePassing, 3),
        (MetaShape::PredictionMinusObservation, 2),
        (MetaShape::CompetitiveInhibition, 2),
        (MetaShape::DelayedPersistence, 1),
        (MetaShape::FeedbackControl, 1),
    ];
    for (shape, count) in &allocations {
        for i in 0..*count {
            r.register(&format!("op_{:?}_{}", shape, i), *shape);
        }
    }
    let counts = r.ops_per_subsystem();
    // Primary dominates feedback.
    let primary = counts[&MetaShape::HierarchicalInvarianceBuildup];
    let feedback = counts[&MetaShape::FeedbackControl];
    assert!(primary > feedback * 5,
            "primary should dominate (primary={}, feedback={})",
            primary, feedback);
    // Ordering by weight: primary > selective > global > prediction
    //                     ≈ competitive > delayed = feedback.
    assert!(counts[&MetaShape::HierarchicalInvarianceBuildup]
            > counts[&MetaShape::SelectiveGating]);
    assert!(counts[&MetaShape::SelectiveGating]
            > counts[&MetaShape::GlobalMessagePassing]);
}
