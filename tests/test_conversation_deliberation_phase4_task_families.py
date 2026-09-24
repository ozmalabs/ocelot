"""Held-out Phase 4 task-family coverage.

These tests exercise cognition evidence, not rendered conversation.  A task
family is represented by graph-resident evidence and its native provenance;
the bridge only transports that evidence into the deliberation ledger.  The
decision-state assertions use the existing residual/tolerance contract for
deep deliberation and deliberately pass no message or turn identifier.
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from domains.conversation_deliberation import materialize_from_live_thought_manifold


def _goal(agent, family):
    return agent.s.add_node("Goal", {
        "kind": family,
        "status": "active",
        "cognitive_family": family,
    })


def _family_deliberation(agent, family, *, epoch):
    """Build one held-out family from a source evidence node."""
    goal = _goal(agent, family)
    manifold = agent.s.add_node("ThoughtManifold", {
        "manifold_id": f"held-out-{family}",
        "cognitive_family": family,
        "event_epoch": float(epoch),
    })
    winner = agent.s.add_node("TaskFamilyEvidence", {
        "candidate_id": f"{family}-candidate",
        "cognitive_family": family,
        "grounding": 1.0,
        "expected_value": 0.90,
        "residual_cost": 0.10,
        "consequence": 0.60,
        "novelty": 0.20,
        "execution_ready": 1.0,
        "outcome_status": "resolved",
        "evidence_epoch": float(epoch),
    })
    alternative = agent.s.add_node("TaskFamilyEvidence", {
        "candidate_id": f"{family}-alternative",
        "cognitive_family": family,
        "grounding": 1.0,
        "expected_value": 0.25,
        "residual_cost": 0.20,
        "consequence": 0.10,
        "novelty": 0.10,
        "execution_ready": 0.0,
        "outcome_status": "pending",
        "evidence_epoch": float(epoch),
    })
    # These are substrate evidence classes.  The family itself is carried by
    # the source node, rather than encoded as a language-specific relation.
    relation = "has_repair_evidence" if family in {
        "defer_error", "correction", "contradiction", "topic_shift"
    } else "has_residual_evidence"
    agent.inner.add_edge_unchecked(manifold, relation, winner)
    agent.inner.add_edge_unchecked(manifold, relation, alternative)
    deliberation = materialize_from_live_thought_manifold(
        agent, goal=goal, manifold=manifold, epoch=epoch,
    )
    return deliberation, manifold, winner, alternative, relation


def _assert_native_family_trace(agent, deliberation, manifold, winner,
                                alternative, relation, family):
    attrs = agent.s.node(deliberation)["attrs"]
    assert attrs["candidate_source"] == "live_thought_manifold"
    assert list(agent.inner.neighbours(deliberation,
                                      "generated_from_thought_manifold")) == [manifold]

    ledger = {
        agent.s.node(node)["attrs"]["candidate_id"]: node
        for node in agent.inner.neighbours(deliberation, "has_candidate")
    }
    winner_id = f"{relation}:{family}-candidate"
    alternative_id = f"{relation}:{family}-alternative"
    assert set(ledger) == {winner_id, alternative_id}
    for node in ledger.values():
        assert list(agent.inner.neighbours(node, "derived_from_evidence"))
        assert agent.s.node(node)["attrs"]["source_relation"] == relation

    agent.inner.run_rules()
    attrs = agent.s.node(deliberation)["attrs"]
    assert attrs["status"] == "resolved"
    assert attrs["candidate_trace_complete"] == 1.0
    selection = list(agent.inner.neighbours(deliberation, "has_selection"))
    settlement = list(agent.inner.neighbours(deliberation, "has_settlement"))
    credit = list(agent.inner.neighbours(deliberation, "has_counterfactual_credit"))
    assert len(selection) == len(settlement) == len(credit) == 1
    assert agent.s.node(selection[0])["attrs"]["selected_candidate_id"] == winner_id
    assert agent.s.node(settlement[0])["attrs"]["candidate_id"] == winner_id
    credit_attrs = agent.s.node(credit[0])["attrs"]
    assert credit_attrs["rejected_candidate_id"] == alternative_id
    assert credit_attrs["counterfactual_status"] == "unexecuted_alternative"
    assert agent.s.node(ledger[winner_id])["attrs"]["status"] == "resolved"
    assert agent.s.node(ledger[alternative_id])["attrs"]["status"] == "rejected"
    assert agent.s.node(winner)["attrs"]["cognitive_family"] == family
    assert agent.s.node(alternative)["attrs"]["cognitive_family"] == family


@pytest.mark.parametrize(
    "family",
    ["defer_error", "correction", "contradiction", "topic_shift"],
)
def test_held_out_family_preserves_native_provenance_and_settle_back(family):
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(
        manifest_for("conversation_deliberation_phase4a"), agent.agent)
    d, manifold, winner, alternative, relation = _family_deliberation(
        agent, family, epoch=17)
    _assert_native_family_trace(
        agent, d, manifold, winner, alternative, relation, family)


def test_asynchronous_residual_is_event_scoped_not_turn_scoped():
    """A residual arriving at a later epoch remains independently traceable.

    No message node or turn id is supplied.  The event epoch scopes the
    evidence, while native settlement still preserves the source relation.
    """
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(
        manifest_for("conversation_deliberation_phase4a"), agent.agent)
    d, manifold, winner, alternative, relation = _family_deliberation(
        agent, "asynchronous_residual", epoch=31)
    _assert_native_family_trace(
        agent, d, manifold, winner, alternative, relation,
        "asynchronous_residual")
    assert agent.s.node(manifold)["attrs"]["event_epoch"] == 31.0
    assert agent.s.node(winner)["attrs"]["evidence_epoch"] == 31.0
    assert agent.s.node(alternative)["attrs"]["evidence_epoch"] == 31.0


@pytest.mark.parametrize(
    "token,expects_deep",
    [("residual_frame", True), ("residual_fact", False),
     ("residual_inquiry", False), ("follow_up_inquiry", False)],
)
def test_deep_deliberation_has_native_trigger_rationale_without_turn(
        token, expects_deep):
    """The native residual gate explains deep versus shallow mode."""
    agent = WorldAdapter(seeds=())
    agent._record_conversation_decision(token, None)
    states = [node for node in agent.s.nodes("ConversationDecisionState")
              if agent.s.node(node)["attrs"].get("token") == token]
    assert len(states) == 1
    attrs = agent.s.node(states[0])["attrs"]
    assert (attrs["residual"] > attrs["settle_tolerance"]) is expects_deep
    assert attrs["deeper_enabled"] == int(expects_deep)
    assert attrs["settle_mode"] == ("deep" if expects_deep else "shallow")
    assert attrs["settled_candidate"] == token
    assert not list(agent.inner.neighbours(states[0], "has_turn"))
