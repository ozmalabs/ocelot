"""Phase 4R: partial substrate evidence remains typed and fail-closed."""
from __future__ import annotations

import json

from evaluation.phase4_partial_evidence_audit import (
    audit_live_event,
    audit_partial_evidence,
)
from substrate.world_adapter import WorldAdapter


def test_partial_faculties_are_reported_without_dimension_inference():
    sources = [
        {"source_id": "held-path", "source_type": "HeldRelation",
         "faculty": "self_dialogue",
         "attrs": {"grounding": 1.0, "consequence": 0.2}},
        {"source_id": "audience-novelty", "source_type": "AudienceModel",
         "faculty": "audience",
         "attrs": {"novelty": 1.0}},
        {"source_id": "salience", "source_type": "SalienceRecord",
         "faculty": "global_workspace",
         "attrs": {"salience_quanta": 2}},
    ]
    report = audit_partial_evidence(sources)
    assert report["source_count"] == 3
    assert report["complete_tuple_count"] == 0
    assert report["promotion_count"] == 0
    assert report["records"][0]["faculty"] == "audience"
    assert "expected_value" in report["records"][1]["dimensions_missing"]
    assert "salience_quanta" not in report["required_dimensions"]
    assert json.loads(json.dumps(report)) == report


def test_complete_explicit_record_is_observable_but_not_selected():
    report = audit_partial_evidence([{
        "source_id": "verified-relation",
        "source_type": "ThoughtManifold",
        "faculty": "verified_relation",
        "attrs": {
            "grounding": 1.0, "expected_value": 0.8,
            "residual_cost": 0.1, "consequence": 0.6, "novelty": 0.2,
        },
    }])
    assert report["complete_tuple_count"] == 1
    assert report["promotion_eligible_count"] == 1
    assert report["promotion_count"] == 0
    assert report["records"][0]["promotion_reason"] == "complete_existing_tuple"
    assert "selected_candidate_id" not in report


def test_complete_tuple_from_unapproved_source_is_not_promotion_eligible():
    report = audit_partial_evidence([{
        "source_id": "complete-but-unapproved",
        "source_type": "AudienceModel",
        "faculty": "audience",
        "attrs": {
            "grounding": 1.0, "expected_value": 0.8,
            "residual_cost": 0.1, "consequence": 0.6, "novelty": 0.2,
        },
    }])
    assert report["complete_tuple_count"] == 1
    assert report["promotion_eligible_count"] == 0
    assert report["promotion_count"] == 0
    assert report["records"][0]["promotion_reason"] == "unapproved_source_type"


def test_live_event_audit_reads_only_explicit_event_links():
    agent = WorldAdapter(seeds=())
    event = agent.s.add_node("DiscourseEvent", {"event_id": "e4r"})
    linked = agent.s.add_node("AudienceModel", {
        "evidence_faculty": "audience", "novelty": 1.0,
    })
    unrelated = agent.s.add_node("ThoughtManifold", {
        "grounding": 1.0, "expected_value": 1.0,
        "residual_cost": 0.0, "consequence": 1.0, "novelty": 1.0,
    })
    agent.inner.add_edge_unchecked(event, "evidence_for_event", linked)
    report = audit_live_event(agent, event)
    assert report["source_count"] == 1
    assert report["records"][0]["source_id"] == str(linked.value)
    assert report["complete_tuple_count"] == 0
    assert unrelated not in [row["source_id"] for row in report["records"]]


def test_live_event_audit_follows_explicit_manifold_evidence_provenance():
    agent = WorldAdapter(seeds=())
    event = agent.s.add_node("DiscourseEvent", {"event_id": "e4r-manifold"})
    manifold = agent.s.add_node("ThoughtManifold", {})
    source = agent.s.add_node("AudienceModel", {
        "evidence_faculty": "audience", "novelty": 1.0,
    })
    agent.inner.add_edge_unchecked(manifold, "generated_from_discourse_event", event)
    agent.inner.add_edge_unchecked(manifold, "has_goal_evidence", source)
    report = audit_live_event(agent, event)
    assert report["source_count"] == 1
    assert any(row["source_id"] == str(source.value) for row in report["records"])


def test_live_event_audit_discovers_each_explicit_event_link_direction():
    agent = WorldAdapter(seeds=())
    event = agent.s.add_node("DiscourseEvent", {"event_id": "e4r-directions"})
    relations = (
        "derived_from_discourse_event", "generated_from_discourse_event",
        "evidence_for_event", "for_event",
    )
    expected = set()
    for index, relation in enumerate(relations):
        outgoing = agent.s.add_node("AudienceModel", {
            "evidence_faculty": "outgoing", "novelty": float(index + 1),
        })
        incoming = agent.s.add_node("AudienceModel", {
            "evidence_faculty": "incoming", "novelty": float(index + 5),
        })
        agent.inner.add_edge_unchecked(event, relation, outgoing)
        agent.inner.add_edge_unchecked(incoming, relation, event)
        expected.update({str(outgoing.value), str(incoming.value)})

    report = audit_live_event(agent, event)
    assert {row["source_id"] for row in report["records"]} == expected
    assert report["source_count"] == 8
    assert report["complete_tuple_count"] == 0


def test_partial_audit_replay_is_deterministic():
    sources = [
        {"source_id": "b", "source_type": "Residual", "faculty": "gap",
         "attrs": {"residual_cost": 0.4}},
        {"source_id": "a", "source_type": "Held", "faculty": "self_dialogue",
         "attrs": {"grounding": 1.0}},
    ]
    assert audit_partial_evidence(sources) == audit_partial_evidence(list(reversed(sources)))
