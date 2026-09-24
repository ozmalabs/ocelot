"""Phase 4 boundary: proposition consequences do not become deliberation evidence.

These tests exercise the existing proposition, situation-model, live-manifold,
and native deliberation APIs.  The boundary under test is deliberately narrow:
an accepted situation consequence is cognitive state, not a thought candidate;
only an explicitly authored complete Phase 4 evidence wrapper may cross into
the deliberation manifold.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.conversation_deliberation import materialize_from_live_thought_manifold
from domains.proposition_commitment import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA,
    apply_situation_consequence,
    bridge_proposition_evidence,
)
from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


def _agent():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    agent.inner.load_seed_manifest(
        manifest_for("conversation_deliberation_phase4a"), agent.agent)
    return agent


def _accepted_proposition(agent, *, evidence_id="phase4-boundary-1"):
    event = agent.s.add_node("DiscourseEvent", {
        "schema": "discourse_event.v1", "event_index": 1.0,
    })
    result = bridge_proposition_evidence(
        agent,
        {
            "schema": EVIDENCE_SCHEMA,
            "kind": EVIDENCE_KIND,
            "predicate": "drop",
            "arguments": {"agent": "john", "theme": "glass"},
            "polarity": "affirmed",
            "provider": "phase4_boundary_test",
            "evidence_id": evidence_id,
            "commitment_status": "proposed",
            "uptake_signal": "accept",
        },
        source_event=event,
    )
    assert result["supported"] is True
    agent.inner.run_rules()
    consequence = apply_situation_consequence(agent, result["proposition"])
    assert consequence["supported"] is True
    return event, result["proposition"], consequence["consequence"]


def _live_boundary(agent, *, event, consequence, partial=False):
    agent.inner.add_edge_unchecked(event, "grounded_in", consequence)
    wrapper = agent.s.add_node("AuthoredPhase4Evidence", {
        "phase4_evidence": {
            "candidate_id": "authored-consequence",
            "kind": "situation_model_consequence",
            "grounding": 1.0,
            "expected_value": 0.9,
            "residual_cost": 0.1,
            "consequence": 0.8,
            **({} if partial else {"novelty": 0.2}),
            "evidence_path": "proposition->consequence->authored_phase4",
        }
    })
    agent.inner.add_edge_unchecked(consequence, "supports", wrapper)
    state = agent.s.add_node("DiscourseState", {
        "schema": "discourse_state.v1",
    })
    goal = agent.s.add_node("Goal", {
        "kind": "answer", "status": "active",
    })
    manifold, has_evidence = agent._live_thought_manifold_evidence(
        None, state, event, goal)
    return manifold, wrapper, has_evidence


def test_accepted_situation_consequence_alone_creates_no_thought_candidate():
    agent = _agent()
    _, proposition, consequence = _accepted_proposition(agent)

    assert agent.s.node(proposition)["attrs"]["commitment_status"] == "accepted"
    assert agent.s.node(consequence)["attrs"]["status"] == "applied"
    assert len(agent.s.nodes("ThoughtCandidate")) == 0
    assert len(agent.s.nodes("DeliberativeCandidate")) == 0


def test_incomplete_phase4_wrapper_is_rejected_without_thought_candidate():
    agent = _agent()
    event, _, consequence = _accepted_proposition(agent)

    manifold, _, has_evidence = _live_boundary(
        agent, event=event, consequence=consequence, partial=True)

    assert has_evidence is False
    assert len(agent.s.nodes("ThoughtCandidate")) == 0
    assert list(agent.inner.neighbours(manifold, "has_goal_evidence")) == []


def test_complete_authored_evidence_is_consumed_once_with_proposition_provenance():
    agent = _agent()
    event, proposition, consequence = _accepted_proposition(agent)

    manifold, wrapper, has_evidence = _live_boundary(
        agent, event=event, consequence=consequence)
    assert has_evidence is True
    first = list(agent.inner.neighbours(manifold, "has_goal_evidence"))
    assert len(first) == 1

    # Re-running the mechanical boundary must not duplicate the candidate.
    manifold_again, has_evidence_again = agent._live_thought_manifold_evidence(
        None, agent.s.node(consequence)["attrs"].get("discourse_state_id"),
        event, agent.s.add_node("Goal", {"kind": "answer", "status": "active"}))
    assert manifold_again == manifold
    assert has_evidence_again is True
    second = list(agent.inner.neighbours(manifold, "has_goal_evidence"))
    assert second == first

    assert agent.s.has_edge(consequence, "for_proposition", proposition)
    assert agent.s.has_edge(consequence, "supports", wrapper)
    assert agent.s.has_edge(first[0], "derived_from_evidence", wrapper)
    assert agent.s.node(first[0])["attrs"]["evidence_path"] == (
        "proposition->consequence->authored_phase4"
    )


def test_native_selection_owns_outcome_after_complete_evidence_crosses_boundary():
    agent = _agent()
    event, proposition, consequence = _accepted_proposition(agent)
    agent.inner.add_edge_unchecked(event, "grounded_in", consequence)

    high = agent.s.add_node("AuthoredPhase4Evidence", {
        "phase4_evidence": {
            "candidate_id": "high", "kind": "answer", "grounding": 1.0,
            "expected_value": 0.9, "residual_cost": 0.1,
            "consequence": 0.8, "novelty": 0.2,
        }
    })
    low = agent.s.add_node("AuthoredPhase4Evidence", {
        "phase4_evidence": {
            "candidate_id": "low", "kind": "answer", "grounding": 1.0,
            "expected_value": 0.1, "residual_cost": 0.1,
            "consequence": 0.1, "novelty": 0.1,
        }
    })
    # Two independent authored evidence sources are presented at the event
    # boundary.  The proposition/consequence provenance chain is asserted in
    # the preceding test; native selection must compare these two sources.
    agent.inner.add_edge_unchecked(event, "grounded_in", high)
    agent.inner.add_edge_unchecked(event, "grounded_in", low)
    goal = agent.s.add_node("Goal", {"kind": "answer", "status": "active"})

    manifold, has_evidence = agent._live_thought_manifold_evidence(
        None, agent.s.add_node("DiscourseState", {}), event, goal)
    assert has_evidence is True
    candidates = list(agent.inner.neighbours(manifold, "has_goal_evidence"))
    assert len(candidates) == 2

    deliberation = materialize_from_live_thought_manifold(
        agent, goal=goal, manifold=manifold)
    agent.inner.run_rules()

    assert agent.s.node(deliberation)["attrs"]["status"] == "selected"
    selection = list(agent.inner.neighbours(deliberation, "has_selection"))
    assert len(selection) == 1
    selected = list(agent.inner.neighbours(selection[0], "selects_candidate"))
    assert len(selected) == 1
    assert agent.s.node(selected[0])["attrs"]["candidate_id"].endswith(":high")
    assert agent.s.has_edge(consequence, "for_proposition", proposition)
