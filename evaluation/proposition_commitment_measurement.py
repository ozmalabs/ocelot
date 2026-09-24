"""Isolated measurement for neutral proposition commitment and consequence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from substrate.boot_all import load_all_seeds
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from domains.proposition_commitment import apply_situation_consequence


FIXTURE = (Path(__file__).resolve().parents[1] / "tests" / "fixtures" /
           "conversational_manifold" / "proposition_commitment_cases.json")


def load_cases(path: Path = FIXTURE) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("schema") != "proposition_commitment_cases.v1":
        raise ValueError("invalid proposition commitment fixture schema")
    if not isinstance(payload.get("cases"), list) or not payload["cases"]:
        raise ValueError("proposition commitment fixture needs cases")
    return payload


def measure_cases(cases: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = load_cases() if cases is None else cases
    rows: list[dict[str, Any]] = []
    for case in payload["cases"]:
        agent = WorldAdapter(seeds=())
        load_all_seeds(agent)
        agent.inner.load_seed_manifest(
            manifest_for("proposition_commitment_lifecycle"), agent.agent)
        result = agent.ingest_semantic_event(
            {
                "speech_act": "assertion",
                "communicative_force": "assertion_or_correction",
                "cognitive_goal": "update_common_ground",
                "grounding_status": "candidate_grounded",
                "proposition": case["proposition"],
            },
            provider=case["proposition"]["provider"],
            interaction_mode="asynchronous",
        )
        proposition_result = result["proposition"]
        proposition = proposition_result.get("proposition") if proposition_result else None
        attrs = agent.s.node(proposition)["attrs"] if proposition else {}
        consequence = apply_situation_consequence(agent, proposition) if proposition else {
            "supported": False, "error": "proposition_not_materialized"
        }
        expected = case["expected"]
        rows.append({
            "id": case["id"],
            "bridge_supported": bool(proposition_result and proposition_result.get("supported")),
            "commitment_status": attrs.get("commitment_status"),
            "expected_commitment_status": expected["commitment_status"],
            "consequence_supported": bool(consequence.get("supported")),
            "expected_consequence_supported": bool(expected["consequence_supported"]),
            "provenance_complete": bool(
                proposition_result and proposition_result.get("evidence") and
                agent.s.has_edge(proposition, "evidenced_by",
                                 proposition_result["evidence"])),
            "error": consequence.get("error"),
        })

    status_matches = sum(r["commitment_status"] == r["expected_commitment_status"] for r in rows)
    consequence_matches = sum(r["consequence_supported"] == r["expected_consequence_supported"] for r in rows)
    return {
        "schema": "proposition_commitment_measurement.v1",
        "case_count": len(rows),
        "commitment_status_accuracy": status_matches / len(rows),
        "consequence_projection_accuracy": consequence_matches / len(rows),
        "supported_consequence_count": sum(r["consequence_supported"] for r in rows),
        "provenance_complete_count": sum(r["provenance_complete"] for r in rows),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(measure_cases(), indent=2, sort_keys=True))
