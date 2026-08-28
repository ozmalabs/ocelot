//! L3 ↔ L2 bridge — gain scheduling driven by L2's per-kind hot
//! counters.
//!
//! ## What this realises
//!
//! The `gain_scheduling_per_context` component of the
//! `drives_estimation_control` Mt (commit 1b9a7e0) + the explicit
//! L2 ↔ L3 bridge named in the same Mt's `this_mt_bridges_drives_
//! to_l2_dispatch` meta concept:
//!
//! > "L2's hot counters provide context observations; L3's gain
//! >  scheduler uses those observations to adapt controller gains;
//! >  L3's corrected drives shape what fires next, feeding back
//! >  to L2."
//!
//! The bridge closes the feedback loop. L2 observes (counts fires);
//! L3 acts on the observations (schedules gains); L3's actions
//! affect what L2 observes next (different reflex prioritisation).
//!
//! ## Two scheduler variants
//!
//! - **`TableLookupGainScheduler`** — discrete table keyed on the
//!   dominant kind (highest fire count). Sharp gain transitions
//!   when dominance shifts. Simplest realisation; matches the
//!   Mt's "indexes a precomputed gain table" path.
//!
//! - **`InterpolatingGainScheduler`** — continuous interpolation:
//!   per-kind gains weighted by fire-count share. Smooth gain
//!   transitions; satisfies the implicit "gains continuous in
//!   context" property suggested by control-theory practice.
//!
//! Both implement the `GainScheduler` trait so callers pick at
//! configuration time.

use rustc_hash::FxHashMap;

use crate::l2_adaptive::HotCounter;
use crate::l3_drives::{Controller, PidController};
use crate::sym::Sym;

/// PID gain triple `(Kp, Ki, Kd)`. Returned by schedulers; applied
/// by the controller-extension method below.
pub type PidGains = (f64, f64, f64);

/// A gain scheduler observes L2 dispatcher context (via
/// `HotCounter`) and produces controller gains tuned for the
/// current observation.
pub trait GainScheduler: Send {
    /// Compute appropriate `(Kp, Ki, Kd)` given the current hot
    /// counter state. May mutate internal state (e.g. moving
    /// average accumulators).
    fn gains(&mut self, hot: &HotCounter) -> PidGains;
}

/// Extension methods on `PidController` so applying a scheduled
/// update is one call. Concrete on PidController because the gain
/// shape is PID-specific.
impl PidController {
    /// Replace the controller's gains in-place.
    pub fn set_gains(&mut self, gains: PidGains) {
        self.kp = gains.0;
        self.ki = gains.1;
        self.kd = gains.2;
    }

    /// Apply a scheduler's output: read scheduler.gains(hot),
    /// install on the controller. Idempotent + cheap.
    pub fn apply_scheduled<S: GainScheduler>(&mut self, scheduler: &mut S, hot: &HotCounter) {
        let g = scheduler.gains(hot);
        self.set_gains(g);
    }
}

// =======================================================================
// TableLookupGainScheduler
// =======================================================================

/// Maps Sym → gains. Picks the dominant kind (highest fire count)
/// + looks up its entry; falls back to `default_gains` when:
/// - the table is empty, OR
/// - no kind has fired (snapshot empty), OR
/// - the dominant kind has no table entry.
///
/// Simplest scheduler implementation. Suited to small substrates
/// where each kind has a known gain profile + transitions between
/// dominant kinds are rare.
pub struct TableLookupGainScheduler {
    pub table: FxHashMap<Sym, PidGains>,
    pub default_gains: PidGains,
}

impl TableLookupGainScheduler {
    pub fn new(default_gains: PidGains) -> Self {
        Self {
            table: FxHashMap::default(),
            default_gains,
        }
    }
    pub fn insert(&mut self, kind: Sym, gains: PidGains) -> Option<PidGains> {
        self.table.insert(kind, gains)
    }
}

