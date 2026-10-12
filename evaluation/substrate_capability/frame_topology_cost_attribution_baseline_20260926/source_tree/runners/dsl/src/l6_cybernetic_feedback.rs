//! L6 cybernetic feedback at system scale.
//!
//! Realises the `cybernetic_feedback_at_system_scale` component of the
//! `universal_coordination` Mt (commit c383b6c).
//!
//! ## What the Mt says
//!
//! > "Wiener's universal feedback pattern applied at the SYSTEM level —
//! >  every layer's output becomes feedback for adjacent layers. L1's
//! >  allocation rate feeds L2's dispatch policy; L2's hot counters
//! >  feed L3's gain scheduler; L3's drives feed L4's subsystem
//! >  weighting; L4's subsystem load feeds L5's compile priorities.
//! >  The loop is closed not just within layers but ACROSS layers."
//!
//! ## What's already wired
//!
//! - **L2 → L3** — gain scheduling driven by L2 hot counters
//!   (commit 148c339, `l3_gain_scheduling.rs`).
//!
//! ## What this commit adds
//!
//! A general **`CyberneticFeedbackLoop`** + concrete channels that
//! read L6 essential variables + emit feedback recommendations for
//! lower-layer adjustments. The recommendations are emitted as
//! `FeedbackRecommendation` values; routing them to actual layer
//! mutators is left to the caller (substrate-integration scope).
//!
//! Why recommendations rather than direct mutation: the substrate's
//! lower layers don't all have runtime-adjustable policies yet
//! (e.g. `CodeCacheConfig.max_bytes` is fixed at construction).
//! Emitting recommendations decouples *what should change* from
//! *who applies it*, lets test fixtures verify the feedback logic
//! without needing every layer to expose mutation surfaces, and
//! creates a named signal surface (Mt rule
//! `cross_layer_signals_use_named_surfaces`).
//!
//! ## Mt invariants realised
//!
//! - `every_layer_feeds_every_other_via_named_signal` — channels are
//!   the named signal surface; consumers register by name.
//! - `coordination_latency_within_tick_period` — `tick()` is O(N) in
//!   channel count + per-channel work; bounded.
//! - `circular_causality_between_layers` — channels read L6 essential
//!   variables (which other layers update via Arc handles) + emit
//!   recommendations for those layers; the loop is closed.

use std::sync::Arc;

use crate::l6_essential_variables::{EssentialVariable, ViabilityStatus};

/// A feedback recommendation emitted by a channel. Free-form
/// adjustment name + scalar parameter + named target layer so the
/// consumer can route + apply.
#[derive(Debug, Clone)]
pub struct FeedbackRecommendation {
    /// Name of the essential variable (or other signal) that
    /// triggered this recommendation.
    pub source_variable: String,
    /// The source's current value at trigger time.
    pub source_value: f64,
    /// The source's status (Nominal/NearEdge/Breach).
    pub source_status: ViabilityStatus,
    /// Free-form name of the suggested adjustment.
    pub adjustment_name: String,
    /// Scalar parameter for the adjustment. Interpretation is the
    /// adjustment's responsibility — e.g. multiplier, delta, ratio.
    pub adjustment_scalar: f64,
    /// Named target layer the recommendation is for (e.g.
    /// "L2_dispatch", "L1_cache", "L3_drives").
    pub target_layer: String,
}

/// A feedback channel: observes a signal, emits a recommendation
/// when action is warranted.
pub trait FeedbackChannel: Send + Sync {
    fn name(&self) -> &str;
    /// Read current state + emit recommendation. Returns `None` if
    /// no action is needed this tick (e.g. source is Nominal).
    fn tick(&self) -> Option<FeedbackRecommendation>;
}

// =======================================================================
// EssentialVariableChannel — observes an EssentialVariable; emits a
// recommendation on NearEdge or Breach with caller-specified scalars.
// =======================================================================

/// The canonical channel pattern: tie an essential variable's
/// status to a suggested adjustment.
///
/// Typical use: configure with `near_edge_scalar` (preemptive tighten)
/// and `breach_scalar` (degraded-mode tighten). Channel emits the
/// scalar matching the variable's current status; `Nominal` emits
/// nothing.
pub struct EssentialVariableChannel {
    name: String,
    variable: Arc<dyn EssentialVariable>,
    adjustment_name: String,
    target_layer: String,
    near_edge_scalar: f64,
    breach_scalar: f64,
}

impl EssentialVariableChannel {
    pub fn new(
        name: impl Into<String>,
        variable: Arc<dyn EssentialVariable>,
        target_layer: impl Into<String>,
        adjustment_name: impl Into<String>,
        near_edge_scalar: f64,
        breach_scalar: f64,
    ) -> Self {
        Self {
            name: name.into(),
            variable,
            adjustment_name: adjustment_name.into(),
            target_layer: target_layer.into(),
            near_edge_scalar,
            breach_scalar,
        }
    }
}

