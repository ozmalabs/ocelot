//! L6 essential variable monitoring.
//!
//! Realises the `essential_variables_with_viability_bounds` +
//! `viability_envelope_as_design_constraint` components of the
//! `universal_coordination` Mt (commit c383b6c) — the substrate's
//! top-level coordination layer that keeps the trajectory inside
//! the viability envelope by monitoring four essential variables
//! every tick.
//!
//! ## The four essential variables (per the L6 Mt)
//!
//! 1. **`DeadlineMeetRate`** — fraction of tick deadlines met over
//!    a sliding window. Bound: ≥ 95%. Below → reflexes aren't
//!    completing on time, substrate can't keep up with workload.
//!
//! 2. **`WorkingSetFit`** — ratio of working-set bytes to the
//!    architecture's L3 cache (~32 MiB on Zen 5). Bound: ≤ 90%.
//!    Above → working set blows L3, every operation hits DRAM,
//!    throughput collapses.
//!
//! 3. **`GammaEpochCoherence`** — count of retrograde-epoch reads
//!    observed. Bound: must equal 0. A retrograde read means a
//!    worker observed an older epoch than one it had previously
//!    seen — implies a memory-ordering bug, since `Epoch::bump`
//!    uses Release ordering. Detection here is defence-in-depth.
//!
//! 4. **`DriveStarvation`** — longest gap (in ticks) since any
//!    drive fired. Bound: ≤ N ticks. Above → a drive has been
//!    starved beyond the configured threshold, the substrate's
//!    multi-drive balance is broken.
//!
//! ## Mt rules realised
//!
//! - **`essential_variables_must_be_monitored_every_tick`** — the
//!   `EssentialVariableMonitor::tick` API runs all variables in one
//!   call; expected cadence is every L2 tick (100µs).
//! - **`viability_envelope_breach_triggers_degraded_mode`** —
//!   `tick_with_response` callback fires on transition to `Breach`,
//!   letting the substrate adjust drives + dispatch policy.
//! - **`cross_layer_signals_use_named_surfaces`** — variables are
//!   fed via explicit `record`/`update`/`observe` calls; no layer
//!   reads another layer's internals.
//! - **`coordination_latency_must_be_bounded`** — `tick` is O(N)
//!   in variable count + window size; bounded by configuration.

use std::collections::HashMap;
use std::collections::VecDeque;
use std::sync::atomic::{AtomicU64, AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};

/// Where a variable sits relative to its viability envelope.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum ViabilityStatus {
    /// Well inside envelope; no action needed.
    Nominal,
    /// Within `near_edge_margin` of a bound. Time to act preemptively.
    NearEdge,
    /// Outside the envelope. Degraded-mode response required.
    Breach,
}

/// An essential variable the substrate keeps in bounds.
pub trait EssentialVariable: Send + Sync {
    /// Stable identifier (also used as the graph-attr label when
    /// exposed via the L6↔Graph bridge — future commit).
    fn name(&self) -> &str;
    /// Current sampled value.
    fn current_value(&self) -> f64;
    /// Lower bound (`None` for variables with no lower bound).
    fn lower_bound(&self) -> Option<f64>;
    /// Upper bound (`None` for variables with no upper bound).
    fn upper_bound(&self) -> Option<f64>;

    /// Width of the near-edge zone in value units, applied to BOTH
    /// bounds uniformly.
    ///
    /// In practice most essential variables have a "trouble
    /// direction" — only one bound is the one to worry about
    /// approaching. The default returns 0 (no preemptive warning,
    /// only Breach when bounds are crossed). Variables override
    /// when preemptive warning on a specific approach matters
    /// (e.g. `WorkingSetFit` overrides to flag approach to the
    /// upper bound).
    fn near_edge_margin(&self) -> f64 {
        0.0
    }

