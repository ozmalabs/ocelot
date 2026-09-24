"""Focused Phase 5H tests for explicit production learning observations."""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from evaluation.phase5_production_learning_fixture import (  # noqa: E402
    FIXTURE,
    SCHEMA,
    measure_fixture,
)
from substrate.boot_all import load_all_seeds  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


@pytest.fixture(scope="module")
def report():
    return measure_fixture()


def test_fixture_contract_is_explicit_and_provenance_bearing(report):
    assert report["schema"] == SCHEMA
    assert report["observation_contract"]["status"] == "measured"
    assert report["observation_contract"]["observation_count"] == len(FIXTURE)
    assert report["observation_contract"]["required_fields"] == [
        "gap_identity", "learning_stage", "verification_status",
    ]
    assert report["fixture_sha256"]
    assert {row["gap_identity"] for row in report["observations"]} == {
        "knowledge|task|opaque-alpha|turn:none",
        "planning|goal|opaque-beta|turn:none",
    }


def test_native_recurrence_is_stable_and_local(report):
    assert len(report["identities"]) == 2
    assert all(item["observation_count"] == 2 for item in report["identities"])
    assert all(item["recurrence_count"] == 2.0 for item in report["identities"])
    statuses = {item["gap_identity"]: item["recurrence_status"]
                for item in report["identities"]}
    assert statuses["knowledge|task|opaque-alpha|turn:none"] == "promoted"
    assert statuses["planning|goal|opaque-beta|turn:none"] == "open"
    assert all(item["recurrence_node_ids"] for item in report["identities"])


def test_recurrence_does_not_auto_promote(report):
    assert report["native_authority"]["promotion_is_human_gated"] is True
    statuses = {item["gap_identity"]: item["assessment_status"]
                for item in report["identities"]}
    assert statuses["knowledge|task|opaque-alpha|turn:none"] == "promoted"
    assert statuses["planning|goal|opaque-beta|turn:none"] == "human_review"
    assert all(item["auto_promoted"] == 0.0 for item in report["identities"])
    assert all(item["failed_repair_visible"] == 1.0
               for item in report["identities"])
    assert report["identities"][0]["promotion_authority"] == "human_review"


def test_live_communication_ingress_transports_explicit_learning_observation():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    observation = {
        "gap_identity": "knowledge|task|live-opaque|turn:none",
        "learning_stage": "observed",
        "verification_status": "unverified",
        "kind": "knowledge",
        "source": "task",
        "content": "live-opaque",
        "event_id": "live-learning-1",
        "event_stage": "initial_observation",
    }
    agent.converse(
        "I do not understand the signal.", speech_act="statement",
        context={"interaction_mode": "non_turn",
                 "learning_observation": observation})
    message = agent._last_turn_inbound
    assert agent.s.node(message)["attrs"]["learning_observation_schema"] == (
        "learning_observation.v1")
    concerns = [
        node for node in agent.s.nodes("SelfConcern")
        if agent.s.node(node)["attrs"].get("gap_identity") == observation["gap_identity"]
    ]
    assert len(concerns) == 1
    attrs = agent.s.node(concerns[0])["attrs"]
    assert attrs["learning_stage"] == "observed"
    assert attrs["verification_status"] == "unverified"
    assert attrs["event_id"] == observation["event_id"]
    assert concerns[0] in agent.inner.neighbours(agent.agent, "has_self_concern")
    assert message in agent.inner.neighbours(concerns[0], "originated_in")


def test_live_learning_observations_drive_native_recurrence_priority():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    identity = "knowledge|task|live-recurrent|turn:none"
    for index, stage in enumerate(("observed", "recurrent"), start=1):
        agent.converse(
            "The signal remains unresolved.", speech_act="statement",
            context={
                "interaction_mode": "non_turn",
                "learning_observation": {
                    "gap_identity": identity,
                    "learning_stage": stage,
                    "verification_status": "unverified",
                    "kind": "knowledge",
                    "source": "task",
                    "content": "live-recurrent",
                    "event_id": f"live-recurrent-{index}",
                    "event_stage": stage,
                },
            })
    recurrence = next(
        node for node in agent.s.nodes("GapRecurrence")
        if agent.s.node(node)["attrs"].get("gap_identity") == identity)
    attrs = agent.s.node(recurrence)["attrs"]
    assert attrs["recurrence_count"] == 2.0
    assert attrs["priority"] >= 2.0
    assessment = next(
        node for node in agent.s.nodes("GapLearningAssessment")
        if agent.s.node(node)["attrs"].get("gap_identity") == identity)
    assessment_attrs = agent.s.node(assessment)["attrs"]
    assert assessment_attrs["promotion_status"] == "human_review"
    assert assessment_attrs["auto_promoted"] == 0.0


def test_competing_live_identities_keep_priority_and_learning_local():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    cases = (
        ("knowledge|task|live-alpha|turn:none", "live-alpha", 2),
        ("planning|goal|live-beta|turn:none", "live-beta", 3),
    )
    for identity, content, count in cases:
        for index in range(count):
            agent.converse(
                "The unresolved task persists.", speech_act="statement",
                context={
                    "interaction_mode": "non_turn",
                    "learning_observation": {
                        "gap_identity": identity,
                        "learning_stage": "observed" if index == 0 else "recurrent",
                        "verification_status": "unverified",
                        "kind": identity.split("|", 1)[0],
                        "source": identity.split("|", 2)[1],
                        "content": content,
                        "event_id": f"{content}-{index}",
                        "event_stage": "observation",
                    },
                })
    recurrences = {
        agent.s.node(node)["attrs"]["gap_identity"]: agent.s.node(node)["attrs"]
        for node in agent.s.nodes("GapRecurrence")
        if agent.s.node(node)["attrs"].get("gap_identity") in {
            item[0] for item in cases
        }
    }
    assert set(recurrences) == {item[0] for item in cases}
    assert recurrences[cases[0][0]]["recurrence_count"] == 2.0
    assert recurrences[cases[1][0]]["recurrence_count"] == 3.0
    assert recurrences[cases[0][0]]["priority"] < recurrences[cases[1][0]]["priority"]
    assessments = {
        agent.s.node(node)["attrs"]["gap_identity"]: agent.s.node(node)["attrs"]
        for node in agent.s.nodes("GapLearningAssessment")
        if agent.s.node(node)["attrs"].get("gap_identity") in recurrences
    }
    assert all(attrs["promotion_status"] == "human_review"
               and attrs["auto_promoted"] == 0.0
               for attrs in assessments.values())
