//! L4 subsystem boundary registry + enforcement.
//!
//! Realises the `subsystems_compose_through_named_bridges` invariant +
//! the `cross_subsystem_must_use_named_bridges` rule of the
//! `seven_meta_shape_subsystems` Mt (commit c383b6c). The substrate's
//! 7 functional subsystems (HIERARCHICAL_INVARIANCE_BUILDUP,
//! SELECTIVE_GATING, GLOBAL_MESSAGE_PASSING, PREDICTION_MINUS_OBSERVATION,
//! COMPETITIVE_INHIBITION, DELAYED_PERSISTENCE, FEEDBACK_CONTROL) must
//! interact through named bridges, not implicit coupling.
//!
//! ## What this module provides
//!
//! - `MetaShape` enum — the 7 subsystems Jabberwock's analogical
//!   thinking at n=4 surfaced (commit 47b3370 onwards).
//! - `SubsystemRegistry` — operations registered by name + tagged
//!   with their subsystem.
//! - `NamedBridge` — explicit cross-subsystem channel.
//! - `enforce` — checks an operation against the registry. Unknown
//!   operations or implicit cross-subsystem calls return errors.
//!
//! For v1 the enforcement is advisory: callers opt in by registering
//! their operations + checking via `enforce`. Future revisions might
//! gate operations behind compile-time markers or runtime trampolines.

use std::collections::{HashMap, HashSet};

/// The 7 meta-shape subsystems Jabberwock's analogical_thinking
/// surfaced at n=4 (per the runner-design walk).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum MetaShape {
    /// Primary organising principle (analogy weight 3078).
    HierarchicalInvarianceBuildup,
    /// Attention + admissibility filtering (weight 1194).
    SelectiveGating,
    /// Cross-Mt communication (weight 843).
    GlobalMessagePassing,
    /// Anticipation-correction loop (weight 556).
    PredictionMinusObservation,
    /// Basin separation + winner-take-all (weight 452).
    CompetitiveInhibition,
    /// Consolidation + replay (weight 449).
    DelayedPersistence,
    /// Homeostatic regulation (weight 81).
    FeedbackControl,
}

impl MetaShape {
    /// Analogy weight from the runner-design walk. Resource baseline
    /// allocation can be informed by these (Mt rule
    /// `primary_subsystem_dominates_by_default`).
    pub fn analogy_weight(self) -> u32 {
        match self {
            MetaShape::HierarchicalInvarianceBuildup => 3078,
            MetaShape::SelectiveGating => 1194,
            MetaShape::GlobalMessagePassing => 843,
            MetaShape::PredictionMinusObservation => 556,
            MetaShape::CompetitiveInhibition => 452,
            MetaShape::DelayedPersistence => 449,
            MetaShape::FeedbackControl => 81,
        }
    }
    /// All seven meta-shapes in weight-descending order.
    pub fn all() -> &'static [MetaShape] {
        &[
            MetaShape::HierarchicalInvarianceBuildup,
            MetaShape::SelectiveGating,
            MetaShape::GlobalMessagePassing,
            MetaShape::PredictionMinusObservation,
            MetaShape::CompetitiveInhibition,
            MetaShape::DelayedPersistence,
            MetaShape::FeedbackControl,
        ]
    }
}

/// An operation registered with the subsystem registry.
#[derive(Debug, Clone)]
pub struct RegisteredOperation {
    pub name: String,
    pub subsystem: MetaShape,
}

/// A named bridge between two subsystems. Cross-subsystem operations
/// must use a registered bridge.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct NamedBridge {
    pub name: String,
    pub from: MetaShape,
    pub to: MetaShape,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryViolation {
    /// Operation not in registry.
    UnknownOperation(String),
    /// Cross-subsystem call without a registered bridge.
    MissingBridge { from: MetaShape, to: MetaShape, op: String },
}

/// Registry of operations + their owning subsystems + named bridges
/// for cross-subsystem communication.
#[derive(Debug, Default)]
pub struct SubsystemRegistry {
    operations: HashMap<String, MetaShape>,
    bridges: HashSet<NamedBridge>,
}

impl SubsystemRegistry {
    pub fn new() -> Self {
        Self {
            operations: HashMap::new(),
            bridges: HashSet::new(),
        }
    }

    /// Register an operation in the named subsystem.
    pub fn register(&mut self, op: &str, shape: MetaShape) {
        self.operations.insert(op.to_string(), shape);
    }

    /// Register a named bridge from `from` to `to`.
    pub fn register_bridge(&mut self, name: &str,
                            from: MetaShape, to: MetaShape) {
        self.bridges.insert(NamedBridge {
            name: name.to_string(), from, to,
        });
    }

    pub fn subsystem_of(&self, op: &str) -> Option<MetaShape> {
        self.operations.get(op).copied()
    }

    pub fn has_bridge(&self, from: MetaShape, to: MetaShape) -> bool {
        self.bridges.iter().any(|b| b.from == from && b.to == to)
    }

