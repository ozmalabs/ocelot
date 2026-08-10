"""Focused execution tests for graph-native adaptive control."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


SEED_PATH = Path(__file__).parents[1] / "seeds" / "adaptive_control_core.json"


def _edge(agent, src, edge_type, tgt):
    try:
        agent.inner.add_edge_unchecked(src, edge_type, tgt, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, edge_type, tgt)


def _nodes(agent, node_type):
    return [
        nid for nid in agent.s.nodes()
        if agent.s.node(nid)["type"] == node_type
    ]


def _fresh():
    return WorldAdapter(seeds=("adaptive_control_core",))


def _decision(agent, *, epoch=10.0):
    context = agent.s.add_node("AdaptiveContext", {"name": "test_context"})
    state = agent.s.add_node("BeliefState", {"name": "test_state"})
    action = agent.s.add_node("MotorCommand", {
        "name": "turn", "command_value": 2.0,
    })
    controller = agent.s.add_node("Controller", {"name": "test_controller"})
    attention = agent.s.add_node("AttentionChoice", {"name": "foveal_target"})
    model = agent.s.add_node("ForwardModel", {
        "predicted_consequence": 2.0,
        "confidence": 0.6,
        "expected_noise": 0.1,
        "last_calibration_epoch": -1.0,
    })
    decision = agent.s.add_node("AdaptiveDecision", {
        "status": "committed",
        "epoch": float(epoch),
        "prediction_authored": 0,
        "trace_authored": 0,
        "sensorimotor_prediction_authored": 0,
        "reliable": 0,
        "option_evidence_used": 0,
    })
    _edge(agent, agent.agent, "has_adaptive_decision", decision)
    _edge(agent, decision, "in_adaptive_context", context)
    _edge(agent, decision, "selected_state", state)
    _edge(agent, decision, "selected_action", action)
    _edge(agent, decision, "selected_controller", controller)
    _edge(agent, decision, "selected_attention", attention)
    _edge(agent, decision, "uses_forward_model", model)
    return {
        "context": context,
        "state": state,
        "action": action,
        "controller": controller,
        "attention": attention,
        "model": model,
        "decision": decision,
    }


def _outcome(
    agent,
    prediction,
    context,
    *,
    epoch,
    observed,
    expected_noise=0.0,
    volatility=0.0,
    model_ignorance=0.0,
    receipt_verified=1,
):
    outcome = agent.s.add_node("AdaptiveOutcome", {
        "status": "verified",
        "error_evaluated": 0,
        "epoch": float(epoch),
        "observed_value": float(observed),
        "next_value": 0.0,
        "expected_noise": float(expected_noise),
        "volatility": float(volatility),
        "model_ignorance": float(model_ignorance),
        "receipt_verified": int(receipt_verified),
    })
    _edge(agent, agent.agent, "has_adaptive_outcome", outcome)
    _edge(agent, outcome, "evaluates_prediction", prediction)
    _edge(agent, outcome, "in_adaptive_context", context)
    return outcome


def test_adaptive_control_installs_dormant_and_all_rules_load():
    manifest = json.loads(SEED_PATH.read_text())
    agent = _fresh()

    assert len(manifest["rules"]) == 25
    assert len(_nodes(agent, "AdaptiveControlPolicy")) == 1
    assert agent.tick() == 0
    assert _nodes(agent, "OutcomePrediction") == []
    assert _nodes(agent, "FunctionalBroadcast") == []
    assert "conscious" not in " ".join(
        rule["name"] for rule in manifest["rules"]
    ).lower()


def test_signed_multistep_credit_tracks_all_choices_and_controller_value():
    agent = _fresh()
    choice = _decision(agent)

    assert agent.tick() > 0
    prediction = _nodes(agent, "OutcomePrediction")[0]
    trace = _nodes(agent, "EligibilityTrace")[0]
    value = _nodes(agent, "ControllerValue")[0]

    assert agent.s.node(prediction)["attrs"]["expected_value"] == 0.0
    assert agent.s.node(prediction)["attrs"]["observation_status"] == (
        "not_observed"
    )
    assert agent.s.node(trace)["attrs"]["expires_epoch"] == 14.0
    assert list(agent.inner.neighbours(trace, "traces_state")) == [
        choice["state"]
    ]
    assert list(agent.inner.neighbours(trace, "traces_action")) == [
        choice["action"]
    ]
    assert list(agent.inner.neighbours(trace, "traces_controller")) == [
        choice["controller"]
    ]
    assert list(agent.inner.neighbours(trace, "traces_attention")) == [
        choice["attention"]
    ]

    positive = _outcome(
        agent,
        prediction,
        choice["context"],
        epoch=12,
        observed=1.0,
        expected_noise=0.1,
        volatility=0.4,
        model_ignorance=0.2,
    )
    agent.tick()

    attrs = agent.s.node(positive)["attrs"]
    assert attrs["prediction_error"] == pytest.approx(1.0)
    assert attrs["precision_weight"] == pytest.approx(1.0 / 1.3)
    assert attrs["adaptive_learning_rate"] == pytest.approx(0.25 * 1.4 / 1.3)
    assert attrs["exploration_pressure"] == pytest.approx(0.35)
    credit = _nodes(agent, "CreditAssignment")[0]
    assert agent.s.node(credit)["attrs"]["lag"] == 2.0
    assert agent.s.node(credit)["attrs"]["discounted_error"] == pytest.approx(
        0.8**2
    )
    positive_value = agent.s.node(value)["attrs"]["estimate"]
    assert positive_value == pytest.approx((0.25 * 1.4 / 1.3) * 0.8**2)

    negative = _outcome(
        agent,
        prediction,
        choice["context"],
        epoch=13,
        observed=-0.5,
    )
    agent.tick()

    assert agent.s.node(negative)["attrs"]["prediction_error"] == -0.5
    credits = sorted(
        (agent.s.node(node)["attrs"] for node in _nodes(agent, "CreditAssignment")),
        key=lambda item: item["outcome_epoch"],
    )
    assert credits[1]["lag"] == 3.0
    assert credits[1]["discounted_error"] == pytest.approx(
        -0.5 * 0.8**3 * 0.75
    )
    assert agent.s.node(value)["attrs"]["estimate"] < positive_value

    clock = agent.s.add_node("AdaptiveClock", {"epoch": 14.0})
    _edge(agent, agent.agent, "has_adaptive_clock", clock)
    agent.tick()
    assert agent.s.node(trace)["attrs"]["status"] == "expired"


def test_noise_volatility_and_ignorance_have_distinct_control_effects():
    agent = _fresh()
    prediction = agent.s.add_node("OutcomePrediction", {
        "expected_value": 0.0, "status": "open",
    })
    context = agent.s.add_node("AdaptiveContext", {"name": "uncertainty"})

    noisy = _outcome(
        agent, prediction, context, epoch=1, observed=1,
        expected_noise=0.8,
    )
    volatile = _outcome(
        agent, prediction, context, epoch=2, observed=1,
        volatility=0.8,
    )
    ignorant = _outcome(
        agent, prediction, context, epoch=3, observed=1,
        model_ignorance=0.8,
    )
    agent.tick()

    noisy_attrs = agent.s.node(noisy)["attrs"]
    volatile_attrs = agent.s.node(volatile)["attrs"]
    ignorant_attrs = agent.s.node(ignorant)["attrs"]
    assert noisy_attrs["adaptive_learning_rate"] == pytest.approx(0.25 / 1.8)
    assert volatile_attrs["adaptive_learning_rate"] == pytest.approx(0.25 * 1.8)
    assert ignorant_attrs["adaptive_learning_rate"] == pytest.approx(0.25 / 1.8)
    assert noisy_attrs["exploration_pressure"] == 0.0
    assert volatile_attrs["exploration_pressure"] == pytest.approx(0.4)
    assert ignorant_attrs["exploration_pressure"] == pytest.approx(0.8)


def test_verified_status_without_a_receipt_cannot_drive_learning():
    agent = _fresh()
    choice = _decision(agent)
    agent.tick()
    prediction = _nodes(agent, "OutcomePrediction")[0]
    value = _nodes(agent, "ControllerValue")[0]
    spoofed = _outcome(
        agent,
        prediction,
        choice["context"],
        epoch=11,
        observed=1.0,
        receipt_verified=0,
    )

    assert agent.tick() == 0
    assert agent.s.node(spoofed)["attrs"]["status"] == "verified"
    assert "prediction_error" not in agent.s.node(spoofed)["attrs"]
    assert _nodes(agent, "CreditAssignment") == []
    assert agent.s.node(value)["attrs"]["experience_count"] == 0.0

    agent.inner.set_attr(spoofed, "receipt_verified", 1)
    assert agent.tick() > 0
    assert agent.s.node(spoofed)["attrs"]["status"] == "evaluated"
    assert agent.s.node(spoofed)["attrs"]["prediction_error"] == 1.0
    assert len(_nodes(agent, "CreditAssignment")) == 1
    assert agent.s.node(value)["attrs"]["experience_count"] == 1.0


def test_efference_copy_and_receipt_gated_forward_model_calibration():
    agent = _fresh()
    choice = _decision(agent)
    agent.tick()

    copy = _nodes(agent, "EfferenceCopy")[0]
    prediction = _nodes(agent, "PredictedSensoryConsequence")[0]
    assert agent.s.node(copy)["attrs"]["command_value"] == 2.0
    assert agent.s.node(copy)["attrs"]["status"] == (
        "intended_not_yet_verified"
    )
    assert agent.s.node(prediction)["attrs"]["predicted_signal"] == 2.0
    assert agent.s.node(prediction)["attrs"]["observation_status"] == (
        "not_observed"
    )

    consequence = agent.s.add_node("SensoryConsequence", {
        "status": "observed",
        "receipt_verified": 0,
        "calibration_applied": 0,
        "epoch": 11.0,
        "signal_value": 2.5,
    })
    _edge(agent, consequence, "reports_decision", choice["decision"])
    assert agent.tick() == 0
    assert _nodes(agent, "SensorimotorResidual") == []

    agent.inner.set_attr(consequence, "receipt_verified", 1)
    assert agent.tick() > 0
    residual = _nodes(agent, "SensorimotorResidual")[0]
    assert agent.s.node(residual)["attrs"]["residual"] == pytest.approx(0.5)
    assert agent.s.node(residual)["attrs"]["attribution"] == (
        "self_generated_receipt_backed"
    )
    model = agent.s.node(choice["model"])["attrs"]
    assert model["predicted_consequence"] == pytest.approx(2.125)
    assert model["confidence"] == pytest.approx(0.5890909091)
    assert model["last_calibration_epoch"] == 11.0
    assert agent.tick() == 0
    assert len(_nodes(agent, "SensorimotorResidual")) == 1


def test_repeated_reliable_sequence_proposes_one_unevaluated_option():
    agent = _fresh()
    action_one = agent.s.add_node("MotorCommand", {"name": "turn_left"})
    action_two = agent.s.add_node("MotorCommand", {"name": "advance"})
    decisions = []
    for epoch, action in enumerate(
        (action_one, action_two, action_one, action_two), start=1
    ):
        decision = agent.s.add_node("AdaptiveDecision", {
            "status": "settled",
            "epoch": float(epoch),
            "reliable": 1,
            "option_evidence_used": 0,
        })
        _edge(agent, agent.agent, "has_adaptive_decision", decision)
        _edge(agent, decision, "selected_action", action)
        decisions.append(decision)
    _edge(agent, decisions[0], "next_adaptive_decision", decisions[1])
    _edge(agent, decisions[2], "next_adaptive_decision", decisions[3])

    agent.tick()

    options = _nodes(agent, "SkillOptionCandidate")
    assert len(options) == 1
    attrs = agent.s.node(options[0])["attrs"]
    assert attrs["status"] == "candidate"
    assert attrs["reliable_execution_count"] == 2.0
    assert attrs["requires_evaluation"] == 1
    assert list(agent.inner.neighbours(options[0], "first_action")) == [
        action_one
    ]
    assert list(agent.inner.neighbours(options[0], "second_action")) == [
        action_two
    ]
    assert agent.tick() == 0
    assert len(_nodes(agent, "SkillOptionCandidate")) == 1


def test_allostatic_forecast_competes_broadcasts_and_expires_by_clock():
    agent = _fresh()
    consumers = [
        agent.s.add_node("BroadcastConsumer", {"name": name})
        for name in ("working_memory", "planning")
    ]
    for consumer in consumers:
        _edge(agent, agent.agent, "has_broadcast_consumer", consumer)
    forecast = agent.s.add_node("InteroceptiveForecast", {
        "status": "raw",
        "processed": 0,
        "epoch": 5.0,
        "current_level": 1.0,
        "predicted_demand": 0.7,
        "desired_reserve": 0.8,
        "expected_noise": 0.1,
        "model_ignorance": 0.2,
    })
    _edge(agent, agent.agent, "has_interoceptive_forecast", forecast)

    agent.tick()

    error = _nodes(agent, "AllostaticError")[0]
    error_attrs = agent.s.node(error)["attrs"]
    assert error_attrs["forecast_level"] == pytest.approx(0.3)
    assert error_attrs["error"] == pytest.approx(0.5)
    assert error_attrs["precision"] == pytest.approx(1.0 / 1.3)
    assert error_attrs["observation_status"] == "not_observed"

    broadcasts = _nodes(agent, "FunctionalBroadcast")
    assert len(broadcasts) == 1
    broadcast = broadcasts[0]
    attrs = agent.s.node(broadcast)["attrs"]
    assert attrs["status"] == "active"
    assert attrs["source_kind"] == "allostatic_forecast"
    assert attrs["functional_routing_only"] == 1
    assert attrs["expires_epoch"] == 7.0
    assert set(agent.inner.neighbours(
        broadcast, "available_to_consumer"
    )) == set(consumers)
    assert agent.tick() == 0

    clock = agent.s.add_node("AdaptiveClock", {"epoch": 7.0})
    _edge(agent, agent.agent, "has_adaptive_clock", clock)
    agent.tick()
    assert agent.s.node(broadcast)["attrs"]["status"] == "expired"


def test_exact_broadcast_tie_is_refused_without_order_breaking():
    agent = _fresh()
    candidates = []
    for index in range(2):
        content = agent.s.add_node("BroadcastContent", {"index": index})
        candidate = agent.s.add_node("BroadcastCandidate", {
            "epoch": 1.0,
            "status": "pending",
            "salience": 0.5,
            "urgency": 0.2,
            "confidence": 1.0,
            "precision": 1.0,
            "ttl": 2.0,
            "priority": 0.0,
            "source_kind": "test",
            "provenance_kind": "observed",
        })
        _edge(agent, agent.agent, "has_broadcast_candidate", candidate)
        _edge(agent, candidate, "about_content", content)
        candidates.append(candidate)

    agent.tick()

    assert _nodes(agent, "FunctionalBroadcast") == []
    assert len(_nodes(agent, "BroadcastTie")) == 1
    assert {
        agent.s.node(candidate)["attrs"]["status"]
        for candidate in candidates
    } == {"refused_exact_tie"}
    assert agent.tick() == 0


def test_unselected_broadcast_candidate_has_clock_bounded_ttl():
    agent = _fresh()
    content = agent.s.add_node("BroadcastContent", {"name": "weak_signal"})
    candidate = agent.s.add_node("BroadcastCandidate", {
        "epoch": 1.0,
        "status": "pending",
        "salience": 0.05,
        "urgency": 0.0,
        "confidence": 1.0,
        "precision": 1.0,
        "ttl": 2.0,
        "priority": 0.0,
        "source_kind": "test",
        "provenance_kind": "observed",
    })
    _edge(agent, agent.agent, "has_broadcast_candidate", candidate)
    _edge(agent, candidate, "about_content", content)

    agent.tick()
    assert agent.s.node(candidate)["attrs"]["status"] == "scored"
    assert _nodes(agent, "FunctionalBroadcast") == []

    clock = agent.s.add_node("AdaptiveClock", {"epoch": 3.0})
    _edge(agent, agent.agent, "has_adaptive_clock", clock)
    agent.tick()
    assert agent.s.node(candidate)["attrs"]["status"] == "expired"


def test_terminal_transients_prune_after_retention_but_learning_survives():
    agent = _fresh()
    controller_value = agent.s.add_node("ControllerValue", {
        "estimate": 0.75, "experience_count": 4.0,
    })
    forward_model = agent.s.add_node("ForwardModel", {
        "predicted_consequence": 2.25, "confidence": 0.8,
    })
    skill_option = agent.s.add_node("SkillOptionCandidate", {
        "status": "candidate", "reliable_execution_count": 2.0,
    })

    broadcast = agent.s.add_node("FunctionalBroadcast", {
        "status": "expired", "epoch": 3.0, "expires_epoch": 5.0,
        "expired_epoch": 5.0,
    })
    candidate = agent.s.add_node("BroadcastCandidate", {
        "status": "refused_exact_tie", "epoch": 3.0, "ttl": 2.0,
    })
    tie = agent.s.add_node("BroadcastTie", {
        "status": "refused", "epoch": 3.0,
    })
    trace = agent.s.add_node("EligibilityTrace", {
        "status": "expired", "expired_epoch": 5.0,
    })
    error = agent.s.add_node("WorldModelPredictionError", {
        "status": "integrated", "epoch": 5.0,
    })
    for edge_type, transient in (
        ("has_functional_broadcast", broadcast),
        ("has_broadcast_candidate", candidate),
        ("has_broadcast_tie", tie),
        ("has_eligibility_trace", trace),
        ("has_prediction_error", error),
    ):
        _edge(agent, agent.agent, edge_type, transient)

    clock = agent.s.add_node("AdaptiveClock", {"epoch": 6.0})
    _edge(agent, agent.agent, "has_adaptive_clock", clock)
    assert agent.tick() == 0
    live = set(agent.s.nodes())
    assert {broadcast, candidate, tie, trace, error} <= live

    agent.inner.set_attr(clock, "epoch", 7.0)
    assert agent.tick() > 0
    live = set(agent.s.nodes())
    assert not ({broadcast, candidate, tie, trace, error} & live)
    assert {controller_value, forward_model, skill_option} <= live
    assert agent.s.node(controller_value)["attrs"]["estimate"] == 0.75
    assert agent.s.node(forward_model)["attrs"]["confidence"] == 0.8
    assert agent.s.node(skill_option)["attrs"]["status"] == "candidate"
    assert agent.tick() == 0