    /// Status based on bounds + margin.
    fn status(&self) -> ViabilityStatus {
        let v = self.current_value();
        let lo = self.lower_bound();
        let hi = self.upper_bound();
        // Breach checks.
        if let Some(l) = lo {
            if v < l {
                return ViabilityStatus::Breach;
            }
        }
        if let Some(h) = hi {
            if v > h {
                return ViabilityStatus::Breach;
            }
        }
        // Near-edge checks (only if margin > 0).
        let margin = self.near_edge_margin();
        if margin > 0.0 {
            if let Some(l) = lo {
                if v - l < margin {
                    return ViabilityStatus::NearEdge;
                }
            }
            if let Some(h) = hi {
                if h - v < margin {
                    return ViabilityStatus::NearEdge;
                }
            }
        }
        ViabilityStatus::Nominal
    }
}

// =======================================================================
// 1. DeadlineMeetRate
// =======================================================================

/// Sliding-window deadline meet rate. `record(met)` per tick.
/// `current_value()` = met / window_size in [0, 1].
pub struct DeadlineMeetRate {
    name: String,
    window: Mutex<VecDeque<bool>>,
    window_size: usize,
    bound_low: f64,
}

impl DeadlineMeetRate {
    /// `bound_low` is the minimum acceptable rate (e.g. 0.95).
    pub fn new(name: impl Into<String>, window_size: usize, bound_low: f64) -> Self {
        Self {
            name: name.into(),
            window: Mutex::new(VecDeque::with_capacity(window_size)),
            window_size,
            bound_low,
        }
    }
    pub fn record(&self, met: bool) {
        let mut w = self.window.lock().unwrap();
        if w.len() >= self.window_size {
            w.pop_front();
        }
        w.push_back(met);
    }
    pub fn sample_count(&self) -> usize {
        self.window.lock().unwrap().len()
    }
}

impl EssentialVariable for DeadlineMeetRate {
    fn name(&self) -> &str {
        &self.name
    }
    fn current_value(&self) -> f64 {
        let w = self.window.lock().unwrap();
        if w.is_empty() {
            return 1.0;
        } // no samples ⇒ nominal
        let met = w.iter().filter(|m| **m).count();
        met as f64 / w.len() as f64
    }
    fn lower_bound(&self) -> Option<f64> {
        Some(self.bound_low)
    }
    /// No upper bound — high meet rate is always good. Setting an
    /// upper bound here (e.g. 1.0) would spuriously flag perfect
    /// performance as NearEdge.
    fn upper_bound(&self) -> Option<f64> {
        None
    }
}

// =======================================================================
// 2. WorkingSetFit
// =======================================================================

/// Ratio of working-set bytes to a target cache size (e.g. L3).
/// `update(bytes)` per tick or per allocation; current_value =
/// bytes / cache_bytes.
pub struct WorkingSetFit {
    name: String,
    current_bytes: AtomicUsize,
    cache_bytes: usize,
    bound_high: f64,
}

impl WorkingSetFit {
    /// `cache_bytes`: target architecture cache (e.g. 32 MiB for L3).
    /// `bound_high`: max fraction allowed (e.g. 0.90).
    pub fn new(name: impl Into<String>, cache_bytes: usize, bound_high: f64) -> Self {
        Self {
            name: name.into(),
            current_bytes: AtomicUsize::new(0),
            cache_bytes,
            bound_high,
        }
    }
    pub fn update(&self, bytes: usize) {
        self.current_bytes.store(bytes, Ordering::Relaxed);
    }
    pub fn current_bytes(&self) -> usize {
        self.current_bytes.load(Ordering::Relaxed)
    }
}

impl EssentialVariable for WorkingSetFit {
    fn name(&self) -> &str {
        &self.name
    }
    fn current_value(&self) -> f64 {
        self.current_bytes.load(Ordering::Relaxed) as f64 / self.cache_bytes as f64
    }
    /// No lower bound — empty working set is fine, no issue.
    fn lower_bound(&self) -> Option<f64> {
        None
    }
    fn upper_bound(&self) -> Option<f64> {
        Some(self.bound_high)
    }
    /// Near-edge zone just below the upper bound: 10% of bound.
    fn near_edge_margin(&self) -> f64 {
        0.1 * self.bound_high
    }
}

// =======================================================================
// 3. GammaEpochCoherence
// =======================================================================

