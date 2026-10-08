"""Adjudicate Phase 6 runtime-state diagnostics without changing cognition.

This evaluation overlay separates missing disposition authority from genuine
graph-state disagreement.  It never treats receipt semantics, reply text, or
interpretation-only fields as a cognitive disposition and never emits a
repair policy.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping


SCHEMA = "phase6_runtime_state_adjudication.v1"


def _category(row: Mapping[str, Any]) -> str:
    authority = row.get("authority")
    if authority not in {"graph_readback", "native_graph_readback"}:
        if row.get("evidence_available") is True:
            # A coincident expected/observed label is not a verified state
            # match when the source is only interpretation or adapter evidence.
            return "disposition_authority_missing"
        return "state_evidence_unavailable"
    if row.get("match"):
        return "state_match"
    return "graph_cognitive_state_mismatch"


def adjudicate_runtime_state(
    report: Mapping[str, Any], corpus: Mapping[str, Any]
) -> dict[str, Any]:
    """Classify runtime-state diagnostics by evidence authority."""
    diagnostics = {
        str(item.get("id")): item
        for item in report.get("runtime_state_diagnostics", ())
        if isinstance(item, Mapping)
    }
    # Current Phase 8 corpus reports carry the same diagnostic fields directly
    # on each observation.  Reuse that authoritative schema instead of
    # requiring a parallel runtime-state export or reconstructing state from
    # reply text.  The legacy explicit diagnostic input remains supported for
    # older reports and focused tests.
    if "runtime_state_diagnostics" not in report:
        diagnostics = {
            str(item.get("id")): {
                "id": item.get("id"),
                "observed_state": item.get("observed_state"),
                "match": item.get("state_match", False),
                "source": item.get("cognitive_state_evidence_source"),
                "authority": item.get("cognitive_state_authority"),
                "evidence_available": item.get(
                    "cognitive_state_evidence_available"),
                "release_state": item.get("release_state"),
            }
            for item in report.get("observations", ())
            if isinstance(item, Mapping)
        }
    rows: list[dict[str, Any]] = []
    for event in corpus.get("events", ()):
        event_id = str(event.get("id"))
        row = diagnostics.get(event_id)
        if row is None:
            continue
        category = _category(row)
        rows.append({
            "id": event_id,
            "expected_state": event.get("expected_state"),
            "observed_state": row.get("observed_state"),
            "match": bool(row.get("match")),
            "category": category,
            "source": row.get("source"),
            "authority": row.get("authority"),
            "evidence_available": row.get("evidence_available"),
            "release_state": row.get("release_state"),
            "not_receipt_semantic_evidence": True,
        })
    counts = Counter(row["category"] for row in rows)
    expected_ids = {str(event.get("id")) for event in corpus.get("events", ())}
    return {
        "schema": SCHEMA,
        "event_count": len(corpus.get("events", ())),
        "diagnostic_count": len(rows),
        "matched_count": sum(row["match"] for row in rows),
        "mismatch_count": sum(not row["match"] for row in rows),
        "category_counts": dict(sorted(counts.items())),
        "missing_diagnostic_ids": sorted(expected_ids - set(diagnostics)),
        "unknown_diagnostic_ids": sorted(set(diagnostics) - expected_ids),
        "rows": rows,
        "reply_text_used_as_evidence": False,
        "receipt_semantics_used_as_cognitive_state": False,
        "status": "measured" if len(rows) == len(expected_ids) else "incomplete",
    }


__all__ = ["SCHEMA", "adjudicate_runtime_state"]