impl GainScheduler for TableLookupGainScheduler {
    fn gains(&mut self, hot: &HotCounter) -> PidGains {
        let snap = hot.snapshot();
        let dominant: Option<Sym> = snap
            .iter()
            .filter(|(_, c)| *c > 0)
            .max_by_key(|(_, c)| *c)
            .map(|(k, _)| *k);
        dominant
            .and_then(|k| self.table.get(&k).copied())
            .unwrap_or(self.default_gains)
    }
}

// =======================================================================
// InterpolatingGainScheduler
// =======================================================================

/// Each tabled kind contributes its gains weighted by its share of
/// total fire counts. Untabled kinds contribute the default_gains
/// at their share. Produces smooth gain transitions as dominance
/// shifts gradually.
///
/// Suited to substrates with many drives + gradual context drift.
/// Avoids the gain "jumps" of TableLookup when dominance flips
/// across closely-counted kinds.
pub struct InterpolatingGainScheduler {
    pub table: FxHashMap<Sym, PidGains>,
    pub default_gains: PidGains,
}

impl InterpolatingGainScheduler {
    pub fn new(default_gains: PidGains) -> Self {
        Self {
            table: FxHashMap::default(),
            default_gains,
        }
    }
    pub fn insert(&mut self, kind: Sym, gains: PidGains) -> Option<PidGains> {
        self.table.insert(kind, gains)
    }
}

