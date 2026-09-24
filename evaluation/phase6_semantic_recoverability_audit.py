"""Fail-closed audit of semantic recoverability mismatches.

This is an evaluation readback, not a repair policy.  It compares independent
runtime fields with the corpus labels and classifies mismatches so cognitive
work can target the right faculty.  It never treats reply wording as semantic
evidence and never proposes a fallback surface.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from evaluation.phase8_corpus_runner import FORCE_ALIASES


def audit_semantic_recoverability(
    report: Mapping[str, Any], corpus: Mapping[str, Any]
) -> dict[str, Any]:
    observations = {str(item.get("id")): item for item in report.get("observations", ())
                    if isinstance(item, Mapping)}
    mismatches: list[dict[str, Any]] = []
    for event in corpus.get("events", ()):
        case_id = str(event.get("id"))
        observed = observations.get(case_id, {})
        expected_state = event.get("expected_state")
        observed_state = observed.get("observed_state")
        raw_expected_force = event.get("communicative_force")
        # The corpus preserves fine-grained adjudication labels, while the
        # runtime deliberately exposes the language-neutral communication
        # ontology.  Compare at that declared boundary; do not make the audit
        # demand a second surface-level force taxonomy.
        expected_force = FORCE_ALIASES.get(raw_expected_force, raw_expected_force)
        observed_force = observed.get("observed_force")
        expected_grounding = event.get("grounding_status")
        observed_grounding = observed.get("grounding_status")
        dimensions: list[str] = []
        if expected_state != observed_state:
            dimensions.append("state")
        if expected_force != observed_force:
            dimensions.append("force")
        if expected_grounding in {"grounded", "partially_grounded"} and observed_grounding not in {
            "candidate_grounded", "grounded", "partially_grounded"
        }:
            dimensions.append("grounding_recall")
        if not dimensions:
            continue
        # Keep only graph/runtime evidence fields; reply text is intentionally
        # excluded from the audit record.
        mismatches.append({
            "id": case_id,
            "dimensions": dimensions,
            "expected": {"state": expected_state, "force": expected_force,
                          "raw_force": raw_expected_force,
                          "grounding": expected_grounding},
            "observed": {"state": observed_state, "force": observed_force,
                          "grounding": observed_grounding,
                          "grounding_evidence_path": observed.get("grounding_evidence_path"),
                          "error": observed.get("error")},
            "cognitive_trace_present": observed.get("cognitive_trace") is not None,
            "production_gate_receipt_count": len(observed.get("production_gate_receipts") or []),
        })
    dimension_counts = Counter(
        dimension for item in mismatches for dimension in item["dimensions"]
    )
    return {
        "schema": "phase6_semantic_recoverability_audit.v1",
        "protocol_id": report.get("protocol_id"),
        "event_count": len(corpus.get("events", ())),
        "observed_event_count": len(observations),
        "mismatch_count": len(mismatches),
        "dimension_counts": dict(sorted(dimension_counts.items())),
        "mismatches": mismatches,
        "surface_text_used_as_evidence": False,
        "status": "measured" if len(observations) == len(corpus.get("events", ())) else "incomplete",
    }
