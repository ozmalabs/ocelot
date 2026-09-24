"""Focused Phase 5A gate for graph-native verified self-correction."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "self_correction_verification_phase5a.json"


@pytest.fixture()
def agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    with SEED.open() as fh:
        a.inner.load_seed_manifest(json.load(fh), a.agent)
    return a


def _mint_case(agent, verification_status):
    concern = agent.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": "knowledge",
        "content": "original assertion remains recorded", "gap_identity": "knowledge|implicit|x|turn:7",
    })
    evidence = agent.s.add_node("CorrectionEvidence", {
        "verification_status": verification_status, "corrected_route": "grounded_retrieval",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
    agent.inner.add_edge_unchecked(concern, "has_correction_evidence", evidence)
    agent.inner.run_rules(1000)
    return concern


def test_verified_correction_updates_future_route_without_rewriting_original(agent):
    concern = _mint_case(agent, "verified")
    attrs = agent.s.node(concern)["attrs"]

    assert attrs["status"] == "resolved"
    assert attrs["correction_outcome"] == "verified"
    assert attrs["content"] == "original assertion remains recorded"
    records = [agent.s.node(n)["attrs"] for n in agent.s.nodes("CorrectionRecord")]
    assert len(records) == 1
    assert records[0]["original_content"] == attrs["content"]
    assert records[0]["outcome"] == "verified"
    models = [agent.s.node(n)["attrs"] for n in agent.s.nodes("RouteModel")]
    assert models == [{
        "schema": "route_model.v1", "model_layer": 2.0,
        "route": "grounded_retrieval", "source_outcome": "verified",
    }]


def test_failed_correction_is_recorded_but_remains_open_and_idempotent(agent):
    concern = _mint_case(agent, "failed")
    attrs = agent.s.node(concern)["attrs"]

    assert attrs["status"] == "noted"
    assert attrs["correction_outcome"] == "failed"
    assert agent.s.nodes("RouteModel") == []
    assert len(agent.s.nodes("CorrectionRecord")) == 1
    agent.inner.run_rules(1000)
    assert len(agent.s.nodes("CorrectionRecord")) == 1

