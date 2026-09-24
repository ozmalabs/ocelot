"""Phase 2T: event-to-commitment measurement over a separate overlay.

This evaluator is intentionally not a second conversation or truth layer.  It
replays neutral semantic frames through the existing ``WorldAdapter`` ingress,
reads the graph-resident proposition lifecycle, and records the existing
situation-consequence projection.  The overlay references event IDs from the
Phase 0 corpus but never edits or replays that corpus.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from domains.proposition_commitment import (
    EVIDENCE_KIND,
    EVIDENCE_SCHEMA,
    apply_situation_consequence,
)
from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = (ROOT / "tests" / "fixtures" / "conversational_manifold" /
           "proposition_event_commitment_cases.json")
PHASE0 = ROOT / "tests" / "fixtures" / "conversational_manifold" / "phase0_events.json"


def load_cases(path: Path = FIXTURE) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("schema") != "proposition_event_commitment_cases.v1":
        raise ValueError("invalid proposition event commitment fixture schema")
    if not isinstance(payload.get("cases"), list) or not payload["cases"]:
        raise ValueError("proposition event commitment fixture needs cases")
    phase0 = json.loads(PHASE0.read_text(encoding="utf-8"))
    valid_ids = {event.get("id") for event in phase0.get("events", [])}
    for case in payload["cases"]:
        for step in case.get("steps", []):
            if step.get("event_id") not in valid_ids:
                raise ValueError("overlay event_id is not in Phase 0 corpus: %s" %
                                 step.get("event_id"))
    return payload


def _new_agent() -> WorldAdapter:
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.inner.load_seed_manifest(
        manifest_for("proposition_commitment_lifecycle"), agent.agent)
    return agent


def _frame(step: Mapping[str, Any]) -> dict[str, Any]:
    frame = {
        "event_id": step["event_id"],
        "speech_act": "assertion",
        "communicative_force": "assertion_or_correction",
        "cognitive_goal": "update_common_ground",
        "grounding_status": step.get("grounding_status", "candidate_grounded"),
        "interaction_mode": step.get("interaction_mode", "non_turn"),
    }
    if "proposition" in step:
        frame["proposition"] = step["proposition"]
    return frame


def _node_attrs(agent: WorldAdapter, node) -> dict[str, Any]:
    return dict(agent.s.node(node)["attrs"]) if node is not None else {}


def _event_identity(agent: WorldAdapter, result: Mapping[str, Any]) -> bool:
    frame = result.get("semantic_frame_id")
    return bool(frame and _node_attrs(agent, frame).get("event_id"))


def _proposition_readback(agent: WorldAdapter, proposition) -> dict[str, Any]:
    attrs = _node_attrs(agent, proposition)
    evidence = list(agent.inner.neighbours(proposition, "evidenced_by")) if proposition else []
    origins = list(agent.inner.neighbours(proposition, "originated_in")) if proposition else []
    return {
        "materialized": proposition is not None,
        "commitment_status": attrs.get("commitment_status"),
        "uptake_signal": attrs.get("uptake_signal"),
        "uptake_applied": attrs.get("uptake_applied"),
        "evidence_present": bool(evidence),
        "origin_event_present": bool(origins),
    }


def _run_case(case: Mapping[str, Any]) -> dict[str, Any]:
    agent = _new_agent()
    steps: list[dict[str, Any]] = []
    proposition = None
    bridge_errors: list[str] = []
    initial_prop_count = len(agent.s.nodes("Proposition"))

    for step in case["steps"]:
        before_props = len(agent.s.nodes("Proposition"))
        result = agent.ingest_semantic_event(
            _frame(step), provider=step.get("provider", "phase2t_overlay"),
            interaction_mode=step.get("interaction_mode", "non_turn"),
        )
        proposition_result = result.get("proposition")
        if proposition_result and proposition_result.get("error"):
            bridge_errors.append(str(proposition_result["error"]))
        if proposition_result and proposition_result.get("proposition") is not None:
            proposition = proposition_result["proposition"]

        # Lifecycle mutations are explicit native uptake signals.  They are
        # not derived from text, a reply, or the overlay's expected result.
        for signal in step.get("native_uptake", []):
            if proposition is not None:
                agent.inner.set_attr(proposition, "uptake_signal", signal)
                agent.inner.run_rules()

        readback = _proposition_readback(agent, proposition)
        steps.append({
            "event_id": step["event_id"],
            "event_identity": _event_identity(agent, result),
            "proposition": readback,
            "bridge_supported": bool(proposition_result and
                                       proposition_result.get("supported")),
            "bridge_error": (proposition_result or {}).get("error"),
            "proposition_count_delta": len(agent.s.nodes("Proposition")) - before_props,
            "reply": result.get("reply"),
        })

    consequence = ({"supported": False, "error": "no_proposition"}
                   if proposition is None else
                   apply_situation_consequence(agent, proposition))
    final = _proposition_readback(agent, proposition)
    expected = case["expected"]
    return {
        "id": case["id"],
        "category": case["category"],
        "steps": steps,
        "event_identity": all(step["event_identity"] for step in steps),
        "proposition_materialized": final["materialized"],
        "proposition": final,
        "commitment_status": final["commitment_status"],
        "expected_commitment_status": expected.get("commitment_status"),
        "consequence_supported": bool(consequence.get("supported")),
        "consequence_error": consequence.get("error"),
        "consequence_provenance": bool(
            consequence.get("consequence") and proposition and
            agent.inner.has_edge(consequence["consequence"],
                                 "for_proposition", proposition)),
        "expected_consequence_supported": bool(
            expected.get("consequence_supported", False)),
        "expected_materialized": bool(expected.get("materialized", True)),
        "bridge_errors": bridge_errors,
        "reply_evidence_used": False,
        "external_truth_claim": False,
        "proposition_count_delta": len(agent.s.nodes("Proposition")) - initial_prop_count,
    }


def measure_cases(cases: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = load_cases() if cases is None else cases
    rows = [_run_case(case) for case in payload["cases"]]
    status_rows = [row for row in rows if row["expected_commitment_status"] is not None]
    status_accuracy = (
        sum(row["commitment_status"] == row["expected_commitment_status"]
            for row in status_rows) / len(status_rows) if status_rows else 1.0)
    consequence_accuracy = sum(
        row["consequence_supported"] == row["expected_consequence_supported"]
        for row in rows) / len(rows)
    materialization_accuracy = sum(
        row["proposition_materialized"] == row["expected_materialized"]
        for row in rows) / len(rows)
    return {
        "schema": "proposition_event_commitment_measurement.v1",
        "case_count": len(rows),
        "event_identity_count": sum(
            step["event_identity"] for row in rows for step in row["steps"]),
        "proposition_materialization_accuracy": materialization_accuracy,
        "commitment_status_accuracy": status_accuracy,
        "consequence_projection_accuracy": consequence_accuracy,
        "proposition_provenance_complete_count": sum(
            row["proposition"]["evidence_present"] and
            row["proposition"]["origin_event_present"] for row in rows),
        "consequence_provenance_complete_count": sum(
            row["consequence_provenance"] for row in rows),
        "fail_closed_negative_count": sum(
            row["category"] in {"unsupported", "ambiguous", "no_world", "contradiction"}
            and not row["consequence_supported"] for row in rows),
        "reply_evidence_used": any(row["reply_evidence_used"] for row in rows),
        "external_truth_claim": any(row["external_truth_claim"] for row in rows),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(measure_cases(), indent=2, sort_keys=True))
