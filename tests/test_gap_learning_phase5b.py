"""Phase 5B: recurrence identity, priority, and future-route application."""
from __future__ import annotations

import json
from pathlib import Path

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [
    ROOT / "seeds" / "gap_identity.json",
    ROOT / "seeds" / "self_correction_verification_phase5a.json",
    ROOT / "seeds" / "gap_learning_phase5b.json",
]


def _agent():
    agent = WorldAdapter(seeds=())
    for path in SEEDS:
        with path.open() as fh:
            agent.inner.load_seed_manifest(json.load(fh), agent.agent)
    return agent


def test_corrected_identity_recurs_once_and_routes_future_goal():
    agent = _agent()
    identity = "knowledge|implicit|phase5b topic|turn:none"
    first = agent.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": "knowledge",
        "content": "phase5b topic", "gap_identity": identity,
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", first)
    agent.inner.run_rules(1000)

    recs = [n for n in agent.s.nodes("GapRecurrence")
            if agent.s.node(n)["attrs"].get("gap_identity") ==
            identity]
    assert len(recs) == 1
    rec = recs[0]
    assert agent.s.node(rec)["attrs"]["recurrence_count"] == 1.0
    assert agent.s.node(rec)["attrs"]["priority"] == 1.0

    evidence = agent.s.add_node("CorrectionEvidence", {
        "verification_status": "verified", "corrected_route": "grounded_retrieval",
    })
    agent.inner.add_edge_unchecked(first, "has_correction_evidence", evidence)
    agent.inner.run_rules(1000)

    goal = agent.s.add_node("Goal", {
            "gap_identity": identity,
        "route": "unresolved_default", "status": "pending",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.run_rules(1000)

    goal_attrs = agent.s.node(goal)["attrs"]
    assert goal_attrs["route"] == "grounded_retrieval"
    assert goal_attrs["learning_applied"] == 1.0
    assert sum(
        agent.s.node(n)["attrs"].get("gap_identity") == identity
        for n in agent.s.nodes("SelfConcern")
    ) == 1


def test_recurrence_priority_counts_distinct_same_identity_concerns():
    agent = _agent()
    identity = "knowledge|implicit|phase5b topic|turn:none"
    for turn in (1, 2):
        concern = agent.s.add_node("SelfConcern", {
            "status": "noted", "source": "implicit", "kind": "knowledge",
            "content": "phase5b topic", "gap_identity": identity,
        })
        agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
        agent.inner.run_rules(1000)
        if turn == 1:
            # A later occurrence is not a second active concern: the first
            # occurrence has been closed, while its identity remains usable
            # as recurrence evidence.
            agent.s.node(concern)["attrs"]["status"] = "resolved"
    recs = [n for n in agent.s.nodes("GapRecurrence")
            if agent.s.node(n)["attrs"].get("gap_identity") == identity]
    assert len(recs) == 1
    attrs = agent.s.node(recs[0])["attrs"]
    assert attrs["recurrence_count"] == 2.0
    assert attrs["priority"] == 2.0
