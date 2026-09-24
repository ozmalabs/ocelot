"""Phase 5C: recurrence pressure, failed repair visibility, and supervised promotion."""
from __future__ import annotations

import json
from pathlib import Path

from substrate.world_adapter import WorldAdapter

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [
    ROOT / "seeds" / "gap_identity.json",
    ROOT / "seeds" / "self_correction_verification_phase5a.json",
    ROOT / "seeds" / "gap_learning_phase5b.json",
    ROOT / "seeds" / "gap_learning_phase5c.json",
]


def _agent():
    agent = WorldAdapter(seeds=())
    for path in SEEDS:
        with path.open() as fh:
            agent.inner.load_seed_manifest(json.load(fh), agent.agent)
    return agent


def _concern(agent, identity, content):
    concern = agent.s.add_node("SelfConcern", {
        "status": "noted", "source": "implicit", "kind": "knowledge",
        "content": content, "gap_identity": identity,
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
    return concern


def test_recurrence_battery_surfaces_failed_repair_without_duplicate_concerns():
    agent = _agent()
    identity = "knowledge|implicit|phase5c-battery|turn:none"
    first = _concern(agent, identity, "phase5c-battery")
    failed_evidence = agent.s.add_node("CorrectionEvidence", {
        "verification_status": "failed", "corrected_route": "grounded_retrieval",
    })
    agent.inner.add_edge_unchecked(first, "has_correction_evidence", failed_evidence)
    agent.inner.run_rules(2000)

    # The second occurrence is a new historical fact, not a second active
    # unresolved concern. The identity remains the recurrence key.
    second = _concern(agent, identity, "phase5c-battery")
    agent.inner.run_rules(2000)

    concerns = [n for n in agent.s.nodes("SelfConcern")
                if agent.s.node(n)["attrs"].get("gap_identity") == identity]
    assert len(concerns) == 2
    assert len({agent.s.node(n)["attrs"].get("gap_identity") for n in concerns}) == 1

    recs = [n for n in agent.s.nodes("GapRecurrence")
            if agent.s.node(n)["attrs"].get("gap_identity") == identity]
    assert len(recs) == 1
    assert agent.s.node(recs[0])["attrs"]["recurrence_count"] == 2.0

    records = [agent.s.node(n)["attrs"] for n in agent.s.nodes("CorrectionRecord")
               if agent.s.node(n)["attrs"].get("outcome") == "failed"]
    assert len(records) == 1
    assert agent.s.node(first)["attrs"]["status"] == "noted"
    assert agent.s.node(first)["attrs"]["correction_outcome"] == "failed"

    assessments = [n for n in agent.s.nodes("GapLearningAssessment")
                   if agent.s.node(n)["attrs"].get("gap_identity") == identity]
    assert len(assessments) == 1
    assessment = agent.s.node(assessments[0])["attrs"]
    assert assessment["recurrence_count"] == 2.0
    assert assessment["failed_repair_count"] == 1.0
    assert assessment["promotion_status"] == "human_review"
    assert assessment["auto_promoted"] == 0.0
    assert agent.s.nodes("StandingConcern") == []


def test_assessment_is_idempotent_under_resource_heavy_replay():
    agent = _agent()
    identities = [f"knowledge|implicit|phase5c-{i}|turn:none" for i in range(8)]
    for identity in identities:
        _concern(agent, identity, identity.rsplit("|", 2)[1])
        agent.inner.run_rules(2000)
        _concern(agent, identity, identity.rsplit("|", 2)[1])
        # Let each identity cross the assessment threshold in its own graph
        # fixpoint before adding the next one; this is the resource-heavy
        # replay shape and avoids treating same-pass rule matches as a
        # persistence guarantee.
        agent.inner.run_rules(2000)
    agent.inner.run_rules(8000)
    agent.inner.run_rules(8000)

    assessments = [agent.s.node(n)["attrs"] for n in agent.s.nodes("GapLearningAssessment")]
    assert len(assessments) == len(identities)
    assert {a["gap_identity"] for a in assessments} == set(identities)
    assert all(a["promotion_status"] == "human_review" for a in assessments)
    assert all(a["auto_promoted"] == 0.0 for a in assessments)
