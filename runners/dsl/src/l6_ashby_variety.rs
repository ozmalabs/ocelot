//! L6 Ashby variety check at system scale.
//!
//! Realises the `ashby_variety_match_at_system_scale` component of
//! the `universal_coordination` Mt (commit c383b6c). Applies Ashby's
//! law of requisite variety at the substrate level:
//!
//! > log V(R) ≥ log V(D) - log V(E)
//!
//! The substrate's total **regulator variety** (sum over per-layer
//! regulators) must equal or exceed the total **disturbance variety**
//! (sum over environment + Γ mutations + workload churn + hardware
//! events). Violation means some failure mode is structurally
//! unregulated — substrate can't react to a class of disturbance
//! because nothing watches for it.
//!
//! ## What this module provides
//!
//! - `AshbyVarietyCheck` — registry of named regulator channels
//!   + named disturbance sources.
//! - `variety_ratio()` — V(R) / V(D).
//! - `variety_match_holds()` — true iff V(R) ≥ V(D).
//! - `unregulated_disturbances()` — disturbances without a regulator
//!   covering them (diagnostic; substrate's L6 layer flags these).
//!
//! ## Mt invariant: `system_scale_variety_match_holds`
//!
//! The substrate's total regulator variety ≥ total disturbance
//! variety. Computed by counting registered channels.

use std::collections::HashSet;

/// Ashby variety counter. Tracks which substrate-level regulators
/// (channels that can act) exist + which disturbance sources (things
/// that can change) the substrate observes.
///
/// For v1 we count by name; future revisions might weight regulators
/// by their action variety + disturbances by their state space.
#[derive(Debug, Default)]
pub struct AshbyVarietyCheck {
    regulators: HashSet<String>,
    disturbances: HashSet<String>,
    /// Optional coverage map: which regulator covers which disturbance.
    /// Used to compute `unregulated_disturbances`.
    coverage: Vec<(String, String)>,
}

impl AshbyVarietyCheck {
    pub fn new() -> Self {
        Self {
            regulators: HashSet::new(),
            disturbances: HashSet::new(),
            coverage: Vec::new(),
        }
    }

    /// Register a regulator channel by name (e.g. "L2_dispatch",
    /// "L3_pid_corrector", "L6_cybernetic_feedback").
    pub fn register_regulator(&mut self, name: &str) {
        self.regulators.insert(name.to_string());
    }

    /// Register a disturbance source by name (e.g. "gamma_mutations",
    /// "workload_churn", "hardware_interrupt", "missed_deadlines").
    pub fn register_disturbance(&mut self, name: &str) {
        self.disturbances.insert(name.to_string());
    }

    /// Declare that `regulator` covers `disturbance`. Used for the
    /// `unregulated_disturbances` diagnostic.
    pub fn register_coverage(&mut self, regulator: &str, disturbance: &str) {
        self.coverage.push((regulator.to_string(), disturbance.to_string()));
    }

    pub fn regulator_variety(&self) -> usize { self.regulators.len() }
    pub fn disturbance_variety(&self) -> usize { self.disturbances.len() }

    /// V(R) / V(D). When V(D) == 0, returns infinity (no disturbances
    /// → regulator-variety-match trivially holds).
    pub fn variety_ratio(&self) -> f64 {
        let d = self.disturbances.len();
        if d == 0 { return f64::INFINITY; }
        self.regulators.len() as f64 / d as f64
    }

    /// Ashby's law: V(R) ≥ V(D). True iff the substrate has at least
    /// as many regulator channels as disturbance sources.
    ///
    /// This is a NECESSARY condition for substrate viability; not
    /// sufficient. Even with V(R) ≥ V(D), regulators must actually
    /// COVER the right disturbances (see `unregulated_disturbances`).
    pub fn variety_match_holds(&self) -> bool {
        self.regulators.len() >= self.disturbances.len()
    }

    /// Disturbances with no registered covering regulator. The
    /// substrate's L6 layer flags these as structurally unregulated
    /// — there exists no path from observation to correction for
    /// these disturbance classes.
    pub fn unregulated_disturbances(&self) -> Vec<String> {
        let covered: HashSet<&str> = self.coverage.iter()
            .map(|(_, d)| d.as_str()).collect();
        self.disturbances.iter()
            .filter(|d| !covered.contains(d.as_str()))
            .cloned()
            .collect()
    }