/// Detects retrograde-epoch observations. `observe(epoch)` per
/// dispatch; any read where the new value is less than the last
/// seen is a coherence violation (implies memory-ordering bug).
/// Current value = retrograde-read count (must be 0).
pub struct GammaEpochCoherence {
    name: String,
    last_seen: AtomicU64,
    retrograde_reads: AtomicU64,
}

impl GammaEpochCoherence {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            last_seen: AtomicU64::new(0),
            retrograde_reads: AtomicU64::new(0),
        }
    }
    pub fn observe(&self, epoch: u64) {
        // Compare-and-swap loop: if epoch ≥ last_seen, update; else
        // count a retrograde read.
        let mut last = self.last_seen.load(Ordering::Acquire);
        loop {
            if epoch < last {
                self.retrograde_reads.fetch_add(1, Ordering::Relaxed);
                return;
            }
            match self.last_seen.compare_exchange_weak(
                last,
                epoch,
                Ordering::Release,
                Ordering::Acquire,
            ) {
                Ok(_) => return,
                Err(prev) => last = prev,
            }
        }
    }
    pub fn retrograde_count(&self) -> u64 {
        self.retrograde_reads.load(Ordering::Relaxed)
    }
}

impl EssentialVariable for GammaEpochCoherence {
    fn name(&self) -> &str {
        &self.name
    }
    fn current_value(&self) -> f64 {
        self.retrograde_reads.load(Ordering::Relaxed) as f64
    }
    /// No lower bound — zero is ideal.
    fn lower_bound(&self) -> Option<f64> {
        None
    }
    /// Any nonzero count is a breach. `0.5` upper bound + integer
    /// counts means count ≥ 1 → Breach. No near-edge zone (default 0).
    fn upper_bound(&self) -> Option<f64> {
        Some(0.5)
    }
}

// =======================================================================
// 4. DriveStarvation
// =======================================================================

/// Longest gap (in tick units) since any drive fired. `record_fire`
/// per drive fire; `advance_tick` per L2 tick. Current value = max
/// (current_tick - last_fire) across all known drives.
pub struct DriveStarvation {
    name: String,
    current_tick: AtomicU64,
    /// Drive ID → tick number of last fire.
    /// Mutex-guarded HashMap; access is O(drives) per query, which
    /// for the substrate's typical drive count (<100) is trivial.
    last_fire: Mutex<HashMap<u64, u64>>,
    /// Maximum tolerated starvation in ticks before breach.
    max_starvation_ticks: u64,
}

impl DriveStarvation {
    pub fn new(name: impl Into<String>, max_starvation_ticks: u64) -> Self {
        Self {
            name: name.into(),
            current_tick: AtomicU64::new(0),
            last_fire: Mutex::new(HashMap::new()),
            max_starvation_ticks,
        }
    }
    /// Increment the current-tick counter. Call once per L2 tick.
    pub fn advance_tick(&self) -> u64 {
        self.current_tick.fetch_add(1, Ordering::AcqRel) + 1
    }
    /// Record that drive `id` fired this tick.
    pub fn record_fire(&self, id: u64) {
        let t = self.current_tick.load(Ordering::Acquire);
        self.last_fire.lock().unwrap().insert(id, t);
    }
    /// Longest starvation observed across all tracked drives.
    pub fn longest_starvation(&self) -> u64 {
        let t = self.current_tick.load(Ordering::Acquire);
        let map = self.last_fire.lock().unwrap();
        if map.is_empty() {
            return 0;
        }
        map.values()
            .map(|last| t.saturating_sub(*last))
            .max()
            .unwrap_or(0)
    }
}

impl EssentialVariable for DriveStarvation {
    fn name(&self) -> &str {
        &self.name
    }
    fn current_value(&self) -> f64 {
        self.longest_starvation() as f64
    }
    /// No lower bound — zero starvation is ideal.
    fn lower_bound(&self) -> Option<f64> {
        None
    }
    fn upper_bound(&self) -> Option<f64> {
        Some(self.max_starvation_ticks as f64)
    }
    /// Near-edge zone just below the max: 10% of max.
    fn near_edge_margin(&self) -> f64 {
        0.1 * self.max_starvation_ticks as f64
    }
}

// =======================================================================
// EssentialVariableMonitor
// =======================================================================

