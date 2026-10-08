//! P2-B1 native bounded world-model planning contract.
//!
//! This is deliberately a finite, local decision kernel.  It turns
//! action-conditioned native graph evidence into an auditable all-actions
//! prediction set and a lexicographic tie set; it does not grant actions,
//! access host authority, or interpret opaque identifiers as rankings.

use std::collections::BTreeSet;

pub const P2_MAX_ACTIONS: usize = 4;
pub const P2_MAX_NODES: usize = 8;
pub const P2_HORIZON: u8 = 1;
pub const P2_BRANCHING: u8 = 1;
pub const P2_MAX_NODES_PER_ACTION: usize = P2_MAX_NODES;
pub const P2_CONFIDENCE_THRESHOLD_BP: u16 = 7_500;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum P2Terminal {
    Predicted,
    Unestablished,
    Infeasible,
    BudgetExhausted,
    ProtocolError,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct P2Bounds {
    pub horizon: u8,
    pub branching: u8,
    pub action_count: usize,
    pub nodes_per_action: usize,
}
impl P2Bounds {
    pub fn validate(&self) -> Result<(), P2Terminal> {
        if self.horizon != P2_HORIZON
            || self.branching != P2_BRANCHING
            || self.action_count == 0
            || self.action_count > P2_MAX_ACTIONS
            || self.nodes_per_action == 0
            || self.nodes_per_action > P2_MAX_NODES_PER_ACTION
        {
            return Err(P2Terminal::BudgetExhausted);
        }
        Ok(())
    }
}

/// Fresh graph-local state-estimation and planning records.  They are kept
/// separate from evaluator authority and mirror the seed's node vocabulary:
/// observers become beliefs; legal actions become one-step requests; imagined
/// successor state retains source epoch/provenance and cannot be observed.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorldModelObservation {
    pub epoch: u64,
    pub public_atoms: Vec<String>,
    pub confidence_bp: u16,
    pub uncertainty_bp: u16,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BeliefState {
    pub epoch: u64,
    pub source_observation_digest: String,
    pub provenance: &'static str,
    pub confidence_bp: u16,
    pub uncertainty_bp: u16,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorldModelAction {
    pub action_id: String,
    pub legal: bool,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SimulationRequest {
    pub source_epoch: u64,
    pub horizon: u8,
    pub branching: u8,
    pub action: WorldModelAction,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PredictedBeliefState {
    pub source_epoch: u64,
    pub depth: u8,
    pub provenance: &'static str,
    pub terminal: P2Terminal,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PredictionTrajectory {
    pub request: SimulationRequest,
    pub successor: PredictedBeliefState,
    pub transition_witnesses: Vec<String>,
}

/// Native observation revision is explicit and monotonic: stale observations
/// cannot recreate an older perceived belief, and confidence/uncertainty must
/// remain a basis-point partition.
pub fn revise_belief(
    previous: Option<&BeliefState>,
    observation: &WorldModelObservation,
    observation_digest: String,
) -> Result<BeliefState, P2Terminal> {
    if observation.public_atoms.is_empty()
        || observation.public_atoms.len() > P2_MAX_NODES
        || observation.confidence_bp as u32 + observation.uncertainty_bp as u32 != 10_000
        || previous.map_or(false, |belief| observation.epoch <= belief.epoch)
    {
        return Err(P2Terminal::Unestablished);
    }
    Ok(BeliefState {
        epoch: observation.epoch,
        source_observation_digest: observation_digest,
        provenance: "perceived",
        confidence_bp: observation.confidence_bp,
        uncertainty_bp: observation.uncertainty_bp,
    })
}

/// Construct the one-action imagined transition only for an allowlisted action
/// with a nonempty action-conditioned witness.  A correlated observation has
/// no route through this function and therefore cannot become causal support.
pub fn simulate_one_action(
    bounds: &P2Bounds,
    belief: &BeliefState,
    action: WorldModelAction,
    transition_witnesses: Vec<String>,
) -> Result<PredictionTrajectory, P2Terminal> {
    bounds.validate()?;
    if !action.legal || transition_witnesses.is_empty() || transition_witnesses.len() > P2_MAX_NODES
    {
        return Err(P2Terminal::Unestablished);
    }
    let request = SimulationRequest {
        source_epoch: belief.epoch,
        horizon: P2_HORIZON,
        branching: P2_BRANCHING,
        action,
    };
    let successor = PredictedBeliefState {
        source_epoch: belief.epoch,
        depth: 1,
        provenance: "imagined",
        terminal: P2Terminal::Predicted,
    };
    Ok(PredictionTrajectory {
        request,
        successor,
        transition_witnesses,
    })
}

/// Graph-resident evidence copied into a sealed proposal record. Digests bind
/// the source belief and action-conditioned hypothesis witness, preventing a
/// learned correlation from being promoted without an intervention witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CounterfactualPrediction {
    pub action_id: String,
    pub source_belief_digest: String,
    pub transition_witness_digests: Vec<String>,
    pub trajectory_nodes: usize,
    pub outcome_basis_points: Vec<u16>,
    pub all_goals_predicted: bool,
    pub intervention_cost: u32,
    pub manifold_support: bool,
    pub manifold_resolved: bool,
    pub manifold_loss: u16,
    pub manifold_information_loss: u16,
    /// Native graph-derived probability that every requested goal holds after
    /// this intervention. It is deliberately distinct from confidence.
    pub goal_probability_bp: u16,
    pub confidence_bp: u16,
    pub uncertainty_bp: u16,
    pub terminal: P2Terminal,
}
impl CounterfactualPrediction {
    pub fn validate(&self, outcome_atoms: usize) -> Result<(), P2Terminal> {
        if self.action_id.is_empty()
            || self.source_belief_digest.is_empty()
            || self.transition_witness_digests.is_empty()
            || self.transition_witness_digests.len() > P2_MAX_NODES
            || self.trajectory_nodes == 0
            || self.trajectory_nodes > P2_MAX_NODES_PER_ACTION
            || self.outcome_basis_points.len() != outcome_atoms
            || self
                .outcome_basis_points
                .iter()
                .map(|x| *x as u32)
                .sum::<u32>()
                != 10_000
            || self.goal_probability_bp > 10_000
            || self.confidence_bp as u32 + self.uncertainty_bp as u32 != 10_000
        {
            return Err(P2Terminal::ProtocolError);
        }
        if self.manifold_resolved && !self.manifold_support {
            return Err(P2Terminal::ProtocolError);
        }
        Ok(())
    }
    pub fn feasible(&self) -> bool {
        matches!(self.terminal, P2Terminal::Predicted)
            && self.manifold_support
            && self.manifold_resolved
            && self.manifold_loss == 0
            && self.manifold_information_loss == 0
            && self.confidence_bp >= P2_CONFIDENCE_THRESHOLD_BP
            && self.all_goals_predicted
    }
    pub fn feasible_with_maximum(&self, maximum_intervention: u32) -> bool {
        self.intervention_cost <= maximum_intervention && self.feasible()
    }
    pub fn goal_probability_bp(&self) -> u16 {
        self.goal_probability_bp
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NativeSelection {
    pub feasible: Vec<String>,
    pub minimal: Vec<String>,
    pub native_tie_set: Vec<String>,
    pub terminal: P2Terminal,
}

/// Compute the P2 lexicographic decision family.  Sorting is used only for
/// canonical export; opaque labels never decide membership.  Equal minimum
/// candidates remain a tie set for the evaluator's sealed enactment rank.
pub fn select_all_actions(
    bounds: &P2Bounds,
    legal: &[String],
    predictions: &[CounterfactualPrediction],
    outcome_atoms: usize,
    maximum_intervention: u32,
) -> NativeSelection {
    if bounds.validate().is_err()
        || legal.len() != bounds.action_count
        || legal.len() != predictions.len()
        || legal.iter().collect::<BTreeSet<_>>().len() != legal.len()
    {
        return NativeSelection {
            feasible: vec![],
            minimal: vec![],
            native_tie_set: vec![],
            terminal: P2Terminal::ProtocolError,
        };
    }
    let legal_set: BTreeSet<String> = legal.iter().cloned().collect();
    let mut seen = BTreeSet::new();
    for prediction in predictions {
        if prediction.validate(outcome_atoms).is_err()
            || !legal_set.contains(&prediction.action_id)
            || !seen.insert(&prediction.action_id)
        {
            return NativeSelection {
                feasible: vec![],
                minimal: vec![],
                native_tie_set: vec![],
                terminal: P2Terminal::ProtocolError,
            };
        }
    }
    if seen.len() != legal_set.len() {
        return NativeSelection {
            feasible: vec![],
            minimal: vec![],
            native_tie_set: vec![],
            terminal: P2Terminal::ProtocolError,
        };
    }
    let feasible_refs: Vec<_> = predictions
        .iter()
        .filter(|p| p.feasible_with_maximum(maximum_intervention))
        .collect();
    if feasible_refs.is_empty() {
        return NativeSelection {
            feasible: vec![],
            minimal: vec![],
            native_tie_set: vec![],
            terminal: P2Terminal::Unestablished,
        };
    }
    let min_cost = feasible_refs
        .iter()
        .map(|p| p.intervention_cost)
        .min()
        .unwrap();
    let minimal_refs: Vec<_> = feasible_refs
        .iter()
        .copied()
        .filter(|p| p.intervention_cost == min_cost)
        .collect();
    let max_goal = minimal_refs
        .iter()
        .map(|p| p.goal_probability_bp())
        .max()
        .unwrap();
    let mut feasible: Vec<_> = feasible_refs
        .into_iter()
        .map(|p| p.action_id.clone())
        .collect();
    let mut minimal: Vec<_> = minimal_refs.iter().map(|p| p.action_id.clone()).collect();
    let mut tie: Vec<_> = minimal_refs
        .into_iter()
        .filter(|p| p.goal_probability_bp() == max_goal)
        .map(|p| p.action_id.clone())
        .collect();
    feasible.sort();
    minimal.sort();
    tie.sort();
    NativeSelection {
        feasible,
        minimal,
        native_tie_set: tie,
        terminal: P2Terminal::Predicted,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn p(id: &str, cost: u32) -> CounterfactualPrediction {
        CounterfactualPrediction {
            action_id: id.into(),
            source_belief_digest: "x".into(),
            transition_witness_digests: vec!["w".into()],
            trajectory_nodes: 1,
            outcome_basis_points: vec![10_000],
            all_goals_predicted: true,
            intervention_cost: cost,
            manifold_support: true,
            manifold_resolved: true,
            manifold_loss: 0,
            manifold_information_loss: 0,
            goal_probability_bp: 8_000,
            confidence_bp: 8_000,
            uncertainty_bp: 2_000,
            terminal: P2Terminal::Predicted,
        }
    }
    #[test]
    fn preserves_equal_minima_as_tie() {
        let actions = vec!["opaque_b".into(), "opaque_a".into()];
        let out = select_all_actions(
            &P2Bounds {
                horizon: 1,
                branching: 1,
                action_count: 2,
                nodes_per_action: 8,
            },
            &actions,
            &[p("opaque_b", 1), p("opaque_a", 1)],
            1,
            1,
        );
        assert_eq!(
            out.native_tie_set,
            vec!["opaque_a".to_string(), "opaque_b".to_string()]
        );
    }
    #[test]
    fn fails_closed_for_incomplete_prediction_set() {
        let actions = vec!["a".into(), "b".into()];
        assert_eq!(
            select_all_actions(
                &P2Bounds {
                    horizon: 1,
                    branching: 1,
                    action_count: 2,
                    nodes_per_action: 8
                },
                &actions,
                &[p("a", 1)],
                1,
                1
            )
            .terminal,
            P2Terminal::ProtocolError
        );
    }
    #[test]
    fn maximum_intervention_removes_over_budget_candidates() {
        let actions = vec!["over".into(), "within".into()];
        let selected = select_all_actions(
            &P2Bounds {
                horizon: 1,
                branching: 1,
                action_count: 2,
                nodes_per_action: 8,
            },
            &actions,
            &[p("over", 2), p("within", 1)],
            1,
            1,
        );
        assert_eq!(selected.feasible, vec!["within"]);
        assert_eq!(selected.native_tie_set, vec!["within"]);
        let abstained = select_all_actions(
            &P2Bounds {
                horizon: 1,
                branching: 1,
                action_count: 2,
                nodes_per_action: 8,
            },
            &actions,
            &[p("over", 2), p("within", 1)],
            1,
            0,
        );
        assert_eq!(abstained.terminal, P2Terminal::Unestablished);
        assert!(abstained.feasible.is_empty());
    }
}