    /// Verify a call from `caller_op` to `callee_op`. Returns Ok if
    /// (a) same subsystem (in-subsystem calls are always allowed),
    /// or (b) cross-subsystem AND a bridge exists.
    pub fn enforce(&self, caller_op: &str, callee_op: &str)
        -> Result<(), BoundaryViolation>
    {
        let caller_sub = self.subsystem_of(caller_op)
            .ok_or_else(|| BoundaryViolation::UnknownOperation(
                caller_op.to_string()))?;
        let callee_sub = self.subsystem_of(callee_op)
            .ok_or_else(|| BoundaryViolation::UnknownOperation(
                callee_op.to_string()))?;
        if caller_sub == callee_sub { return Ok(()); }
        if self.has_bridge(caller_sub, callee_sub) { return Ok(()); }
        Err(BoundaryViolation::MissingBridge {
            from: caller_sub, to: callee_sub, op: callee_op.to_string(),
        })
    }

    /// Count operations per subsystem. Useful for verifying the
    /// resource-allocation invariant (primary subsystem dominates).
    pub fn ops_per_subsystem(&self) -> HashMap<MetaShape, usize> {
        let mut counts = HashMap::new();
        for shape in self.operations.values() {
            *counts.entry(*shape).or_insert(0) += 1;
        }
        counts
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn analogy_weights_match_runner_design() {
        // From commit 9bf8370 (analogical thinking output).
        assert_eq!(
            MetaShape::HierarchicalInvarianceBuildup.analogy_weight(),
            3078);
        assert_eq!(
            MetaShape::FeedbackControl.analogy_weight(), 81);
    }

    #[test]
    fn all_seven_meta_shapes_present() {
        assert_eq!(MetaShape::all().len(), 7);
    }

    #[test]
    fn in_subsystem_call_always_allowed() {
        let mut r = SubsystemRegistry::new();
        r.register("op_a", MetaShape::SelectiveGating);
        r.register("op_b", MetaShape::SelectiveGating);
        assert!(r.enforce("op_a", "op_b").is_ok());
    }

    #[test]
    fn cross_subsystem_call_needs_bridge() {
        let mut r = SubsystemRegistry::new();
        r.register("dispatch_submit", MetaShape::SelectiveGating);
        r.register("drive_step", MetaShape::FeedbackControl);
        let result = r.enforce("dispatch_submit", "drive_step");
        match result {
            Err(BoundaryViolation::MissingBridge { from, to, op }) => {
                assert_eq!(from, MetaShape::SelectiveGating);
                assert_eq!(to, MetaShape::FeedbackControl);
                assert_eq!(op, "drive_step");
            }
            _ => panic!("expected MissingBridge; got {:?}", result),
        }
    }

    #[test]
    fn cross_subsystem_with_bridge_passes() {
        let mut r = SubsystemRegistry::new();
        r.register("dispatch_submit", MetaShape::SelectiveGating);
        r.register("drive_step", MetaShape::FeedbackControl);
        r.register_bridge("gain_scheduling",
            MetaShape::SelectiveGating,
            MetaShape::FeedbackControl);
        assert!(r.enforce("dispatch_submit", "drive_step").is_ok());
    }

    #[test]
    fn unknown_operation_violates() {
        let r = SubsystemRegistry::new();
        let result = r.enforce("undeclared", "also_undeclared");
        assert!(matches!(result,
            Err(BoundaryViolation::UnknownOperation(_))));
    }

    #[test]
    fn ops_per_subsystem_counts() {
        let mut r = SubsystemRegistry::new();
        r.register("a1", MetaShape::HierarchicalInvarianceBuildup);
        r.register("a2", MetaShape::HierarchicalInvarianceBuildup);
        r.register("a3", MetaShape::HierarchicalInvarianceBuildup);
        r.register("b1", MetaShape::SelectiveGating);
        r.register("c1", MetaShape::FeedbackControl);
        let counts = r.ops_per_subsystem();
        assert_eq!(counts[&MetaShape::HierarchicalInvarianceBuildup], 3);
        assert_eq!(counts[&MetaShape::SelectiveGating], 1);
        assert_eq!(counts[&MetaShape::FeedbackControl], 1);
    }

    /// Substrate's expected subsystem allocation at startup: most
    /// ops in HIERARCHICAL_INVARIANCE_BUILDUP (the primary by 4×
    /// analogy weight), minimum in FEEDBACK_CONTROL.
    /// Mt rule: `primary_subsystem_dominates_by_default`.
    #[test]
    fn primary_subsystem_dominates_baseline_allocation() {
        let mut r = SubsystemRegistry::new();
        // 5 ops in primary, 1 in secondary, etc.
        for i in 0..5 {
            r.register(&format!("hier_{}", i),
                MetaShape::HierarchicalInvarianceBuildup);
        }
        r.register("sel_1", MetaShape::SelectiveGating);
        r.register("fb_1", MetaShape::FeedbackControl);
        let counts = r.ops_per_subsystem();
        let primary = counts[&MetaShape::HierarchicalInvarianceBuildup];
        let feedback = counts[&MetaShape::FeedbackControl];
        // Primary should dominate.
        assert!(primary > feedback * 2,
                "primary should dominate; primary={}, feedback={}",
                primary, feedback);
    }
}
