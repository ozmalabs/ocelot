"""Phase 5E: real conversation/task sequence through the supervised gap gate."""
from __future__ import annotations

import pytest

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter

@pytest.fixture()
def agent(monkeypatch):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    # Keep the unresolved-topic branch deterministic; this changes only the
    # test world's external retrieval datum, not the conversation rules.
    import domains.topic_grounding as topic_grounding
    monkeypatch.setattr(topic_grounding, "ground_topic", lambda *_a, **_k: None)
    # Keep the real conversation ingress. The full boot already loads the
    # Phase 5 overlay; loading these manifests a second time would duplicate
    # the production rules and make the sequence test exercise a different
    # graph than the live runtime.
    return agent


def _attrs(agent, node_type):
    return [agent.s.node(n)["attrs"] for n in agent.s.nodes(node_type)]


def _conversation_concern(agent):
    before = set(agent.s.nodes("SelfConcern"))
    reply = agent.converse(
        "What do you know about phase5e_unknown?",
        speech_act="question",
    )
    agent.comprehend()
    assert reply
    created = [n for n in agent.s.nodes("SelfConcern") if n not in before]
    concerns = [
        n for n in created
        if agent.s.node(n)["attrs"].get("content") == "phase5e_unknown"
    ]
    assert len(concerns) == 1
    attrs = agent.s.node(concerns[0])["attrs"]
    assert attrs["source"] == "implicit"
    assert attrs["gap_identity_schema"] == "gap_identity.v1"
    assert attrs["gap_identity"].split("|turn:", 1)[1].isdigit()
    return concerns[0]


def test_real_conversation_concern_enters_human_gated_promotion(agent):
    """A live unresolved conversation event is only eligible for review."""
    concern = _conversation_concern(agent)
    identity = agent.s.node(concern)["attrs"]["gap_identity"]

    assessments = [a for a in _attrs(agent, "GapLearningAssessment")
                   if a.get("gap_identity") == identity]
    assert assessments == [], "one occurrence is not recurrence pressure"
    assert not [a for a in _attrs(agent, "StandingConcern")
                 if a.get("gap_identity") == identity]

    # This is the explicit human action. converse() itself must not promote.
    import jabberwock_daemon as daemon

    result = daemon.promote_self_concern(agent, str(concern.value))
    assert result["ok"]
    standing = [s for s in _attrs(agent, "StandingConcern")
                if s.get("name") == f"promoted_self_concern_{concern.value}"]
    assert len(standing) == 1
    assert standing[0]["status"] == "pending"
    assert agent.s.node(concern)["attrs"]["status"] == "promoted"


def test_task_recurrence_runs_failed_repair_then_two_explicit_human_outcomes(agent):
    """Two task events share identity; failure stays visible until a human acts."""
    identity = "knowledge|task|phase5e-repeated-task|turn:none"
    episode = agent.s.add_node("TaskEpisode", {
        "task_identity": identity,
        "sequence": "conversation -> task_attempt -> repair_attempt",
    })

    # Historical observations are graph data for one task sequence. The
    # identity is opaque and stable; no surface-language matching is used.
    for step in ("conversation", "task_retry"):
        concern = agent.s.add_node("SelfConcern", {
            "status": "noted", "source": "task", "kind": "knowledge",
            "content": "phase5e-repeated-task", "gap_identity": identity,
            "event_stage": step,
        })
        agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
        agent.inner.add_edge_unchecked(concern, "belongs_to_task", episode)
        agent.inner.run_rules(3000)

    assessment = next(a for a in agent.s.nodes("GapLearningAssessment")
                       if agent.s.node(a)["attrs"].get("gap_identity") == identity)
    review = agent.s.neighbours(assessment, "has_human_review")[0]
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "human_review"
    assert agent.s.node(review)["attrs"]["decision"] == "pending"

    failed = agent.s.add_node("RepairAttempt", {
        "verification_status": "failed", "repair_route": "grounded_retrieval",
        "sequence_stage": "repair_attempt",
    })
    agent.inner.add_edge_unchecked(review, "has_repair_attempt", failed)
    agent.inner.run_rules(3000)
    assert agent.s.node(failed)["attrs"]["failure_recorded"] == 1.0
    assert agent.s.node(review)["attrs"]["failed_repair_visible"] == 1.0
    assert agent.s.node(review)["attrs"]["review_status"] == "open"
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "human_review"
    assert agent.s.nodes("FailedRepairRecord")

    # A verified retry is still inert until the human approves it.
    verified = agent.s.add_node("RepairAttempt", {
        "verification_status": "verified", "repair_route": "grounded_retrieval",
        "sequence_stage": "verified_retry",
    })
    agent.inner.add_edge_unchecked(review, "has_repair_attempt", verified)
    agent.inner.run_rules(3000)
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "human_review"
    assert agent.s.node(review)["attrs"]["review_status"] == "open"

    # Explicit approval is the only route to promotion.
    agent.inner.set_attr(review, "decision", "approve")
    agent.inner.run_rules(3000)
    recurrence = agent.s.neighbours(assessment, "assesses_recurrence")[0]
    assert agent.s.node(recurrence)["attrs"]["status"] == "promoted"
    assert agent.s.node(recurrence)["attrs"]["promotion_authority"] == "human_review"
    assert agent.s.node(assessment)["attrs"]["promotion_status"] == "promoted"
    assert agent.s.node(review)["attrs"]["review_status"] == "promoted"

    # A separate repeated task reaches retirement only by another explicit
    # human decision; recurrence and failed repair never imply retirement.
    retire_identity = "knowledge|task|phase5e-retired-task|turn:none"
    for stage in ("conversation", "task_retry"):
        concern = agent.s.add_node("SelfConcern", {
            "status": "noted", "source": "task", "kind": "knowledge",
            "content": "phase5e-retired-task", "gap_identity": retire_identity,
        })
        agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
        agent.inner.run_rules(3000)
    retired_assessment = next(a for a in agent.s.nodes("GapLearningAssessment")
                              if agent.s.node(a)["attrs"].get("gap_identity") == retire_identity)
    retired_review = agent.s.neighbours(retired_assessment, "has_human_review")[0]
    agent.inner.set_attr(retired_review, "decision", "retire")
    agent.inner.run_rules(3000)
    retired_recurrence = agent.s.neighbours(retired_assessment, "assesses_recurrence")[0]
    assert agent.s.node(retired_recurrence)["attrs"]["status"] == "retired"
    assert agent.s.node(retired_recurrence)["attrs"]["retirement_authority"] == "human_review"
    assert agent.s.node(retired_assessment)["attrs"]["promotion_status"] == "retired"
