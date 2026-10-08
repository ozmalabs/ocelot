use rustc_hash::FxHashMap;
use std::sync::Arc;

use crate::{
    graph::{NodeID, TypedGraph},
    p4_readiness::{
        advance_p4_r0, advance_signed_evaluator_outcome, P4Decision, P4ObservationStatus,
        P4R0Limits, P4TrustedEvaluatorAuthority, SealedObservation,
    },
    sym::Interner,
    value::Value,
};

const PUBLIC_KEY: &str = "A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg";
const SIGNED_TRANSPORT: &str = r#"{"authority_id":"p4-r0-evaluator","authority_public_key":"A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg","broker_receipt_digest":"sha256:5555555555555555555555555555555555555555555555555555555555555555","grant_receipt_digest":"sha256:4444444444444444444444444444444444444444444444444444444444444444","key_id":"p4-r0-local-test-key","lock_digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","outcome_receipt_digest":"sha256:6666666666666666666666666666666666666666666666666666666666666666","proposal_digest":"sha256:3333333333333333333333333333333333333333333333333333333333333333","proposal_receipt_digest":"sha256:8888888888888888888888888888888888888888888888888888888888888888","replan_receipt_digest":"sha256:2222222222222222222222222222222222222222222222222222222222222222","reservation_digest":"sha256:9999999999999999999999999999999999999999999999999999999999999999","run_id":"run","schema":"P4R0EvaluatorSignedOutcomeV1","sequence":4,"signature":"pHLvh6ACmsuQhFBytYGO7ypN7iF37zt1XNIOZ_rWzNBhN3bj3Ulw7iw0P9dAu4alYGCPFzbhvkaRhbY8F9eBBg","snapshot_digest":"sha256:1111111111111111111111111111111111111111111111111111111111111111","success":true}"#;
const SIGNED_ALTERED_RESERVATION: &str = r#"{"authority_id":"p4-r0-evaluator","authority_public_key":"A6EHv_POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg","broker_receipt_digest":"sha256:5555555555555555555555555555555555555555555555555555555555555555","grant_receipt_digest":"sha256:4444444444444444444444444444444444444444444444444444444444444444","key_id":"p4-r0-local-test-key","lock_digest":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","outcome_receipt_digest":"sha256:6666666666666666666666666666666666666666666666666666666666666666","proposal_digest":"sha256:3333333333333333333333333333333333333333333333333333333333333333","proposal_receipt_digest":"sha256:8888888888888888888888888888888888888888888888888888888888888888","replan_receipt_digest":"sha256:2222222222222222222222222222222222222222222222222222222222222222","reservation_digest":"sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff","run_id":"run","schema":"P4R0EvaluatorSignedOutcomeV1","sequence":4,"signature":"0X8kymlg7CDKHDESFbvnNMmUk7X3e5PjA9xCcG1wJ2PfdkD-PZwEe0djYgdecNr2aeVbPTiwjwjDQ4Wn7og9CA","snapshot_digest":"sha256:1111111111111111111111111111111111111111111111111111111111111111","success":true}"#;

fn digest(c: char) -> String {
    format!("sha256:{}", c.to_string().repeat(64))
}

fn authority() -> P4TrustedEvaluatorAuthority {
    P4TrustedEvaluatorAuthority::from_base64url(
        "p4-r0-evaluator".into(),
        "p4-r0-local-test-key".into(),
        digest('a'),
        PUBLIC_KEY,
    )
    .expect("deterministic evaluator key")
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

fn reach_action_phase(
    graph: &mut TypedGraph,
    interner: &mut Interner,
    episode: NodeID,
    policy: NodeID,
    candidate: NodeID,
) {
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
    let replan = digest('2');
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

fn runtime_observation(episode: NodeID, policy: NodeID, candidate: NodeID) -> SealedObservation {
    observation(
        4,
        P4ObservationStatus::SealedActionOutcome,
        episode,
        policy,
        candidate,
        Some(digest('6')),
        None,
    )
}

#[test]
fn runtime_signed_transport_completes_only_through_native_adapter() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    reach_action_phase(&mut graph, &mut interner, episode, policy, candidate);
    assert_eq!(
        advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            runtime_observation(episode, policy, candidate),
            SIGNED_TRANSPORT.as_bytes(),
            &authority(),
            P4R0Limits::default(),
        ),
        Ok(P4Decision::Complete),
    );
}

#[test]
fn runtime_rejects_forged_signature_before_capability_minting() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    reach_action_phase(&mut graph, &mut interner, episode, policy, candidate);
    let forged = SIGNED_TRANSPORT.replacen("pHLvh6", "AHLvh6", 1);
    assert_eq!(
        advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            runtime_observation(episode, policy, candidate),
            forged.as_bytes(),
            &authority(),
            P4R0Limits::default()
        ),
        Err("evaluator_receipt_verification_failed"),
    );
}

#[test]
fn runtime_rejects_missing_and_noncanonical_transport_before_adapter() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    reach_action_phase(&mut graph, &mut interner, episode, policy, candidate);
    let missing = SIGNED_TRANSPORT.replace(
        "\"reservation_digest\":\"sha256:9999999999999999999999999999999999999999999999999999999999999999\",",
        "",
    );
    assert_eq!(
        advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            runtime_observation(episode, policy, candidate),
            missing.as_bytes(),
            &authority(),
            P4R0Limits::default()
        ),
        Err("invalid_evaluator_transport"),
    );
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    reach_action_phase(&mut graph, &mut interner, episode, policy, candidate);
    let noncanonical = format!("{SIGNED_TRANSPORT}\n");
    assert_eq!(
        advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            runtime_observation(episode, policy, candidate),
            noncanonical.as_bytes(),
            &authority(),
            P4R0Limits::default()
        ),
        Err("noncanonical_evaluator_transport"),
    );
}

#[test]
fn runtime_rejects_validly_signed_altered_native_binding() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    reach_action_phase(&mut graph, &mut interner, episode, policy, candidate);
    assert_eq!(
        advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            runtime_observation(episode, policy, candidate),
            SIGNED_ALTERED_RESERVATION.as_bytes(),
            &authority(),
            P4R0Limits::default()
        ),
        Err("evaluator_outcome_binding_mismatch"),
    );
}

#[test]
fn runtime_rejects_replayed_verified_transport_after_completion() {
    let (mut graph, mut interner, episode, policy, candidate) = setup();
    reach_action_phase(&mut graph, &mut interner, episode, policy, candidate);
    assert_eq!(
        advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            runtime_observation(episode, policy, candidate),
            SIGNED_TRANSPORT.as_bytes(),
            &authority(),
            P4R0Limits::default()
        ),
        Ok(P4Decision::Complete),
    );
    assert_eq!(
        advance_signed_evaluator_outcome(
            &mut graph,
            &mut interner,
            runtime_observation(episode, policy, candidate),
            SIGNED_TRANSPORT.as_bytes(),
            &authority(),
            P4R0Limits::default()
        ),
        Ok(P4Decision::Impasse {
            reason: "replayed_action_outcome"
        }),
    );
}