impl GainScheduler for InterpolatingGainScheduler {
    fn gains(&mut self, hot: &HotCounter) -> PidGains {
        let snap = hot.snapshot();
        let total: u64 = snap.iter().map(|(_, c)| *c).sum();
        if total == 0 {
            return self.default_gains;
        }
        let mut kp = 0.0_f64;
        let mut ki = 0.0_f64;
        let mut kd = 0.0_f64;
        for (kind, count) in &snap {
            let share = (*count as f64) / (total as f64);
            let (k_kp, k_ki, k_kd) = self.table.get(kind).copied().unwrap_or(self.default_gains);
            kp += share * k_kp;
            ki += share * k_ki;
            kd += share * k_kd;
        }
        (kp, ki, kd)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sym::Interner;

    fn populate(hot: &HotCounter, kind: Sym, n: u64) {
        for _ in 0..n {
            hot.record(kind);
        }
    }

    // ---------- TableLookupGainScheduler ----------

    #[test]
    fn table_lookup_returns_default_for_empty_hot_counter() {
        let mut sched = TableLookupGainScheduler::new((1.0, 0.5, 0.1));
        let hot = HotCounter::new();
        assert_eq!(sched.gains(&hot), (1.0, 0.5, 0.1));
    }

    #[test]
    fn table_lookup_uses_dominant_kind_entry() {
        let mut i = Interner::new();
        let k_a = i.intern("rule_a");
        let k_b = i.intern("rule_b");
        let mut sched = TableLookupGainScheduler::new((1.0, 0.0, 0.0));
        sched.insert(k_a, (10.0, 1.0, 0.5));
        sched.insert(k_b, (2.0, 0.2, 0.05));
        let hot = HotCounter::new();
        // a dominant.
        populate(&hot, k_a, 100);
        populate(&hot, k_b, 10);
        assert_eq!(sched.gains(&hot), (10.0, 1.0, 0.5));
        // Flip dominance.
        populate(&hot, k_b, 200);
        assert_eq!(sched.gains(&hot), (2.0, 0.2, 0.05));
    }

    #[test]
    fn table_lookup_falls_back_when_dominant_not_in_table() {
        let mut i = Interner::new();
        let k_a = i.intern("rule_a");
        let k_unknown = i.intern("rule_x");
        let mut sched = TableLookupGainScheduler::new((3.0, 0.3, 0.03));
        sched.insert(k_a, (10.0, 1.0, 0.5));
        let hot = HotCounter::new();
        populate(&hot, k_unknown, 50);
        populate(&hot, k_a, 10);
        // Dominant kind (k_unknown) has no entry → default.
        assert_eq!(sched.gains(&hot), (3.0, 0.3, 0.03));
    }

    // ---------- InterpolatingGainScheduler ----------

    #[test]
    fn interpolating_blends_proportional_to_counts() {
        let mut i = Interner::new();
        let k_a = i.intern("rule_a");
        let k_b = i.intern("rule_b");
        let mut sched = InterpolatingGainScheduler::new((0.0, 0.0, 0.0));
        sched.insert(k_a, (10.0, 0.0, 0.0));
        sched.insert(k_b, (2.0, 0.0, 0.0));
        let hot = HotCounter::new();
        // 75/25 split favouring a.
        populate(&hot, k_a, 75);
        populate(&hot, k_b, 25);
        let (kp, ki, kd) = sched.gains(&hot);
        // Expected blend: 0.75 * 10 + 0.25 * 2 = 7.5 + 0.5 = 8.0.
        assert!((kp - 8.0).abs() < 1e-9, "kp blend wrong: {}", kp);
        assert!(ki.abs() < 1e-9);
        assert!(kd.abs() < 1e-9);
    }

    #[test]
    fn interpolating_returns_default_when_no_fires() {
        let mut sched = InterpolatingGainScheduler::new((7.0, 1.0, 0.1));
        let hot = HotCounter::new();
        assert_eq!(sched.gains(&hot), (7.0, 1.0, 0.1));
    }

    #[test]
    fn interpolating_uses_default_for_untabled_kinds() {
        let mut i = Interner::new();
        let k_a = i.intern("rule_a");
        let k_unknown = i.intern("rule_x");
        let mut sched = InterpolatingGainScheduler::new((1.0, 0.0, 0.0));
        sched.insert(k_a, (5.0, 0.0, 0.0));
        let hot = HotCounter::new();
        // Half-and-half between tabled (gains 5.0) and untabled (default 1.0).
        populate(&hot, k_a, 50);
        populate(&hot, k_unknown, 50);
        let (kp, _, _) = sched.gains(&hot);
        // Expected: 0.5 * 5.0 + 0.5 * 1.0 = 3.0.
        assert!(
            (kp - 3.0).abs() < 1e-9,
            "kp blend with default wrong: {}",
            kp
        );
    }

    // ---------- PidController::apply_scheduled ----------

    /// End-to-end the bridge: PID + scheduler + L2 HotCounter.
    /// Verifies the Mt's gain_scheduling_per_context component
    /// works end-to-end through the actual PidController.
    #[test]
    fn pid_apply_scheduled_updates_gains_in_place() {
        let mut i = Interner::new();
        let k = i.intern("hot_kind");
        let mut pid = PidController::new(1.0, 0.5, 0.1);
        let mut sched = TableLookupGainScheduler::new((1.0, 0.5, 0.1));
        sched.insert(k, (20.0, 5.0, 1.0));
        let hot = HotCounter::new();
        populate(&hot, k, 10);
        pid.apply_scheduled(&mut sched, &hot);
        assert_eq!(pid.kp, 20.0);
        assert_eq!(pid.ki, 5.0);
        assert_eq!(pid.kd, 1.0);
    }

    /// The bridge under context shift: PID gains track the L2
    /// dominant kind as it changes. Mirrors what happens at runtime
    /// when the substrate transitions between Mt regimes.
    #[test]
    fn pid_gains_track_context_shift() {
        let mut i = Interner::new();
        let k_calm = i.intern("calm");
        let k_volatile = i.intern("volatile");
        let mut pid = PidController::new(1.0, 0.5, 0.1);
        let mut sched = TableLookupGainScheduler::new((1.0, 0.5, 0.1));
        sched.insert(k_calm, (5.0, 0.5, 0.05)); // smooth
        sched.insert(k_volatile, (1.0, 0.0, 0.5)); // fast-D, no-I

        let hot = HotCounter::new();
        // Phase 1: calm dominant.
        populate(&hot, k_calm, 100);
        pid.apply_scheduled(&mut sched, &hot);
        assert_eq!((pid.kp, pid.ki, pid.kd), (5.0, 0.5, 0.05));

        // Phase 2: volatile takes over.
        populate(&hot, k_volatile, 200);
        pid.apply_scheduled(&mut sched, &hot);
        assert_eq!((pid.kp, pid.ki, pid.kd), (1.0, 0.0, 0.5));
    }
}