    /// Regulators that aren't declared to cover any disturbance.
    /// May indicate dead code or misregistration.
    pub fn idle_regulators(&self) -> Vec<String> {
        let active: HashSet<&str> = self.coverage.iter()
            .map(|(r, _)| r.as_str()).collect();
        self.regulators.iter()
            .filter(|r| !active.contains(r.as_str()))
            .cloned()
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_check_has_trivial_match() {
        let c = AshbyVarietyCheck::new();
        // V(R)=0, V(D)=0 → match trivially holds.
        assert!(c.variety_match_holds());
        assert_eq!(c.variety_ratio(), f64::INFINITY);
    }

    #[test]
    fn variety_ratio_correct() {
        let mut c = AshbyVarietyCheck::new();
        c.register_regulator("r1");
        c.register_regulator("r2");
        c.register_regulator("r3");
        c.register_disturbance("d1");
        c.register_disturbance("d2");
        // 3 / 2 = 1.5
        assert!((c.variety_ratio() - 1.5).abs() < 1e-12);
        assert!(c.variety_match_holds());
    }

    #[test]
    fn variety_match_fails_when_under_regulated() {
        let mut c = AshbyVarietyCheck::new();
        c.register_regulator("r1");
        c.register_disturbance("d1");
        c.register_disturbance("d2");
        c.register_disturbance("d3");
        // 1 < 3 → fails
        assert!(!c.variety_match_holds());
        assert!((c.variety_ratio() - (1.0 / 3.0)).abs() < 1e-12);
    }

    #[test]
    fn unregulated_disturbances_finds_uncovered() {
        let mut c = AshbyVarietyCheck::new();
        c.register_regulator("dispatcher");
        c.register_regulator("drives");
        c.register_disturbance("gamma_mutations");
        c.register_disturbance("workload_churn");
        c.register_disturbance("hardware_interrupts");
        c.register_coverage("dispatcher", "gamma_mutations");
        c.register_coverage("dispatcher", "workload_churn");
        // hardware_interrupts not covered.
        let uncovered = c.unregulated_disturbances();
        assert_eq!(uncovered.len(), 1);
        assert_eq!(uncovered[0], "hardware_interrupts");
    }

    #[test]
    fn idle_regulators_finds_dead_code() {
        let mut c = AshbyVarietyCheck::new();
        c.register_regulator("dispatcher");
        c.register_regulator("unused");
        c.register_disturbance("d1");
        c.register_coverage("dispatcher", "d1");
        let idle = c.idle_regulators();
        assert_eq!(idle.len(), 1);
        assert_eq!(idle[0], "unused");
    }

    /// Realistic substrate setup: 4 regulators (the L2/L3/L5/L6
    /// layers) + 4 disturbance sources (essential variables). Each
    /// regulator covers one disturbance. Variety match holds.
    #[test]
    fn realistic_substrate_variety_holds() {
        let mut c = AshbyVarietyCheck::new();
        for r in ["L2_dispatch", "L3_drives", "L5_codegen", "L6_feedback"] {
            c.register_regulator(r);
        }
        for d in ["deadline_meet_rate", "working_set_fit",
                   "gamma_epoch_coherence", "drive_starvation"] {
            c.register_disturbance(d);
        }
        c.register_coverage("L2_dispatch", "deadline_meet_rate");
        c.register_coverage("L5_codegen",  "working_set_fit");
        c.register_coverage("L2_dispatch", "gamma_epoch_coherence");
        c.register_coverage("L3_drives",   "drive_starvation");
        assert!(c.variety_match_holds());
        assert!(c.unregulated_disturbances().is_empty());
        // L6_feedback isn't declared to cover anything — it's the
        // meta-regulator. Flagged as idle by this diagnostic but
        // that's correct (it operates by ROUTING signals, not by
        // covering a specific disturbance).
        assert_eq!(c.idle_regulators(), vec!["L6_feedback"]);
    }
}