/// Per-variable status snapshot. Returned by `tick`.
#[derive(Debug, Clone)]
pub struct VariableSnapshot {
    pub name: String,
    pub value: f64,
    pub status: ViabilityStatus,
}

/// Aggregates the four essential variables (or any
/// `EssentialVariable` impl) + monitors them per tick. Realises the
/// `essential_variables_must_be_monitored_every_tick` Mt rule via
/// the `tick` API.
///
/// Variables are stored as `Arc<dyn EssentialVariable>` so the
/// substrate's mutator paths can keep their own handles to push
/// updates (e.g. the dispatcher can hold an `Arc<DeadlineMeetRate>`
/// and call `record` on it, while the monitor reads through its
/// own clone).
pub struct EssentialVariableMonitor {
    variables: Vec<Arc<dyn EssentialVariable>>,
    near_edge_margin: f64,
    last_status: Mutex<HashMap<String, ViabilityStatus>>,
}

impl Default for EssentialVariableMonitor {
    fn default() -> Self {
        Self::new(0.1)
    }
}

impl EssentialVariableMonitor {
    /// `near_edge_margin` is the fraction of the envelope that
    /// counts as "near edge" (typical 0.05-0.1).
    pub fn new(near_edge_margin: f64) -> Self {
        Self {
            variables: Vec::new(),
            near_edge_margin,
            last_status: Mutex::new(HashMap::new()),
        }
    }
    pub fn add(&mut self, var: Arc<dyn EssentialVariable>) {
        self.variables.push(var);
    }
    /// Sample every variable. Returns a snapshot vector. Does NOT
    /// fire degraded-mode callbacks — use `tick_with_response` for
    /// that.
    pub fn tick(&self) -> Vec<VariableSnapshot> {
        self.variables
            .iter()
            .map(|v| VariableSnapshot {
                name: v.name().to_string(),
                value: v.current_value(),
                status: v.status(),
            })
            .collect()
    }
    /// Sample every variable + fire `responder` callbacks on status
    /// transitions. Realises the
    /// `viability_envelope_breach_triggers_degraded_mode` Mt rule.
    pub fn tick_with_response<R: DegradedModeResponder>(
        &self,
        responder: &mut R,
    ) -> Vec<VariableSnapshot> {
        let snapshots = self.tick();
        let mut last_state = self.last_status.lock().unwrap();
        for snap in &snapshots {
            let old = last_state
                .get(&snap.name)
                .copied()
                .unwrap_or(ViabilityStatus::Nominal);
            let new = snap.status;
            if old != new {
                match new {
                    ViabilityStatus::Breach => responder.on_breach(&snap.name, snap.value),
                    ViabilityStatus::NearEdge => responder.on_near_edge(&snap.name, snap.value),
                    ViabilityStatus::Nominal => responder.on_recovery(&snap.name, snap.value),
                }
                last_state.insert(snap.name.clone(), new);
            }
        }
        snapshots
    }
    /// True iff any variable is currently in `Breach`.
    pub fn any_breach(&self) -> bool {
        self.variables
            .iter()
            .any(|v| v.status() == ViabilityStatus::Breach)
    }
    /// True iff any variable is `NearEdge` or `Breach`.
    pub fn any_outside_nominal(&self) -> bool {
        self.variables
            .iter()
            .any(|v| v.status() != ViabilityStatus::Nominal)
    }
    pub fn len(&self) -> usize {
        self.variables.len()
    }
    pub fn is_empty(&self) -> bool {
        self.variables.is_empty()
    }
}

// =======================================================================
// DegradedModeResponder
// =======================================================================

/// Caller-supplied callback for handling viability transitions.
/// The substrate's coordination layer implements this to act on
/// breach (reduce drives, increase coordination tick rate, etc.)
/// and on recovery (restore nominal operation).
pub trait DegradedModeResponder {
    fn on_near_edge(&mut self, variable: &str, value: f64);
    fn on_breach(&mut self, variable: &str, value: f64);
    fn on_recovery(&mut self, variable: &str, value: f64);
}

#[cfg(test)]
mod tests {
    use super::*;

