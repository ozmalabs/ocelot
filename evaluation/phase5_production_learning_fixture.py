"""Phase 5 follow-up: explicit production-shaped learning observations.

The fixed communication corpus has no learning-stage contract.  This fixture
provides that contract explicitly and feeds the existing SelfConcern,
GapRecurrence, and GapLearningAssessment authorities.  It is deliberately
not a conversation learner: identity and verification are supplied as typed
evidence, while native rules own recurrence and review state.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from substrate.world_adapter import WorldAdapter


SCHEMA = "phase5-production-learning-fixture.v1"
PROTOCOL_ID = "phase5h-explicit-learning-observations-v1"
ROOT = Path(__file__).resolve().parents[1]
SEEDS = (
    ROOT / "seeds" / "gap_identity.json",
    ROOT / "seeds" / "self_correction_verification_phase5a.json",
    ROOT / "seeds" / "gap_learning_phase5b.json",
    ROOT / "seeds" / "gap_learning_phase5c.json",
    ROOT / "seeds" / "gap_learning_phase5d.json",
)

FIXTURE: tuple[dict[str, Any], ...] = (
    {
        "event_id": "learning-alpha-observation-1",
        "gap_identity": "knowledge|task|opaque-alpha|turn:none",
        "kind": "knowledge",
        "source": "task",
        "content": "opaque-alpha",
        "learning_stage": "observed",
        "verification_status": "unverified",
        "event_stage": "initial_observation",
    },
    {
        "event_id": "learning-alpha-observation-2",
        "gap_identity": "knowledge|task|opaque-alpha|turn:none",
        "kind": "knowledge",
        "source": "task",
        "content": "opaque-alpha",
        "learning_stage": "recurrent",
        "verification_status": "unverified",
        "event_stage": "repeated_observation",
    },
    {
        "event_id": "learning-beta-observation-1",
        "gap_identity": "planning|goal|opaque-beta|turn:none",
        "kind": "planning",
        "source": "goal",
        "content": "opaque-beta",
        "learning_stage": "observed",
        "verification_status": "unverified",
        "event_stage": "initial_observation",
    },
    {
        "event_id": "learning-beta-observation-2",
        "gap_identity": "planning|goal|opaque-beta|turn:none",
        "kind": "planning",
        "source": "goal",
        "content": "opaque-beta",
        "learning_stage": "recurrent",
        "verification_status": "unverified",
        "event_stage": "repeated_observation",
    },
)


def _node_id(node: Any) -> int:
    return int(node.value)


def _attrs(agent: WorldAdapter, node: Any) -> dict[str, Any]:
    return dict(agent.s.node(node)["attrs"])


def _load_authorities(agent: WorldAdapter) -> None:
    for path in SEEDS:
        with path.open(encoding="utf-8") as stream:
            agent.inner.load_seed_manifest(json.load(stream), agent.agent)


def _ingest(agent: WorldAdapter, event: Mapping[str, Any]) -> Any:
    # Mechanical typed-evidence materialization.  The identity is accepted
    # only because the fixture supplies the full learning observation schema;
    # no text normalization or repeated-surface comparison occurs here.
    concern = agent.s.add_node("SelfConcern", {
        "status": "noted",
        "gap_identity_schema": "gap_identity.v1",
        "gap_identity": event["gap_identity"],
        "kind": event["kind"],
        "source": event["source"],
        "content": event["content"],
        "event_id": event["event_id"],
        "event_stage": event["event_stage"],
        "learning_stage": event["learning_stage"],
        "verification_status": event["verification_status"],
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_self_concern", concern)
    agent.inner.run_rules(10000)
    return concern


def _identity_nodes(agent: WorldAdapter, node_type: str) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = {}
    for node in agent.s.nodes(node_type):
        identity = _attrs(agent, node).get("gap_identity")
        if identity not in (None, ""):
            grouped.setdefault(str(identity), []).append(node)
    return grouped


def measure_fixture(
    fixture: tuple[Mapping[str, Any], ...] = FIXTURE,
) -> dict[str, Any]:
    agent = WorldAdapter(seeds=())
    _load_authorities(agent)
    observations: list[dict[str, Any]] = []
    for event in fixture:
        concern = _ingest(agent, event)
        observations.append({
            "event_id": event["event_id"],
            "gap_identity": event["gap_identity"],
            "learning_stage": event["learning_stage"],
            "verification_status": event["verification_status"],
            "self_concern_node_id": _node_id(concern),
        })

    recurrences = _identity_nodes(agent, "GapRecurrence")
    assessments = _identity_nodes(agent, "GapLearningAssessment")
    reviews: dict[str, Any] = {}
    for identity, assessment_nodes in assessments.items():
        if assessment_nodes:
            review_nodes = list(agent.inner.neighbours(
                assessment_nodes[0], "has_human_review"))
            if review_nodes:
                reviews[identity] = review_nodes[0]
                failed = agent.s.add_node("RepairAttempt", {
                    "verification_status": "failed",
                    "repair_route": f"repair:{identity}",
                    "sequence_stage": "failed_repair",
                })
                agent.inner.add_edge_unchecked(
                    review_nodes[0], "has_repair_attempt", failed)
    agent.inner.run_rules(10000)

    # One explicit human decision closes one verified retry.  The decision is
    # fixture evidence, not a Python-selected learning outcome; native rules
    # own promotion and leave the other identity at review.
    promoted_identity = "knowledge|task|opaque-alpha|turn:none"
    if promoted_identity in reviews:
        verified = agent.s.add_node("RepairAttempt", {
            "verification_status": "verified",
            "repair_route": "route:opaque-alpha",
            "sequence_stage": "verified_retry",
        })
        agent.inner.add_edge_unchecked(
            reviews[promoted_identity], "has_repair_attempt", verified)
        agent.inner.set_attr(reviews[promoted_identity], "decision", "approve")
        agent.inner.run_rules(10000)

    identities = []
    for identity in sorted({str(item["gap_identity"]) for item in observations}):
        recurrence = recurrences.get(identity, [])
        assessment = assessments.get(identity, [])
        ra = _attrs(agent, recurrence[0]) if recurrence else {}
        aa = _attrs(agent, assessment[0]) if assessment else {}
        review = reviews.get(identity)
        review_attrs = _attrs(agent, review) if review is not None else {}
        identities.append({
            "gap_identity": identity,
            "observation_count": sum(
                item["gap_identity"] == identity for item in observations),
            "recurrence_count": ra.get("recurrence_count"),
            "recurrence_status": ra.get("status"),
            "assessment_status": aa.get("promotion_status"),
            "auto_promoted": aa.get("auto_promoted"),
            "failed_repair_visible": review_attrs.get("failed_repair_visible"),
            "promotion_authority": ra.get("promotion_authority"),
            "recurrence_node_ids": [_node_id(node) for node in recurrence],
            "assessment_node_ids": [_node_id(node) for node in assessment],
        })
    return {
        "schema": SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "fixture_sha256": hashlib.sha256(
            json.dumps(list(fixture), sort_keys=True).encode()).hexdigest(),
        "observation_contract": {
            "status": "measured",
            "required_fields": ["gap_identity", "learning_stage",
                                "verification_status"],
            "observation_count": len(observations),
        },
        "observations": observations,
        "identities": identities,
        "native_authority": {
            "recurrence_node_type": "GapRecurrence",
            "assessment_node_type": "GapLearningAssessment",
            "promotion_is_human_gated": all(
                item["auto_promoted"] == 0.0
                for item in identities
            ),
            "verified_retry_identity": promoted_identity,
        },
        "status": "measured",
    }


__all__ = ["FIXTURE", "PROTOCOL_ID", "SCHEMA", "measure_fixture"]
