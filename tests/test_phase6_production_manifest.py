"""Phase 6 fixed-corpus production receipt/error coverage."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.phase6_production_manifest import (
    EXPLICIT_ERROR,
    build_manifest,
    check_coverage,
    collect_live_observations,
    diagnose_live_manifest,
)


FIXTURE = Path(__file__).parent / "fixtures" / "conversational_manifold" / "phase0_events.json"


def test_manifest_covers_all_74_events_and_separates_fragments():
    corpus = json.loads(FIXTURE.read_text(encoding="utf-8"))
    manifest = build_manifest(corpus)

    assert manifest["event_count"] == 74
    assert manifest["classification_counts"] == {
        "cognition_only": 9,
        "substantive_surface": 65,
    }
    assert len({item["id"] for item in manifest["events"]}) == 74
    assert all(
        item["classification"] == "cognition_only"
        for item in manifest["events"]
        if item["literal_form"] == "fragment"
    )


def test_every_substantive_event_requires_receipt_or_explicit_error():
    manifest = build_manifest(json.loads(FIXTURE.read_text(encoding="utf-8")))
    observations = []
    for event in manifest["events"]:
        if event["classification"] == "cognition_only":
            observations.append({"id": event["id"], "cognitive_trace": {"state": event["expected_state"]}})
        elif event["expected_state"] == "error":
            observations.append({"id": event["id"], "reply": EXPLICIT_ERROR})
        else:
            observations.append({
                "id": event["id"],
                "production_gate_receipt": {
                    "type": "ProductionGateReceipt", "status": "released",
                },
            })

    coverage = check_coverage(manifest, observations)
    assert coverage["event_count"] == 74
    assert coverage["covered"] == 74
    assert coverage["uncovered"] == []
    assert sum(item["status"] == "cognition_only" for item in coverage["results"]) == 9


def test_reply_text_cannot_fabricate_release_or_error_coverage():
    manifest = build_manifest(json.loads(FIXTURE.read_text(encoding="utf-8")))
    event = next(item for item in manifest["events"] if item["classification"] == "substantive_surface")

    coverage = check_coverage(manifest, [{"id": event["id"], "reply": "noted"}])
    result = next(item for item in coverage["results"] if item["id"] == event["id"])
    assert result["status"] == "missing_surface_evidence"
    assert result["covered"] is False


def test_live_adapter_accepts_only_serialized_receipts_errors_and_traces():
    manifest = build_manifest(json.loads(FIXTURE.read_text(encoding="utf-8")))
    report = {"schema": "phase8_sut_corpus_report.v2", "observations": []}
    for event in manifest["events"]:
        row = {"id": event["id"], "trace_coverage": {"interpretation": True}}
        if event["classification"] == "cognition_only":
            row["cognitive_trace"] = {"state": event["expected_state"]}
        elif event["expected_state"] == "error":
            row["reply"] = EXPLICIT_ERROR
        else:
            row["production_gate_receipt"] = {
                "type": "ProductionGateReceipt", "status": "released",
            }
        report["observations"].append(row)

    extracted = collect_live_observations(report)
    assert all("trace_coverage" not in row for row in extracted)
    diagnostic = diagnose_live_manifest(report, manifest)
    assert diagnostic["status"] == "ready"
    assert diagnostic["blockers"] == []
    assert diagnostic["evidence_inventory"] == {
        "released_receipts": 63,
        "explicit_errors": 2,
        "cognitive_traces": 9,
        "trace_coverage_flags_ignored": 74,
    }


def test_current_phase8_report_is_ready_after_measured_permission_fix():
    report = json.loads(
        Path("evaluation/reports/phase8_corpus_report_20260923.json").read_text(encoding="utf-8")
    )
    diagnostic = diagnose_live_manifest(report)

    assert diagnostic["status"] == "ready"
    assert diagnostic["observed_event_count"] == 74
    assert diagnostic["evidence_inventory"]["released_receipts"] == 40
    assert diagnostic["evidence_inventory"]["cognitive_traces"] == 74
    assert diagnostic["evidence_inventory"]["explicit_errors"] == 34
    assert diagnostic["evidence_inventory"]["trace_coverage_flags_ignored"] == 74
    assert "trace_coverage_flags_are_not_cognitive_trace_objects" not in diagnostic["blockers"]
    assert diagnostic["coverage"]["uncovered"] == []


def test_graph_resident_receipt_is_bound_and_serialized_for_the_current_turn():
    pytest.importorskip("substrate_rs")
    from substrate.world_adapter import WorldAdapter
    from domains.production_gate import release_if_gated

    agent = WorldAdapter(seeds=())
    inbound = agent.receive_utterance(
        "The dog is a mammal.", speech_act="statement")
    agent._turn_production_receipt_baseline = set()
    committed = agent.s.add_node("Committed", {"utterance": "The dog is a mammal"})
    gate = {"recoverable": True, "coverage": 1.0, "mode": "test"}
    assert release_if_gated(
        agent,
        {"event": "is", "agent": "dog", "patient": "mammal", "intent": "inform"},
        "The dog is a mammal.", gate, committed) == "The dog is a mammal."

    evidence = agent.production_turn_evidence(inbound)
    assert len(evidence["production_gate_receipts"]) == 1
    receipt = evidence["production_gate_receipts"][0]
    assert receipt["type"] == "ProductionGateReceipt"
    assert receipt["status"] == "released"
    assert receipt["attrs"]["turn_message_id"] == int(inbound.value)
    assert evidence["cognitive_trace"]["source"] == "graph_resident_conversation"


def test_live_extraction_preserves_graph_evidence_but_drops_flags():
    report = {"observations": [{
        "id": "x",
        "trace_coverage": {"interpretation": True},
        "production_gate_receipts": [{
            "type": "ProductionGateReceipt", "status": "released",
        }],
        "cognitive_trace": {"schema": "cognition_trace.v1"},
    }]}
    extracted = collect_live_observations(report)
    assert extracted == [{
        "id": "x",
        "production_gate_receipts": [{
            "type": "ProductionGateReceipt", "status": "released",
        }],
        "cognitive_trace": {"schema": "cognition_trace.v1"},
    }]


def test_production_trace_serializes_native_deliberation_records_when_bound():
    """Phase 4 evidence is observable without fabricating a live candidate."""
    pytest.importorskip("substrate_rs")
    from substrate.seed_loader import manifest_for
    from substrate.world_adapter import WorldAdapter
    from domains.conversation_deliberation import materialize_deliberation

    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(
        manifest_for("conversation_deliberation_phase4a"), agent.agent)
    inbound = agent.receive_utterance(
        "Check the pressure.", speech_act="instruction")
    goal = agent.s.add_node("Goal", {
        "kind": "instruction", "origin_turn_id": int(inbound.value),
    })
    agent.inner.add_edge_unchecked(goal, "comprehends", inbound)
    deliberation = materialize_deliberation(
        agent, goal=goal, candidates=[
            {"candidate_id": "winner", "grounding": 1.0,
             "expected_value": 0.9, "residual_cost": 0.1,
             "consequence": 0.5, "novelty": 0.2,
             "execution_ready": 1.0, "outcome_status": "resolved"},
            {"candidate_id": "alternative", "grounding": 1.0,
             "expected_value": 0.2, "residual_cost": 0.4,
             "consequence": 0.1, "novelty": 0.1},
        ])
    agent.inner.run_rules()
    evidence = agent.production_turn_evidence(inbound)
    deliberations = evidence["cognitive_trace"]["turn"]["deliberations"]
    assert len(deliberations) == 1
    assert deliberations[0]["id"] == int(deliberation.value)
    assert deliberations[0]["candidates"]
    assert deliberations[0]["selections"]
    assert deliberations[0]["settlements"]