    // ---------- DeadlineMeetRate ----------

    #[test]
    fn deadline_meet_rate_empty_is_one() {
        let v = DeadlineMeetRate::new("dmr", 10, 0.95);
        assert_eq!(v.current_value(), 1.0);
        assert_eq!(v.status(), ViabilityStatus::Nominal);
    }

    #[test]
    fn deadline_meet_rate_window_slides() {
        let v = DeadlineMeetRate::new("dmr", 5, 0.95);
        for _ in 0..5 {
            v.record(true);
        }
        assert_eq!(v.current_value(), 1.0);
        v.record(false);
        // Window now [true, true, true, true, false].
        // Met = 4, rate = 0.8.
        assert!((v.current_value() - 0.8).abs() < 1e-9);
    }

    #[test]
    fn deadline_meet_rate_breach_below_bound() {
        let v = DeadlineMeetRate::new("dmr", 10, 0.95);
        for i in 0..10 {
            v.record(i < 5); // 5 met, 5 missed → rate 0.5
        }
        assert_eq!(v.status(), ViabilityStatus::Breach);
    }

    // ---------- WorkingSetFit ----------

    #[test]
    fn working_set_fit_ratio() {
        let v = WorkingSetFit::new("wsf", 1000, 0.9);
        assert_eq!(v.current_value(), 0.0);
        v.update(500);
        assert!((v.current_value() - 0.5).abs() < 1e-9);
        v.update(950);
        assert!((v.current_value() - 0.95).abs() < 1e-9);
        // 95% > 90% bound → breach.
        assert_eq!(v.status(), ViabilityStatus::Breach);
    }

    #[test]
    fn working_set_fit_near_edge() {
        let v = WorkingSetFit::new("wsf", 1000, 0.9);
        v.update(870); // 87% — within 5% of 90% bound
        assert_eq!(
            v.status(), // 5% × 0.9 ≈ 0.045
            ViabilityStatus::NearEdge
        );
    }

    // ---------- GammaEpochCoherence ----------

    #[test]
    fn gamma_epoch_coherence_monotonic_is_clean() {
        let v = GammaEpochCoherence::new("gec");
        for i in 0..100 {
            v.observe(i);
        }
        assert_eq!(v.retrograde_count(), 0);
        assert_eq!(v.status(), ViabilityStatus::Nominal);
    }

    #[test]
    fn gamma_epoch_coherence_retrograde_breach() {
        let v = GammaEpochCoherence::new("gec");
        v.observe(10);
        v.observe(20);
        v.observe(5); // retrograde!
        assert_eq!(v.retrograde_count(), 1);
        assert_eq!(v.status(), ViabilityStatus::Breach);
    }

    // ---------- DriveStarvation ----------

    #[test]
    fn drive_starvation_no_drives_is_zero() {
        let v = DriveStarvation::new("ds", 10);
        assert_eq!(v.current_value(), 0.0);
    }

    #[test]
    fn drive_starvation_tracks_longest_gap() {
        let v = DriveStarvation::new("ds", 10);
        v.record_fire(1);
        v.record_fire(2);
        for _ in 0..3 {
            v.advance_tick();
        }
        v.record_fire(1); // drive 1 fired again at tick 3
                          // Drive 2 last fired at tick 0; current tick = 3.
                          // Drive 1 last fired at tick 3; current tick = 3.
        for _ in 0..5 {
            v.advance_tick();
        }
        // Now current = 8. Drive 2: 8 - 0 = 8. Drive 1: 8 - 3 = 5.
        assert_eq!(v.longest_starvation(), 8);
    }

    #[test]
    fn drive_starvation_breach_when_exceeded() {
        let v = DriveStarvation::new("ds", 5);
        v.record_fire(1);
        for _ in 0..7 {
            v.advance_tick();
        } // gap of 7 > bound 5
        assert_eq!(v.status(), ViabilityStatus::Breach);
    }

    // ---------- Monitor aggregate ----------

