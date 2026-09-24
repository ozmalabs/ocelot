"""Phase 5F: bounded production-scale recurrence and promotion stress.

The corpus is deliberately represented as opaque graph identities and event
stages.  No English surface form participates in recurrence matching.
"""
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
    ROOT / "seeds" / "gap_learning_phase5d.json",
]

# 24 identities x 3 observed stages = 72 historical task/conversation events.
# The identity is intentionally opaque; stage labels are graph evidence only.
PRODUCTION_CASES = tuple(
    {
        # The canonical identity rule derives this from kind/source/content;
        # keep all historical stages on the same cognitive source.
        "identity": f"knowledge|task|opaque-gap-{index:02d}|turn:none",
        "content": f"opaque-gap-{index:02d}",
        "stages": ("conversation", "task_attempt", "task_retry"),
    }
    for index in range(24)
)


def _agent():
    agent = WorldAdapter(seeds=())
    for path in SEEDS:
        with path.open() as fh:
            agent.inner.load_seed_manifest(json.load(fh), agent.agent)
    return agent


def _add_concern(agent, case, stage):
    concern = agent.s.add_node("SelfConcern", {
        "status": "noted",
        "source": "task",
        "kind": "knowledge",
        "content": case["content"],
        "gap_identity": case["identity"],
        "event_stage": stage,
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
    return concern


def test_production_recurrence_stress_keeps_all_gaps_human_gated():
    """A bounded production corpus remains reviewable and never auto-promotes."""
    agent = _agent()
    first_occurrences = {}

    for case in PRODUCTION_CASES:
        first = _add_concern(agent, case, case["stages"][0])
        first_occurrences[case["identity"]] = first
        agent.inner.run_rules(3000)
        evidence = agent.s.add_node("CorrectionEvidence", {
            "verification_status": "failed",
            "corrected_route": "grounded_retrieval",
        })
        agent.inner.add_edge_unchecked(first, "has_correction_evidence", evidence)
        agent.inner.run_rules(3000)
        for stage in case["stages"][1:]:
            _add_concern(agent, case, stage)
            agent.inner.run_rules(3000)

    # The bounded per-identity fixpoints above have now produced the complete
    # production-shaped graph; this pass verifies the aggregate state.
    agent.inner.run_rules(30000)

    recurrences = {
        agent.s.node(node)["attrs"]["gap_identity"]: node
        for node in agent.s.nodes("GapRecurrence")
    }
    assessments = {
        agent.s.node(node)["attrs"]["gap_identity"]: node
        for node in agent.s.nodes("GapLearningAssessment")
    }
    expected = {case["identity"] for case in PRODUCTION_CASES}
    assert set(recurrences) == expected
    assert set(assessments) == expected
    assert len(agent.s.nodes("GapRecurrence")) == len(PRODUCTION_CASES)
    assert len(agent.s.nodes("GapLearningAssessment")) == len(PRODUCTION_CASES)

    for identity in expected:
        recurrence = agent.s.node(recurrences[identity])["attrs"]
        assessment = agent.s.node(assessments[identity])["attrs"]
        # The assessment snapshots the first recurrence threshold; the graph
        # still retains all three historical concerns below.
        assert recurrence["recurrence_count"] >= 2.0
        assert assessment["recurrence_count"] >= 2.0
        assert assessment["failed_repair_count"] == 1.0
        assert assessment["promotion_status"] == "human_review"
        assert assessment["auto_promoted"] == 0.0
        assert agent.s.node(first_occurrences[identity])["attrs"]["correction_outcome"] == "failed"
        assert len([
            node for node in agent.s.nodes("SelfConcern")
            if agent.s.node(node)["attrs"].get("gap_identity") == identity
        ]) == 3

        # Add the production review's failed repair attempt only after the
        # assessment exists, mirroring the real review/repair lifecycle.
        review = agent.s.neighbours(assessments[identity], "has_human_review")[0]
        attempt = agent.s.add_node("RepairAttempt", {
            "verification_status": "failed",
            "repair_route": "grounded_retrieval",
            "sequence_stage": "review_repair",
        })
        agent.inner.add_edge_unchecked(review, "has_repair_attempt", attempt)
    agent.inner.run_rules(10000)

    # Failed repair remains visible at corpus scale, with no automatic
    # standing concern, promotion, or closure.
    assert len(agent.s.nodes("FailedRepairRecord")) == len(PRODUCTION_CASES)
    assert agent.s.nodes("StandingConcern") == []
    assert all(
        agent.s.node(node)["attrs"]["status"] == "open"
        for node in recurrences.values()
    )

    # An explicit human decision changes exactly one item; replay does not
    # promote the remaining 23 or manufacture another assessment.
    selected = assessments[PRODUCTION_CASES[0]["identity"]]
    review = agent.s.neighbours(selected, "has_human_review")[0]
    verified = agent.s.add_node("RepairAttempt", {
        "verification_status": "verified",
        "repair_route": "grounded_retrieval",
        "sequence_stage": "verified_retry",
    })
    agent.inner.add_edge_unchecked(review, "has_repair_attempt", verified)
    agent.inner.run_rules(5000)
    agent.inner.set_attr(review, "decision", "approve")
    agent.inner.run_rules(5000)
    assert agent.s.node(selected)["attrs"]["promotion_status"] == "promoted"
    assert sum(
        agent.s.node(node)["attrs"]["promotion_status"] == "promoted"
        for node in assessments.values()
    ) == 1
    assert len(agent.s.nodes("GapLearningAssessment")) == len(PRODUCTION_CASES)

    # A separate explicit retirement is also local and review-authorized.
    retired = assessments[PRODUCTION_CASES[1]["identity"]]
    retired_review = agent.s.neighbours(retired, "has_human_review")[0]
    agent.inner.set_attr(retired_review, "decision", "retire")
    agent.inner.run_rules(5000)
    assert agent.s.node(retired)["attrs"]["promotion_status"] == "retired"
    assert sum(
        agent.s.node(node)["attrs"]["promotion_status"] == "retired"
        for node in assessments.values()
    ) == 1
