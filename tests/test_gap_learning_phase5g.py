"""Phase 5G: heterogeneous recurring task families under competing pressure.

The families are intentionally opaque graph identities.  Their labels and
routes are test data, not language or conversation heuristics.  This phase
checks that recurrence, priority, repair visibility, review authority, and
route transfer remain local to the cognitive identity that generated them.
"""
from __future__ import annotations

import json
from pathlib import Path

from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
SEEDS = (
    ROOT / "seeds" / "gap_identity.json",
    ROOT / "seeds" / "self_correction_verification_phase5a.json",
    ROOT / "seeds" / "gap_learning_phase5b.json",
    ROOT / "seeds" / "gap_learning_phase5c.json",
    ROOT / "seeds" / "gap_learning_phase5d.json",
)

# Six heterogeneous recurring task families.  The distinct kinds/sources and
# opaque contents prevent accidental conflation while the occurrence counts
# create a deliberately competing priority ordering.
FAMILIES = (
    # Alpha includes one verified pre-corpus observation, so one recurring
    # observation yields the same two-event recurrence pressure as the other
    # families without counting the verified event twice.
    ("knowledge", "task", "family-alpha", 1, "route-alpha"),
    ("planning", "goal", "family-beta", 3, "route-beta"),
    ("perception", "sensor", "family-gamma", 4, "route-gamma"),
    ("control", "action", "family-delta", 5, "route-delta"),
    ("social", "coordination", "family-epsilon", 6, "route-epsilon"),
    ("memory", "recovery", "family-zeta", 7, "route-zeta"),
)


def _agent() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    for path in SEEDS:
        with path.open() as stream:
            agent.inner.load_seed_manifest(json.load(stream), agent.agent)
    return agent


def _identity(kind: str, source: str, content: str) -> str:
    return f"{kind}|{source}|{content}|turn:none"


def _concern(agent, identity: str, content: str, stage: str):
    node = agent.s.add_node("SelfConcern", {
        "status": "noted",
        "source": identity.split("|", 2)[1],
        "kind": identity.split("|", 1)[0],
        "content": content,
        "gap_identity": identity,
        "event_stage": stage,
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", node)
    return node


def _by_identity(agent, node_type: str):
    return {
        agent.s.node(node)["attrs"].get("gap_identity"): node
        for node in agent.s.nodes(node_type)
    }


def test_six_heterogeneous_families_preserve_local_priority_and_learning():
    agent = _agent()
    family_data = []
    priority_history = {content: [] for _, _, content, _, _ in FAMILIES}

    for index, (kind, source, content, occurrences, route) in enumerate(FAMILIES):
        identity = _identity(kind, source, content)

        # One family has a verified cognitive correction available before the
        # recurrence corpus.  This creates the selected-route transfer case;
        # the remaining families have no learned route.
        if index == 0:
            verified = _concern(agent, identity, content, "verified_prior")
            evidence = agent.s.add_node("CorrectionEvidence", {
                "verification_status": "verified",
                "corrected_route": route,
            })
            agent.inner.add_edge_unchecked(verified, "has_correction_evidence", evidence)
            agent.inner.run_rules(3000)

        concerns = []
        for occurrence in range(occurrences):
            concern = _concern(agent, identity, content, f"observation_{occurrence}")
            concerns.append(concern)
            agent.inner.run_rules(3000)
            recurrence = _by_identity(agent, "GapRecurrence")[identity]
            priority_history[content].append(
                agent.s.node(recurrence)["attrs"]["priority"]
            )

        # A failed repair is attached to the first recurring observation and
        # must remain visible in the review graph.
        family_data.append((identity, content, route, concerns))

    agent.inner.run_rules(30000)

    recurrences = _by_identity(agent, "GapRecurrence")
    assessments = _by_identity(agent, "GapLearningAssessment")
    assert set(recurrences) == {
        _identity(kind, source, content)
        for kind, source, content, _, _ in FAMILIES
    }
    assert set(assessments) == set(recurrences)

    # Priority is local and monotonic as evidence accumulates; final values
    # preserve the deliberately competing recurrence pressures.
    for content, history in priority_history.items():
        assert history == sorted(history)
        assert history[-1] >= 2.0
    final_priorities = [
        agent.s.node(recurrences[_identity(kind, source, content)])["attrs"]["priority"]
        for kind, source, content, _, _ in FAMILIES
    ]
    assert final_priorities == [2.0, 3.0, 4.0, 5.0, 6.0, 7.0]

    for identity, content, route, concerns in family_data:
        assessment = assessments[identity]
        attrs = agent.s.node(assessment)["attrs"]
        assert attrs["promotion_status"] == "human_review"
        assert attrs["auto_promoted"] == 0.0
        review = agent.s.neighbours(assessment, "has_human_review")[0]
        failed = agent.s.add_node("RepairAttempt", {
            "verification_status": "failed",
            "repair_route": route,
            "sequence_stage": "failed_repair",
        })
        agent.inner.add_edge_unchecked(review, "has_repair_attempt", failed)

    agent.inner.run_rules(10000)
    assert len(agent.s.nodes("FailedRepairRecord")) == len(FAMILIES)
    assert all(
        agent.s.node(review)["attrs"]["failed_repair_visible"] == 1.0
        for assessment in assessments.values()
        for review in agent.s.neighbours(assessment, "has_human_review")
    )

    selected_identity = _identity(*FAMILIES[0][:3])
    selected_assessment = assessments[selected_identity]
    selected_review = agent.s.neighbours(selected_assessment, "has_human_review")[0]

    # Goals are present while the recurrence is still in the learned state;
    # promotion is a later review transition and must not erase this route
    # transfer evidence.
    selected_goal = agent.s.add_node("Goal", {
        "gap_identity": selected_identity,
        "route": "unresolved_default",
    })
    unrelated_goal = agent.s.add_node("Goal", {
        "gap_identity": _identity(*FAMILIES[1][:3]),
        "route": "unresolved_default",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", selected_goal)
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", unrelated_goal)
    agent.inner.run_rules(10000)
    assert agent.s.node(selected_goal)["attrs"]["route"] == "route-alpha"
    assert agent.s.node(selected_goal)["attrs"]["learning_applied"] == 1.0
    assert agent.s.node(unrelated_goal)["attrs"]["route"] == "unresolved_default"
    assert agent.s.node(unrelated_goal)["attrs"].get("learning_applied") != 1.0

    verified = agent.s.add_node("RepairAttempt", {
        "verification_status": "verified",
        "repair_route": "route-alpha",
        "sequence_stage": "verified_retry",
    })
    agent.inner.add_edge_unchecked(selected_review, "has_repair_attempt", verified)
    agent.inner.set_attr(selected_review, "decision", "approve")
    agent.inner.run_rules(10000)

    # Promotion remains local to the selected review and does not alter the
    # other five families.
    assert agent.s.node(assessments[selected_identity])["attrs"]["promotion_status"] == "promoted"
    assert sum(
        agent.s.node(node)["attrs"]["promotion_status"] == "promoted"
        for node in assessments.values()
    ) == 1
    assert all(
        agent.s.node(node)["attrs"]["promotion_status"] == "human_review"
        for identity, node in assessments.items()
        if identity != selected_identity
    )
