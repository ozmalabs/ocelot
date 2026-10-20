"""Execution gates for impasse_simulation_bridge (P1.A4)."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "impasse_simulation_bridge.json"
GENERATOR = ROOT / "scripts" / "gen_impasse_simulation_bridge_seed.py"

for path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter


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


def _add(agent, node_type, attrs, edge_type=None):
    node = agent.s.add_node(node_type, attrs)
    if edge_type is not None:
        _edge(agent, agent.agent, edge_type, node)
    return node


def _fresh(*, enabled=False):
    agent = WorldAdapter(seeds=(
        "affective_state_core",
        "dual_process_core",
        "generative_world_model",
        "default_mode_core",
        "impasse_simulation_bridge",
    ))
    policies = _nodes(agent, "ImpasseSimulationPolicy")
    assert len(policies) == 1
    if enabled:
        agent.s.set_attr(policies[0], "enabled", 1.0)
    mode = _nodes(agent, "NetworkModeState")[0]
    agent.s.set_attr(mode, "epoch", 1.0)
    return agent


def _perceive(agent, epoch=1):
    observation = _add(agent, "WorldModelObservation", {
        "belief_status": "new",
        "prediction_comparison_status": "uncompared",
        "provenance_kind": "perceived",
        "state_kind": "corridor",
        "state_summary": "door ahead, cover on the left",
        "epoch": float(epoch),
        "confidence": 0.9,
        "uncertainty": 0.1,
    }, "has_world_model_observation")
    agent.dual_process_tick()
    return observation, _nodes(agent, "BeliefState")[-1]


def _model_repertoire(agent):
    forward = _add(agent, "WorldModelAction", {
        "action_kind": "forward", "branch_rank": 1.0,
    }, "has_world_model_action")
    turn = _add(agent, "WorldModelAction", {
        "action_kind": "turn_left", "branch_rank": 2.0,
    }, "has_world_model_action")

    for rank, source, action, successor, observation, outcome, value in (
        (1, "corridor", "forward", "junction", "junction_visible",
         "progress", 0.7),
        (2, "corridor", "turn_left", "corridor", "left_wall_visible",
         "safe_reorientation", 0.2),
        (3, "junction", "forward", "exit", "exit_visible",
         "goal_progress", 1.0),
        (4, "junction", "turn_left", "corridor", "side_route_visible",
         "safe_reorientation", 0.4),
    ):
        transition = _add(agent, "TransitionHypothesis", {
            "source_state_kind": source,
            "action_kind": action,
            "successor_state_kind": successor,
            "successor_summary": f"{action} predicts {successor}",
            "predicted_observation_kind": observation,
            "predicted_observation_value": value,
            "predicted_outcome_kind": outcome,
            "predicted_outcome_value": value,
            "confidence": 0.8,
            "uncertainty": 0.2,
            "model_rank": float(rank),
            "revision_count": 0.0,
        }, "has_transition_hypothesis")
        feature = _add(agent, "TransitionFeature", {
            "feature_key": f"affordance:{action}",
            "feature_value": successor,
            "confidence": 0.9,
        })
        _edge(agent, transition, "predicts_feature", feature)
    return forward, turn


def _context(agent, *, epoch=1):
    context = agent.s.add_node("DualProcessContext", {
        "status": "pending",
        "epoch": epoch,
        "prediction_error": 0.0,
        "novelty": 0.0,
        "uncertainty": 0.0,
        "system_two_expected_utility": 0.0,
        "system_two_reliability": 0.0,
        "system_two_latency": 0.0,
        "system_two_effort": 0.0,
    })
    _edge(agent, agent.agent, "has_dual_process_context", context)
    return context


def _candidate(agent, context, *, epoch=1, value=1.0, residual=0.0):
    candidate = agent.s.add_node("SystemOneCandidate", {
        "status": "ready",
        "epoch": epoch,
        "default_value": value,
        "urgency": 0.0,
        "valence": 0.0,
        "residual": residual,
        "grounded": 1,
        "reliability": 1.0,
        "learned_default": 0,
        "consolidation_strength": 0.0,
        "accumulated_evidence": 0.0,
        "evidence_increment": 0.0,
        "experience_count": 0,
        "eligibility_trace": 1.0,
        "predicted_value": 0.0,
    })
    _edge(agent, context, "has_system_one_candidate", candidate)
    return candidate


def test_generator_reproduces_committed_seed_exactly():
    before = SEED.read_bytes()
    subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert SEED.read_bytes() == before


def test_disabled_policy_produces_no_impasse_simulation_request():
    agent = _fresh(enabled=False)
    _perceive(agent, epoch=1)
    _model_repertoire(agent)
    ctx = _context(agent, epoch=1)
    _candidate(agent, ctx, value=1.0)
    _candidate(agent, ctx, value=1.0)

    agent.dual_process_tick()

    assert _nodes(agent, "SimulationRequest") == []
    assert _nodes(agent, "ImaginedCandidate") == []


def test_instinct_conflict_triggers_simulation_and_proposes_best_imagined_candidate():
    agent = _fresh(enabled=True)
    _, perceived_belief = _perceive(agent, epoch=1)
    _model_repertoire(agent)

    perceived_before = [
        nid for nid in agent.s.nodes()
        if agent.s.node(nid)["attrs"].get("provenance_kind") == "perceived"
    ]

    ctx = _context(agent, epoch=1)
    _candidate(agent, ctx, value=1.0)
    _candidate(agent, ctx, value=1.0)

    agent.dual_process_tick()
    reqs = [
        nid for nid in _nodes(agent, "SimulationRequest")
        if agent.s.node(nid)["attrs"].get("request_kind") == "impasse_counterfactual"
    ]
    if reqs and agent.s.node(reqs[0])["attrs"].get("status") != "completed":
        agent.dual_process_tick()

    assert len(reqs) == 1
    sim = reqs[0]
    assert agent.s.node(sim)["attrs"]["status"] == "completed"

    trajectories = list(agent.inner.neighbours(sim, "has_prediction_trajectory"))
    assert len(trajectories) == 2
    assert all(
        agent.s.node(t)["attrs"]["provenance_kind"] == "imagined"
        for t in trajectories
    )

    escalations = list(agent.inner.neighbours(ctx, "has_system_two_escalation"))
    assert len(escalations) == 1
    esc = escalations[0]

    imagined = list(agent.inner.neighbours(esc, "has_imagined_candidate"))
    assert len(imagined) == 1
    cand_attrs = agent.s.node(imagined[0])["attrs"]
    assert cand_attrs["status"] == "proposal"
    assert cand_attrs["provenance_kind"] == "imagined"
    assert cand_attrs["observation_status"] == "not_observed"
    assert cand_attrs["root_action_kind"] == "forward"
    assert cand_attrs["expected_value"] == pytest.approx(0.576)

    # Live BeliefState stays current and no new perceived nodes appear.
    assert agent.s.node(perceived_belief)["attrs"]["status"] == "current"
    perceived_after = [
        nid for nid in agent.s.nodes()
        if agent.s.node(nid)["attrs"].get("provenance_kind") == "perceived"
    ]
    assert perceived_after == perceived_before


def test_advancing_clock_past_deadline_prunes_simulation_family():
    agent = _fresh(enabled=True)
    _perceive(agent, epoch=1)
    _model_repertoire(agent)

    ctx = _context(agent, epoch=1)
    _candidate(agent, ctx, value=1.0)
    _candidate(agent, ctx, value=1.0)

    agent.dual_process_tick()
    assert len(_nodes(agent, "SimulationRequest")) == 1

    mode = _nodes(agent, "NetworkModeState")[0]
    # deadline_epoch is 1.0 + 4.0 = 5.0; advance to 6.0 to cancel/expire
    agent.s.set_attr(mode, "epoch", 6.0)
    agent.dual_process_tick()

    # cleanup_after_epoch is 6.0 + 2.0 = 8.0; advance to 8.0 to prune
    agent.s.set_attr(mode, "epoch", 8.0)
    agent.dual_process_tick()

    assert _nodes(agent, "SimulationRequest") == []
    assert _nodes(agent, "PredictionTrajectory") == []
    assert _nodes(agent, "PredictedBeliefState") == []
    assert _nodes(agent, "PredictedObservation") == []
    assert _nodes(agent, "PredictedOutcome") == []
    assert _nodes(agent, "PredictedFeature") == []


def test_unique_grounded_default_commits_without_requesting_simulation():
    agent = _fresh(enabled=True)
    _perceive(agent, epoch=1)
    _model_repertoire(agent)

    ctx = _context(agent, epoch=1)
    _candidate(agent, ctx, value=1.0)
    _candidate(agent, ctx, value=2.0)

    agent.dual_process_tick()

    assert agent.s.node(ctx)["attrs"]["status"] == "committed"
    assert _nodes(agent, "SimulationRequest") == []
    assert _nodes(agent, "ImaginedCandidate") == []
