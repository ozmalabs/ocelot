"""Phase 2S coverage for proposition lifecycle and neutral event boundaries.

These tests intentionally use the existing graph APIs directly.  They do not
teach the substrate new rules and do not turn grounding metadata into truth:
an ambiguous, world-missing, or contradicted frame remains an event-level
record unless an explicit proposition/uptake path supports more.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.proposition_commitment import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA,
    apply_situation_consequence,
    bridge_proposition_evidence,
)
from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


def _agent(*, lifecycle=False):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    if lifecycle:
        agent.inner.load_seed_manifest(
            manifest_for("proposition_commitment_lifecycle"), agent.agent)
    return agent


def _evidence(evidence_id="phase2s-1", **updates):
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "predicate": "drop",
        "arguments": {"agent": "john", "theme": "glass"},
        "polarity": "affirmed",
        "provider": "phase2s_neutral_adapter",
        "evidence_id": evidence_id,
        "commitment_status": "proposed",
    }
    evidence.update(updates)
    return evidence


def test_explicit_accept_then_retract_preserves_history_and_blocks_new_projection():
    agent = _agent(lifecycle=True)
    result = bridge_proposition_evidence(
        agent, _evidence(uptake_signal="accept"))
    assert result["supported"] is True
    proposition = result["proposition"]

    agent.inner.run_rules()
    assert agent.s.node(proposition)["attrs"]["commitment_status"] == "accepted"
    first_projection = apply_situation_consequence(agent, proposition)
    assert first_projection["supported"] is True
    assert len(agent.s.nodes("SituationModelConsequence")) == 1

    # Retraction is a second explicit uptake event over the same proposition;
    # it does not erase the historical projection or mint another one.
    agent.inner.set_attr(proposition, "uptake_signal", "retract")
    agent.inner.run_rules()
    attrs = agent.s.node(proposition)["attrs"]
    assert attrs["commitment_status"] == "retracted"
    assert attrs["uptake_applied"] == "retract"

    after_retraction = apply_situation_consequence(agent, proposition)
    assert after_retraction["supported"] is False
    assert "accepted_uptake" in after_retraction["reason"]
    assert len(agent.s.nodes("SituationModelConsequence")) == 1


def test_retract_without_prior_acceptance_remains_proposed():
    agent = _agent(lifecycle=True)
    result = bridge_proposition_evidence(
        agent, _evidence(evidence_id="phase2s-retract-without-prior",
                         uptake_signal="retract"))
    proposition = result["proposition"]
    agent.inner.run_rules()
    attrs = agent.s.node(proposition)["attrs"]
    assert attrs["commitment_status"] == "proposed"
    assert attrs.get("uptake_applied") is None


@pytest.mark.parametrize("change", [
    {"predicate": "different_predicate"},
    {"polarity": "negated"},
    {"arguments": {"agent": "john", "location": "glass"}},
])
def test_conflicting_replay_by_evidence_id_fails_closed(change):
    agent = _agent()
    first = bridge_proposition_evidence(
        agent, _evidence(evidence_id="phase2s-conflict"))
    assert first["supported"] is True
    before = {
        kind: len(agent.s.nodes(kind))
        for kind in ("Proposition", "PropositionEvidence", "PropositionArgument")
    }

    conflicting = bridge_proposition_evidence(
        agent, _evidence(evidence_id="phase2s-conflict", **change))
    assert conflicting["supported"] is False
    assert conflicting["reason"] == "evidence_id_conflicts_with_existing_proposition"
    assert {
        kind: len(agent.s.nodes(kind))
        for kind in ("Proposition", "PropositionEvidence", "PropositionArgument")
    } == before


@pytest.mark.parametrize("arguments", [
    {"agent": "john", "theme": ["glass", "stone"]},
    [{"role": "theme", "referent": "glass"},
     {"role": "theme", "referent": "stone"}],
])
def test_multi_referent_and_duplicate_role_shapes_are_rejected(arguments):
    agent = _agent()
    result = bridge_proposition_evidence(
        agent,
        _evidence(evidence_id="phase2s-invalid-roles", arguments=arguments),
    )
    assert result["supported"] is False
    assert result["error"] == "unsupported_proposition_evidence"
    assert len(agent.s.nodes("Proposition")) == 0
    assert len(agent.s.nodes("PropositionArgument")) == 0


@pytest.mark.parametrize("grounding_status", [
    "ambiguous",
    "no_world",
    "contradicted",
])
def test_ambiguous_no_world_and_contradicted_frames_do_not_mint_claims(
    grounding_status,
):
    agent = _agent()
    result = agent.ingest_semantic_event(
        {
            "speech_act": "assertion",
            "cognitive_goal": "update_common_ground",
            "grounding_status": grounding_status,
            "grounding_evidence_path": "not_available",
            "topic": "opaque-referent",
        },
        provider="phase2s_neutral_adapter",
        interaction_mode="non_turn",
    )

    interpretation = agent.s.node(result["interpretation_id"])["attrs"]
    event = agent.s.node(result["discourse_event_id"])["attrs"]
    assert interpretation["grounding_status"] == grounding_status
    assert interpretation["grounding_evidence_path"] == "not_available"
    assert event.get("topic") is None
    assert result["proposition"] is None
    assert result["reply"] is None
    assert len(agent.s.nodes("Message")) == 0
    assert len(agent.s.nodes("Proposition")) == 0


def _stable_frame_metadata(agent, result):
    semantic = agent.s.node(result["semantic_frame_id"])["attrs"]
    interpretation = agent.s.node(result["interpretation_id"])["attrs"]
    return {
        "semantic": {
            key: semantic.get(key)
            for key in ("schema", "provider", "speech_act", "cognitive_goal",
                        "grounding_status", "grounding_evidence_path")
        },
        "interpretation": {
            key: interpretation.get(key)
            for key in ("schema", "authority", "status", "event_kind",
                        "evidence_schema", "evidence_provider",
                        "evidence_force", "evidence_goal", "grounding_status",
                        "grounding_evidence_path")
        },
    }


def test_non_turn_and_turn_compatible_ingress_have_equivalent_cognitive_metadata():
    frame = {
        "speech_act": "assertion",
        "cognitive_goal": "update_common_ground",
        "grounding_status": "ambiguous",
        "grounding_evidence_path": "sensor_receipt -> unresolved_referent",
        "topic": "opaque-referent",
    }
    non_turn_agent = _agent()
    turn_compatible_agent = _agent()
    non_turn = non_turn_agent.ingest_semantic_event(
        frame, provider="phase2s_adapter", interaction_mode="non_turn")
    turn_compatible = turn_compatible_agent.ingest_semantic_event(
        frame, provider="phase2s_adapter", interaction_mode="turn_compatible")

    assert _stable_frame_metadata(non_turn_agent, non_turn) == _stable_frame_metadata(
        turn_compatible_agent, turn_compatible)
    assert non_turn["reply"] is None
    assert turn_compatible["reply"] is None
    assert len(non_turn_agent.s.nodes("Message")) == 0
    assert len(turn_compatible_agent.s.nodes("Message")) == 0
    assert (non_turn_agent.s.node(non_turn["discourse_event_id"])["attrs"][
        "interaction_mode"] == "non_turn")
    assert (turn_compatible_agent.s.node(turn_compatible["discourse_event_id"])[
        "attrs"]["interaction_mode"] == "turn_compatible")