impl FeedbackChannel for EssentialVariableChannel {
    fn name(&self) -> &str {
        &self.name
    }
    fn tick(&self) -> Option<FeedbackRecommendation> {
        let status = self.variable.status();
        let scalar = match status {
            ViabilityStatus::Nominal => return None,
            ViabilityStatus::NearEdge => self.near_edge_scalar,
            ViabilityStatus::Breach => self.breach_scalar,
        };
        Some(FeedbackRecommendation {
            source_variable: self.variable.name().to_string(),
            source_value: self.variable.current_value(),
            source_status: status,
            adjustment_name: self.adjustment_name.clone(),
            adjustment_scalar: scalar,
            target_layer: self.target_layer.clone(),
        })
    }
}

// =======================================================================
// CyberneticFeedbackLoop — aggregates channels + ticks them per cycle.
// =======================================================================

pub struct CyberneticFeedbackLoop {
    channels: Vec<Box<dyn FeedbackChannel>>,
}

impl CyberneticFeedbackLoop {
    pub fn new() -> Self {
        Self {
            channels: Vec::new(),
        }
    }

    pub fn add(&mut self, channel: Box<dyn FeedbackChannel>) {
        self.channels.push(channel);
    }

    /// Run all channels. Returns the list of recommendations emitted
    /// this tick (empty if all channels are Nominal).
    pub fn tick(&self) -> Vec<FeedbackRecommendation> {
        self.channels.iter().filter_map(|c| c.tick()).collect()
    }

    pub fn channel_count(&self) -> usize {
        self.channels.len()
    }

    /// Tick + route each recommendation to a consumer. The consumer's
    /// `consume` is called once per emitted recommendation; the
    /// consumer is free to apply the adjustment to whatever layer
    /// state it knows how to mutate.
    pub fn tick_with_consumer<C: FeedbackConsumer>(&self, consumer: &mut C) -> usize {
        let recs = self.tick();
        let n = recs.len();
        for r in &recs {
            consumer.consume(r);
        }
        n
    }
}

impl Default for CyberneticFeedbackLoop {
    fn default() -> Self {
        Self::new()
    }
}

/// Consumer of feedback recommendations. The substrate's
/// integration layer implements this to route recommendations to
/// actual layer mutators (CodeCacheConfig, TierUpPolicy, drive
/// weights, etc.).
pub trait FeedbackConsumer {
    fn consume(&mut self, rec: &FeedbackRecommendation);
}

// =======================================================================
// RecommendationApplier — concrete consumer that holds knob handles
// + applies recommendations by writing to the relevant atomic.
// =======================================================================

use std::collections::HashMap;
use std::sync::atomic::{AtomicU64, Ordering};

/// Concrete `FeedbackConsumer` that holds knob handles (typically
/// installed via `AdaptiveDispatcher::install_threshold_knob`) and
/// routes recommendations to them by `(adjustment_name, target_layer)`.
/// The scalar in the recommendation becomes the new knob value.
///
/// For v1 the routing is simple: each recommendation's scalar is
/// rounded + stored as the new u64 value (with a minimum floor of 1).
/// Production usage would have per-adjustment policies (smoothing,
/// ramp-up/down, hysteresis).
#[derive(Default)]
pub struct RecommendationApplier {
    knobs_u64: HashMap<(String, String), Arc<AtomicU64>>,
    /// Applied recommendations (for inspection + tests).
    pub applied: Vec<FeedbackRecommendation>,
    /// Ignored recommendations — no knob registered for their
    /// (adjustment_name, target_layer) pair.
    pub ignored: Vec<FeedbackRecommendation>,
}

impl RecommendationApplier {
    pub fn new() -> Self {
        Self::default()
    }

    /// Register a knob handle for the (adjustment_name, target_layer)
    /// pair. The knob is typically obtained from a layer-side
    /// `install_*_knob` method.
    pub fn register_knob_u64(
        &mut self,
        adjustment_name: &str,
        target_layer: &str,
        knob: Arc<AtomicU64>,
    ) {
        self.knobs_u64.insert(
            (adjustment_name.to_string(), target_layer.to_string()),
            knob,
        );
    }

    /// Inspect the current value of a registered knob.
    pub fn knob_value(&self, adjustment_name: &str, target_layer: &str) -> Option<u64> {
        self.knobs_u64
            .get(&(adjustment_name.to_string(), target_layer.to_string()))
            .map(|k| k.load(Ordering::Acquire))
    }
}

