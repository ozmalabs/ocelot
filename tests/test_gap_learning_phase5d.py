"""Phase 5D: actual recurrence -> review -> repair -> verification -> decision."""
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


def _agent():
    agent = WorldAdapter(seeds=())
    for path in SEEDS:
        with path.open() as fh:
            agent.inner.load_seed_manifest(json.load(fh), agent.agent)
    return agent


def _assessment(agent, identity):
    return next(n for n in agent.s.nodes("GapLearningAssessment")
                if agent.s.node(n)["attrs"].get("gap_identity") == identity)


def _seed_recurrence(agent, identity):
    first = None
    for content in ("task recurrence", "task recurrence"):
        concern = agent.s.add_node("SelfConcern", {
            "status": "noted", "source": "task", "kind": "knowledge",
            "content": content, "gap_identity": identity,
        })
        agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
        agent.inner.run_rules(3000)
        if first is None:
            first = concern
            evidence = agent.s.add_node("CorrectionEvidence", {
                "verification_status": "failed", "corrected_route": "grounded_retrieval",
            })
            agent.inner.add_edge_unchecked(first, "has_correction_evidence", evidence)
            agent.inner.run_rules(3000)


def test_failed_attempt_stays_visible_without_closure():
    agent = _agent()
    identity = "knowledge|task|task recurrence|turn:none"
    _seed_recurrence(agent, identity)
    assessment = _assessment(agent, identity)
    review = agent.s.neighbours(assessment, "has_human_review")[0]
    attempt = agent.s.add_node("RepairAttempt", {
        "verification_status": "failed", "repair_route": "grounded_retrieval",
    })
    agent.inner.add_edge_unchecked(review, "has_repair_attempt", attempt)
    agent.inner.run_rules(3000)

    assert agent.s.node(attempt)["attrs"]["failure_recorded"] == 1.0
    assert agent.s.node(review)["attrs"]["failed_repair_visible"] == 1.0
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "human_review"
    assert agent.s.nodes("FailedRepairRecord")
    assert agent.s.node(review)["attrs"]["review_status"] == "open"


def test_verified_repair_promotes_only_after_explicit_approval():
    agent = _agent()
    identity = "knowledge|task|task recurrence|turn:none"
    _seed_recurrence(agent, identity)
    assessment = _assessment(agent, identity)
    review = agent.s.neighbours(assessment, "has_human_review")[0]
    attempt = agent.s.add_node("RepairAttempt", {
        "verification_status": "verified", "repair_route": "grounded_retrieval",
    })
    agent.inner.add_edge_unchecked(review, "has_repair_attempt", attempt)
    agent.inner.run_rules(3000)
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "human_review"
    assert agent.s.node(review)["attrs"]["review_status"] == "open"

    agent.inner.set_attr(review, "decision", "approve")
    agent.inner.run_rules(3000)
    rec = agent.s.neighbours(assessment, "assesses_recurrence")[0]
    assert agent.s.node(review)["attrs"]["review_status"] == "promoted"
    assert agent.s.node(rec)["attrs"]["status"] == "promoted"
    assert agent.s.node(rec)["attrs"]["promotion_authority"] == "human_review"
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "promoted"


def test_retirement_requires_explicit_human_decision():
    agent = _agent()
    identity = "knowledge|task|task recurrence|turn:none"
    _seed_recurrence(agent, identity)
    assessment = _assessment(agent, identity)
    review = agent.s.neighbours(assessment, "has_human_review")[0]
    rec = agent.s.neighbours(assessment, "assesses_recurrence")[0]
    agent.inner.run_rules(3000)
    assert agent.s.node(rec)["attrs"]["status"] == "open"
    agent.inner.set_attr(review, "decision", "retire")
    agent.inner.run_rules(3000)
    assert agent.s.node(rec)["attrs"]["status"] == "retired"
    assert agent.s.node(rec)["attrs"]["retirement_authority"] == "human_review"
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "retired"