    #[test]
    fn monitor_tick_returns_all_snapshots() {
        let mut mon = EssentialVariableMonitor::new(0.1);
        mon.add(Arc::new(DeadlineMeetRate::new("dmr", 10, 0.95)));
        mon.add(Arc::new(WorkingSetFit::new("wsf", 1000, 0.9)));
        let snaps = mon.tick();
        assert_eq!(snaps.len(), 2);
        assert!(snaps.iter().any(|s| s.name == "dmr"));
        assert!(snaps.iter().any(|s| s.name == "wsf"));
        // Both nominal at startup.
        for s in &snaps {
            assert_eq!(s.status, ViabilityStatus::Nominal);
        }
        assert!(!mon.any_breach());
        assert!(!mon.any_outside_nominal());
    }

    /// `viability_envelope_breach_triggers_degraded_mode` (Mt rule)
    /// realised end-to-end through the responder callback.
    #[test]
    fn monitor_responder_fires_on_breach_transition() {
        struct CountingResponder {
            breaches: Vec<(String, f64)>,
            recoveries: Vec<(String, f64)>,
            near_edges: Vec<(String, f64)>,
        }
        impl DegradedModeResponder for CountingResponder {
            fn on_breach(&mut self, v: &str, x: f64) {
                self.breaches.push((v.to_string(), x));
            }
            fn on_recovery(&mut self, v: &str, x: f64) {
                self.recoveries.push((v.to_string(), x));
            }
            fn on_near_edge(&mut self, v: &str, x: f64) {
                self.near_edges.push((v.to_string(), x));
            }
        }
        let mut mon = EssentialVariableMonitor::new(0.05);
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        mon.add(Arc::clone(&wsf) as Arc<dyn EssentialVariable>);
        let mut r = CountingResponder {
            breaches: Vec::new(),
            recoveries: Vec::new(),
            near_edges: Vec::new(),
        };
        // Tick 1: nominal. No callbacks (status didn't change from
        // initial Nominal).
        mon.tick_with_response(&mut r);
        assert!(r.breaches.is_empty());
        assert!(r.recoveries.is_empty());

        // Push into breach by updating bytes through our retained
        // Arc handle. This is the realistic pattern: the mutator
        // (e.g. dispatcher) holds an Arc + the monitor holds its own.
        wsf.update(950); // 95% > 90% bound
        mon.tick_with_response(&mut r);
        assert_eq!(r.breaches.len(), 1);
        assert_eq!(r.breaches[0].0, "wsf");

        // Push back to nominal.
        wsf.update(500); // 50%
        mon.tick_with_response(&mut r);
        assert_eq!(r.recoveries.len(), 1);
        assert_eq!(r.recoveries[0].0, "wsf");
    }

    /// `essential_variables_must_be_monitored_every_tick` (Mt rule)
    /// realised by `tick` calling every variable's status in one
    /// pass. Verifies no variable is skipped.
    #[test]
    fn monitor_tick_samples_every_variable() {
        let mut mon = EssentialVariableMonitor::new(0.1);
        let names = ["a", "b", "c", "d"];
        for n in &names {
            mon.add(Arc::new(DeadlineMeetRate::new(*n, 5, 0.5)));
        }
        let snaps = mon.tick();
        for n in &names {
            assert!(
                snaps.iter().any(|s| s.name == *n),
                "variable {} should be in snapshots",
                n
            );
        }
    }

    /// All four essential variables can coexist in one monitor.
    /// The substrate's L6 coordination layer would construct this
    /// at startup + tick it every coordination cycle.
    #[test]
    fn monitor_holds_all_four_essential_variables() {
        let mut mon = EssentialVariableMonitor::new(0.1);
        mon.add(Arc::new(DeadlineMeetRate::new(
            "deadline_meet_rate",
            100,
            0.95,
        )));
        mon.add(Arc::new(WorkingSetFit::new(
            "working_set_fit",
            32 * 1024 * 1024,
            0.9,
        )));
        mon.add(Arc::new(GammaEpochCoherence::new("gamma_epoch_coherence")));
        mon.add(Arc::new(DriveStarvation::new("drive_starvation", 50)));
        assert_eq!(mon.len(), 4);
        let snaps = mon.tick();
        assert_eq!(snaps.len(), 4);
        // All nominal at startup.
        assert!(!mon.any_breach());
    }
}