impl FeedbackConsumer for RecommendationApplier {
    fn consume(&mut self, rec: &FeedbackRecommendation) {
        let key = (rec.adjustment_name.clone(), rec.target_layer.clone());
        if let Some(knob) = self.knobs_u64.get(&key) {
            // Round + floor; substrate's adjustments are positive integers.
            let new_val = rec.adjustment_scalar.max(1.0) as u64;
            knob.store(new_val, Ordering::Release);
            self.applied.push(rec.clone());
        } else {
            self.ignored.push(rec.clone());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::l6_essential_variables::{
        DeadlineMeetRate, DriveStarvation, EssentialVariableMonitor, WorkingSetFit,
    };

    /// Nominal variable → no recommendation.
    #[test]
    fn channel_silent_when_variable_nominal() {
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        let ch = EssentialVariableChannel::new(
            "wsf_to_cache",
            Arc::clone(&wsf) as _,
            "L1_cache",
            "tighten_cache",
            0.9,
            0.5,
        );
        // wsf at 0 → Nominal → no recommendation.
        assert!(ch.tick().is_none());
    }

    /// NearEdge → recommendation with near_edge_scalar.
    #[test]
    fn channel_emits_near_edge_scalar() {
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        let ch = EssentialVariableChannel::new(
            "wsf_to_cache",
            Arc::clone(&wsf) as _,
            "L1_cache",
            "tighten_cache",
            0.9,
            0.5,
        );
        // Near-edge zone: 0.9 - 0.09 = 0.81 → 0.9. Update to 0.85.
        wsf.update(850);
        let rec = ch.tick().expect("NearEdge should emit");
        assert_eq!(rec.source_status, ViabilityStatus::NearEdge);
        assert_eq!(rec.adjustment_scalar, 0.9);
        assert_eq!(rec.target_layer, "L1_cache");
        assert_eq!(rec.adjustment_name, "tighten_cache");
        assert_eq!(rec.source_variable, "wsf");
    }

    /// Breach → recommendation with breach_scalar.
    #[test]
    fn channel_emits_breach_scalar() {
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        let ch = EssentialVariableChannel::new(
            "wsf_to_cache",
            Arc::clone(&wsf) as _,
            "L1_cache",
            "tighten_cache",
            0.9,
            0.5,
        );
        // Breach: > 0.9.
        wsf.update(950);
        let rec = ch.tick().expect("Breach should emit");
        assert_eq!(rec.source_status, ViabilityStatus::Breach);
        assert_eq!(rec.adjustment_scalar, 0.5);
    }

    /// Loop aggregates multiple channels — all recommendations come
    /// back from one tick.
    #[test]
    fn loop_aggregates_channels() {
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        let ds: Arc<DriveStarvation> = Arc::new(DriveStarvation::new("ds", 100));
        let mut loop_ = CyberneticFeedbackLoop::new();
        loop_.add(Box::new(EssentialVariableChannel::new(
            "wsf_ch",
            Arc::clone(&wsf) as _,
            "L1_cache",
            "tighten_cache",
            0.9,
            0.5,
        )));
        loop_.add(Box::new(EssentialVariableChannel::new(
            "ds_ch",
            Arc::clone(&ds) as _,
            "L3_drives",
            "boost_starved",
            1.2,
            2.0,
        )));
        // Both nominal → no recommendations.
        assert!(loop_.tick().is_empty());

        // Both breach.
        wsf.update(950);
        ds.record_fire(1);
        for _ in 0..110 {
            ds.advance_tick();
        }
        let recs = loop_.tick();
        assert_eq!(recs.len(), 2);
        let sources: Vec<&str> = recs.iter().map(|r| r.source_variable.as_str()).collect();
        assert!(sources.contains(&"wsf"));
        assert!(sources.contains(&"ds"));
    }

    /// `tick_with_consumer` routes each recommendation to the
    /// consumer. Verifies Mt rule `cross_layer_signals_use_named_
    /// surfaces` — channels emit; consumer applies; no layer reads
    /// another's internals.
    #[test]
    fn loop_routes_to_consumer() {
        struct CollectingConsumer {
            received: Vec<FeedbackRecommendation>,
        }
        impl FeedbackConsumer for CollectingConsumer {
            fn consume(&mut self, rec: &FeedbackRecommendation) {
                self.received.push(rec.clone());
            }
        }

        let dmr: Arc<DeadlineMeetRate> = Arc::new(DeadlineMeetRate::new("dmr", 10, 0.95));
        let mut loop_ = CyberneticFeedbackLoop::new();
        loop_.add(Box::new(EssentialVariableChannel::new(
            "dmr_ch",
            Arc::clone(&dmr) as _,
            "L2_dispatch",
            "lower_threshold",
            0.5,
            0.1,
        )));
        let mut consumer = CollectingConsumer {
            received: Vec::new(),
        };

        // Nominal — no callback fires.
        loop_.tick_with_consumer(&mut consumer);
        assert!(consumer.received.is_empty());

        // Push DMR to breach.
        for _ in 0..10 {
            dmr.record(false);
        }
        let n = loop_.tick_with_consumer(&mut consumer);
        assert_eq!(n, 1);
        assert_eq!(consumer.received.len(), 1);
        assert_eq!(consumer.received[0].adjustment_name, "lower_threshold");
        assert_eq!(consumer.received[0].target_layer, "L2_dispatch");
        assert_eq!(consumer.received[0].adjustment_scalar, 0.1);
    }

    /// `RecommendationApplier` routes recommendations to registered
    /// knob handles + writes the scalar to the atomic. Demonstrates
    /// the full feedback loop: variable breach → channel emits →
    /// applier writes knob → layer reads new value.
    #[test]
    fn applier_writes_to_registered_knob() {
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        let mut loop_ = CyberneticFeedbackLoop::new();
        loop_.add(Box::new(EssentialVariableChannel::new(
            "wsf_to_cache",
            Arc::clone(&wsf) as _,
            "L1_cache",
            "tighten_cache_bytes",
            500.0,
            100.0,
        )));

        let mut applier = RecommendationApplier::new();
        let cache_knob = Arc::new(AtomicU64::new(1000));
        applier.register_knob_u64("tighten_cache_bytes", "L1_cache", Arc::clone(&cache_knob));

        // Nominal: no change.
        loop_.tick_with_consumer(&mut applier);
        assert!(applier.applied.is_empty());
        assert_eq!(cache_knob.load(Ordering::Acquire), 1000);

        // Push into breach: scalar 100 stores as new knob value.
        wsf.update(950);
        loop_.tick_with_consumer(&mut applier);
        assert_eq!(applier.applied.len(), 1);
        assert_eq!(cache_knob.load(Ordering::Acquire), 100);
    }

    /// Applier reports recommendations with no registered knob
    /// in `ignored` rather than silently dropping.
    #[test]
    fn applier_tracks_ignored_recommendations() {
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        let mut loop_ = CyberneticFeedbackLoop::new();
        loop_.add(Box::new(EssentialVariableChannel::new(
            "wsf_ch",
            Arc::clone(&wsf) as _,
            "L1_cache",
            "no_such_adjustment",
            1.0,
            1.0,
        )));
        let mut applier = RecommendationApplier::new();
        wsf.update(950);
        loop_.tick_with_consumer(&mut applier);
        assert!(applier.applied.is_empty());
        assert_eq!(applier.ignored.len(), 1);
    }

    /// End-to-end: configure 4 channels (one per essential variable),
    /// breach a specific one, verify only that recommendation is
    /// emitted. Mirrors the L6 layer the substrate's coordination
    /// loop would assemble at startup.
    #[test]
    fn end_to_end_four_channels_per_variable() {
        let dmr: Arc<DeadlineMeetRate> =
            Arc::new(DeadlineMeetRate::new("deadline_meet_rate", 100, 0.95));
        let wsf: Arc<WorkingSetFit> =
            Arc::new(WorkingSetFit::new("working_set_fit", 32 * 1024 * 1024, 0.9));
        let ds: Arc<DriveStarvation> = Arc::new(DriveStarvation::new("drive_starvation", 50));

        // Aggregate into one EssentialVariableMonitor too (composes).
        let mut mon = EssentialVariableMonitor::new(0.1);
        mon.add(Arc::clone(&dmr) as _);
        mon.add(Arc::clone(&wsf) as _);
        mon.add(Arc::clone(&ds) as _);

        let mut loop_ = CyberneticFeedbackLoop::new();
        loop_.add(Box::new(EssentialVariableChannel::new(
            "dmr_to_L2",
            Arc::clone(&dmr) as _,
            "L2_dispatch",
            "lower_tier_up_threshold",
            0.5,
            0.1,
        )));
        loop_.add(Box::new(EssentialVariableChannel::new(
            "wsf_to_L1",
            Arc::clone(&wsf) as _,
            "L1_cache",
            "tighten_cache_bytes",
            0.9,
            0.5,
        )));
        loop_.add(Box::new(EssentialVariableChannel::new(
            "ds_to_L3",
            Arc::clone(&ds) as _,
            "L3_drives",
            "boost_starved_drive_weight",
            1.5,
            3.0,
        )));

        // Nominal start.
        assert!(loop_.tick().is_empty());
        assert!(!mon.any_breach());

        // Push DMR to breach (the substrate is missing deadlines).
        for _ in 0..100 {
            dmr.record(false);
        }
        let recs = loop_.tick();
        assert_eq!(recs.len(), 1);
        assert_eq!(recs[0].target_layer, "L2_dispatch");
        assert_eq!(recs[0].adjustment_name, "lower_tier_up_threshold");
        assert_eq!(recs[0].adjustment_scalar, 0.1);
        // The monitor sees the same breach.
        assert!(mon.any_breach());
    }
}
