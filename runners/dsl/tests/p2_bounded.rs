use substrate_rs::p2_bounded::*;

fn prediction(id: &str, cost: u32) -> CounterfactualPrediction {
    CounterfactualPrediction {
        action_id: id.into(),
        source_belief_digest: "sha256:x".into(),
        transition_witness_digests: vec!["sha256:w".into()],
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
fn finite_bounds_and_all_actions_are_enforced() {
    let bounds = P2Bounds {
        horizon: 1,
        branching: 1,
        action_count: 2,
        nodes_per_action: 8,
    };
    let legal = vec!["x".into(), "y".into()];
    let result = select_all_actions(
        &bounds,
        &legal,
        &[prediction("x", 1), prediction("y", 2)],
        1,
        2,
    );
    assert_eq!(result.minimal, vec!["x".to_string()]);
}
#[test]
fn unresolved_or_low_confidence_never_becomes_feasible() {
    let bounds = P2Bounds {
        horizon: 1,
        branching: 1,
        action_count: 1,
        nodes_per_action: 8,
    };
    let legal = vec!["x".into()];
    let mut p = prediction("x", 1);
    p.manifold_resolved = false;
    assert_eq!(
        select_all_actions(&bounds, &legal, &[p], 1, 1).terminal,
        P2Terminal::Unestablished
    );
}

#[test]
fn objective_uses_graph_goal_probability_not_declared_confidence() {
    let bounds = P2Bounds {
        horizon: 1,
        branching: 1,
        action_count: 2,
        nodes_per_action: 8,
    };
    let mut high_confidence_low_goal = prediction("x", 1);
    high_confidence_low_goal.confidence_bp = 9_000;
    high_confidence_low_goal.uncertainty_bp = 1_000;
    high_confidence_low_goal.goal_probability_bp = 7_500;
    let mut lower_confidence_high_goal = prediction("y", 1);
    lower_confidence_high_goal.confidence_bp = 8_000;
    lower_confidence_high_goal.uncertainty_bp = 2_000;
    lower_confidence_high_goal.goal_probability_bp = 9_000;
    assert_eq!(
        select_all_actions(
            &bounds,
            &["x".into(), "y".into()],
            &[high_confidence_low_goal, lower_confidence_high_goal],
            1,
            1
        )
        .native_tie_set,
        vec!["y"]
    );
}
