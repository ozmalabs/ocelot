"""Neutral, event-compatible semantic ingress tests."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")

from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from domains.proposition_commitment import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA,
    apply_situation_consequence,
)


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    return a


def test_semantic_event_ingress_is_not_a_turn_or_message(agent):
    before_messages = len(agent.s.nodes("Message"))
    result = agent.ingest_semantic_event(
        {
            "speech_act": "assertion",
            "communicative_force": "assertion_or_correction",
            "cognitive_goal": "update_common_ground",
            "grounding_status": "candidate_grounded",
            "grounding_evidence_path": "sensor_receipt -> gate_state",
            "topic": "gate",
        },
        provider="synthetic_semantic_adapter",
        interaction_mode="non_turn",
    )

    assert len(agent.s.nodes("Message")) == before_messages
    interpretation = agent.s.node(result["interpretation_id"])["attrs"]
    event = agent.s.node(result["discourse_event_id"])["attrs"]
    assert interpretation["event_kind"] == "semantic_event"
    assert interpretation["interaction_mode"] == "non_turn"
    assert interpretation["evidence_provider"] == "synthetic_semantic_adapter"
    assert interpretation["communicative_force"] == "assertion_or_correction"
    assert interpretation["cognitive_goal"] == "update_common_ground"
    assert event["interaction_mode"] == "non_turn"
    assert result["reply"] is None


def test_semantic_event_ingress_preserves_neutral_proposition_payload(agent):
    result = agent.ingest_semantic_event(
        {
            "communicative_force": "assertion_or_correction",
            "cognitive_goal": "update_common_ground",
            "proposition": {
                "schema": "proposition_evidence.v1",
                "predicate": "state_open",
                "arguments": [
                    {"role": "theme", "referent": "gate"},
                ],
                "polarity": "positive",
            },
        },
        provider="semantic_adapter:non_english",
        interaction_mode="asynchronous",
    )
    attrs = agent.s.node(result["interpretation_id"])["attrs"]
    assert attrs["evidence_proposition"]["predicate"] == "state_open"
    assert attrs["interaction_mode"] == "asynchronous"
    assert agent.s.node(result["discourse_event_id"])["attrs"][
        "interaction_mode"] == "asynchronous"


def test_semantic_event_rejects_surface_or_non_mapping_input(agent):
    with pytest.raises(TypeError):
        agent.ingest_semantic_event("The gate is open.", provider="english")
    with pytest.raises(ValueError):
        agent.ingest_semantic_event(
            {"communicative_force": "unsupported"}, provider="adapter")


def test_semantic_event_uses_existing_proposition_bridge_without_uptake(agent):
    proposition = {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "predicate": "state_open",
        "arguments": {"theme": "gate"},
        "polarity": "affirmed",
        "provider": "non_turn_semantic_adapter",
        "evidence_id": "event-001",
        "commitment_status": "proposed",
    }
    result = agent.ingest_semantic_event(
        {
            "communicative_force": "assertion_or_correction",
            "cognitive_goal": "update_common_ground",
            "proposition": proposition,
        },
        provider="non_turn_semantic_adapter",
        interaction_mode="asynchronous",
    )
    assert result["proposition"]["supported"] is True
    pid = result["proposition"]["proposition"]
    pattrs = agent.s.node(pid)["attrs"]
    assert pattrs["commitment_status"] == "proposed"
    assert agent.s.has_edge(pid, "originated_in",
                            result["discourse_event_id"])
    assert not agent.s.has_edge(
        result["discourse_state_id"], "accepted_claim", pid)


def test_non_turn_event_to_proposition_to_native_uptake_to_situation_model(agent):
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    result = agent.ingest_semantic_event(
        {
            "communicative_force": "assertion_or_correction",
            "cognitive_goal": "update_common_ground",
            "proposition": {
                "schema": EVIDENCE_SCHEMA,
                "kind": EVIDENCE_KIND,
                "predicate": "drop",
                "arguments": {"agent": "john", "theme": "glass"},
                "polarity": "affirmed",
                "provider": "non_turn_semantic_adapter",
                "evidence_id": "event-chain-001",
                "commitment_status": "proposed",
                "uptake_signal": "accept",
            },
        },
        provider="non_turn_semantic_adapter",
        interaction_mode="asynchronous",
    )
    pid = result["proposition"]["proposition"]
    agent.inner.run_rules()
    assert agent.s.node(pid)["attrs"]["commitment_status"] == "accepted"
    consequence = apply_situation_consequence(agent, pid)
    assert consequence["supported"] is True
    assert consequence["ingest"]["state"].get("on_floor") == 1
    assert result["reply"] is None
