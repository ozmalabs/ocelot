"""Native proposition uptake lifecycle: explicit signals only."""
from __future__ import annotations

import os
import sys

import pytest

pytest.importorskip("substrate_rs")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from domains.proposition_commitment import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA,
    bridge_proposition_evidence,
)


def _agent():
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    a.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), a.agent)
    return a


def _evidence(evidence_id="lifecycle-1"):
    return {
        "schema": EVIDENCE_SCHEMA,
        "kind": EVIDENCE_KIND,
        "predicate": "state_open",
        "arguments": {"theme": "gate"},
        "polarity": "affirmed",
        "provider": "neutral_adapter",
        "evidence_id": evidence_id,
        "commitment_status": "proposed",
    }


def _proposition(agent, evidence_id="lifecycle-1"):
    result = bridge_proposition_evidence(agent, _evidence(evidence_id))
    assert result["supported"] is True
    return result["proposition"]


def test_native_lifecycle_requires_explicit_uptake_signal():
    agent = _agent()
    proposition = _proposition(agent)
    agent.inner.run_rules()
    assert agent.s.node(proposition)["attrs"]["commitment_status"] == "proposed"

    agent.inner.set_attr(proposition, "uptake_signal", "accept")
    agent.inner.run_rules()
    attrs = agent.s.node(proposition)["attrs"]
    assert attrs["commitment_status"] == "accepted"
    assert attrs["uptake_applied"] == "accept"

    # The same native signal is idempotent and does not mint a second record.
    agent.inner.run_rules()
    assert len(agent.s.nodes("Proposition")) == 1


@pytest.mark.parametrize("signal,expected", [
    ("challenge", "challenged"),
    ("suspend", "suspended"),
])
def test_native_lifecycle_has_distinct_challenge_and_suspend(signal, expected):
    agent = _agent()
    proposition = _proposition(agent, evidence_id=f"lifecycle-{signal}")
    agent.inner.set_attr(proposition, "uptake_signal", signal)
    agent.inner.run_rules()
    assert agent.s.node(proposition)["attrs"]["commitment_status"] == expected


def test_native_retraction_requires_prior_live_commitment():
    agent = _agent()
    proposed = _proposition(agent, evidence_id="lifecycle-proposed")
    agent.inner.set_attr(proposed, "uptake_signal", "retract")
    agent.inner.run_rules()
    assert agent.s.node(proposed)["attrs"]["commitment_status"] == "proposed"

    accepted = _proposition(agent, evidence_id="lifecycle-accepted")
    agent.inner.set_attr(accepted, "uptake_signal", "accept")
    agent.inner.run_rules()
    agent.inner.set_attr(accepted, "uptake_signal", "retract")
    agent.inner.run_rules()
    attrs = agent.s.node(accepted)["attrs"]
    assert attrs["commitment_status"] == "retracted"
    assert attrs["uptake_applied"] == "retract"


def test_native_lifecycle_ignores_status_only_and_invalid_signal():
    agent = _agent()
    proposition = _proposition(agent, evidence_id="lifecycle-invalid")
    agent.inner.set_attr(proposition, "commitment_status", "accepted")
    agent.inner.run_rules()
    assert agent.s.node(proposition)["attrs"].get("uptake_applied") is None
    agent.inner.set_attr(proposition, "commitment_status", "proposed")
    agent.inner.set_attr(proposition, "uptake_signal", "approve")
    agent.inner.run_rules()
    attrs = agent.s.node(proposition)["attrs"]
    assert attrs["commitment_status"] == "proposed"
    assert attrs.get("uptake_applied") is None
