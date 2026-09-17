use rustc_hash::FxHashMap;
use std::sync::Arc;
use substrate_rs::{
    graph::{NodeID, TypedGraph},
    p4_readiness::{advance_p4_r0, P4Decision, P4ObservationStatus, P4R0Limits, SealedObservation},
    sym::Interner,
    value::Value,
};

fn digest(c: char) -> String {
    format!("sha256:{}", c.to_string().repeat(64))
}

fn matrix(rows: &[f64]) -> Value {
    Value::Tuple(Arc::new(
        rows.iter()
            .map(|x| Value::Tuple(Arc::new(vec![Value::Float(*x)].into())))
            .collect::<Vec<_>>()
            .into(),
    ))
}

fn setup() -> (TypedGraph, Interner, NodeID, NodeID, NodeID) {
    let mut graph = TypedGraph::new();
    let mut interner = Interner::new();
    let ty = interner.intern("N");
    let episode = graph.insert_node(ty, FxHashMap::default());
    let policy = graph.insert_node(ty, FxHashMap::default());
    let candidate = graph.insert_node(ty, FxHashMap::default());
    graph.set_node_attr(
        episode,
        interner.intern("future_manifold_target"),
        matrix(&[0., 0., 0.]),
    );
    graph.set_node_attr(
        episode,
        interner.intern("future_manifold_bounds"),
        matrix(&[1., 1., 1.]),
    );
    graph.set_node_attr(
        policy,
        interner.intern("future_manifold_projection_budget"),
        Value::Int(3),
    );
    graph.set_node_attr(
        policy,
        interner.intern("future_manifold_physical_horizon"),
        Value::Int(3),
    );
    graph.set_node_attr(
        candidate,
        interner.intern("future_manifold_values"),
        matrix(&[0., 0., 0.]),
    );
    graph.set_node_attr(candidate, interner.intern("intervention"), Value::Int(1));
    (graph, interner, episode, policy, candidate)
}

fn observation(
    time: u64,
    status: P4ObservationStatus,
    episode: NodeID,
    policy: NodeID,
    candidate: NodeID,
    parent: Option<String>,
    proposal: Option<String>,
) -> SealedObservation {
    let observation = SealedObservation::new(
        time,
        parent,
        status,
        vec!["signal".into()],
        vec![candidate],
        Some(episode),
        Some(policy),
        "run".into(),
        time,
        Some(digest('1')),
        proposal.clone(),
    );
    match proposal {
        Some(_) => observation.with_action_reservation_digest(digest('9')),
        None => observation,
    }
}

fn action_trace(
    graph: &mut TypedGraph,
    interner: &mut Interner,
    episode: NodeID,
    policy: NodeID,
    candidate: NodeID,
) {
    let replan = digest('2');
    assert!(matches!(
        advance_p4_r0(
            graph,
            interner,
            observation(
                1,
                P4ObservationStatus::Initial,
                episode,
                policy,
                candidate,
                None,
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::ProposeIntervention { .. }
    ));
    assert!(matches!(
        advance_p4_r0(
            graph,
            interner,
            observation(
                2,
                P4ObservationStatus::SealedInterventionOutcome,
                episode,
                policy,
                candidate,
                Some(replan.clone()),
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::Replan { .. }
    ));
    assert!(matches!(
        advance_p4_r0(
            graph,
            interner,
            observation(
                3,
                P4ObservationStatus::Initial,
                episode,
                policy,
                candidate,
                Some(replan),
                Some(digest('3'))
            ),
            P4R0Limits::default()
        ),
        P4Decision::ProposeAction { .. }
    ));
}

#[test]
fn native_decision_trace_has_causal_chain() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    let decision = advance_p4_r0(
        &mut graph,
        &mut interner,
        observation(
            1,
            P4ObservationStatus::Initial,
            episode,
            policy,
            candidate,
            None,
            None,
        ),
        P4R0Limits::default(),
    );
    assert!(matches!(decision, P4Decision::ProposeIntervention { .. }));
    assert_eq!(
        graph
            .nodes_of_type(interner.intern("GraphActionProposalV1"))
            .len(),
        1
    );
    assert_eq!(graph.nodes_of_type(interner.intern("PlanNode")).len(), 1);
}

#[test]
fn intervention_precedes_rule_dependent_action_and_exactly_one_replan() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    action_trace(&mut graph, &mut interner, episode, policy, candidate);
    assert_eq!(graph.nodes_of_type(interner.intern("Replan")).len(), 1);
}

#[test]
fn action_proposal_requires_a_reservation_digest() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    let replan = digest('2');
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                1,
                P4ObservationStatus::Initial,
                episode,
                policy,
                candidate,
                None,
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::ProposeIntervention { .. }
    ));
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                2,
                P4ObservationStatus::SealedInterventionOutcome,
                episode,
                policy,
                candidate,
                Some(replan.clone()),
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::Replan { .. }
    ));
    let missing_reservation = SealedObservation::new(
        3,
        Some(replan),
        P4ObservationStatus::Initial,
        vec!["signal".into()],
        vec![candidate],
        Some(episode),
        Some(policy),
        "run".into(),
        3,
        Some(digest('1')),
        Some(digest('3')),
    );
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            missing_reservation,
            P4R0Limits::default()
        ),
        P4Decision::Impasse {
            reason: "replan_receipt_required"
        }
    ));
}

#[test]
fn action_reservation_persists_the_native_binding() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    action_trace(&mut graph, &mut interner, episode, policy, candidate);
    let reservation = graph
        .nodes_of_type(interner.intern("ActionReservation"))
        .into_iter()
        .next()
        .expect("native reservation exists");
    let reservation_digest = graph
        .node(reservation)
        .attrs
        .get(&interner.intern("p4_reservation_digest"));
    let proposal_digest = graph
        .node(reservation)
        .attrs
        .get(&interner.intern("p4_proposal_digest"));
    assert!(
        matches!(reservation_digest, Some(Value::Str(value)) if interner.resolve(*value) == digest('9'))
    );
    assert!(
        matches!(proposal_digest, Some(Value::Str(value)) if interner.resolve(*value) == digest('3'))
    );
}

#[test]
fn unverified_action_outcome_cannot_complete() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    action_trace(&mut graph, &mut interner, episode, policy, candidate);
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                4,
                P4ObservationStatus::SealedActionOutcome,
                episode,
                policy,
                candidate,
                Some(digest('6')),
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::Impasse {
            reason: "verified_action_outcome_required"
        }
    ));
}

#[test]
fn unsupported_manifold_has_no_effect() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    graph.remove_node_attr(candidate, interner.intern("future_manifold_values"));
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                1,
                P4ObservationStatus::Initial,
                episode,
                policy,
                candidate,
                None,
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::Impasse { .. }
    ));
    assert!(graph
        .nodes_of_type(interner.intern("GraphActionProposalV1"))
        .is_empty());
}

#[test]
fn stale_or_malformed_receipts_cannot_advance_action_phase() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                1,
                P4ObservationStatus::Initial,
                episode,
                policy,
                candidate,
                None,
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::ProposeIntervention { .. }
    ));
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                1,
                P4ObservationStatus::SealedInterventionOutcome,
                episode,
                policy,
                candidate,
                Some(digest('2')),
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::Impasse {
            reason: "stale_or_replayed_observation"
        }
    ));
    assert!(matches!(
        advance_p4_r0(
            &mut graph,
            &mut interner,
            observation(
                2,
                P4ObservationStatus::SealedInterventionOutcome,
                episode,
                policy,
                candidate,
                Some("sha256:bad".into()),
                None
            ),
            P4R0Limits::default()
        ),
        P4Decision::Impasse {
            reason: "invalid_envelope"
        }
    ));
}
