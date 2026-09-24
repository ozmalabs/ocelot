"""Explain Phase 6 receipt mismatches without changing release semantics.

The recoverability classifier identifies a mismatch; this audit reads the
receipt graph evidence to distinguish a repeated identical release from
multiple competing semantic releases on one communication event.  It never
chooses a receipt or rewrites a production outcome.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from evaluation.phase6_receipt_recoverability import (
    RELEASED_MISMATCH, measure_receipt_recoverability,
)


SCHEMA = "phase6_receipt_mismatch_audit.v1"


def _receipt_attrs(receipt: Mapping[str, Any]) -> Mapping[str, Any]:
    attrs = receipt.get("attrs")
    return attrs if isinstance(attrs, Mapping) else receipt


def _receipts(observation: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    values = observation.get("production_gate_receipts")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        one = observation.get("production_gate_receipt")
        return [one] if isinstance(one, Mapping) else []
    return [item for item in values if isinstance(item, Mapping)]


def audit_receipt_mismatches(
    report: Mapping[str, Any], corpus: Mapping[str, Any]
) -> dict[str, Any]:
    """Return mismatch causes plus receipt-level semantic provenance."""
    measured = measure_receipt_recoverability(report, corpus)
    raw = {
        str(item.get("id")): item
        for item in report.get("observations", ())
        if isinstance(item, Mapping)
    }
    rows: list[dict[str, Any]] = []
    for result in measured["results"]:
        if result["classification"] != RELEASED_MISMATCH:
            continue
        observation = raw.get(result["id"], {})
        released = [item for item in _receipts(observation)
                    if _receipt_attrs(item).get("status") == "released"]
        semantic_keys = ("semantic_event", "semantic_intent", "semantic_content",
                         "parse_back_mode")
        signatures = [tuple(_receipt_attrs(item).get(key)
                            if key != "semantic_content"
                            else tuple(_receipt_attrs(item).get(key) or [])
                            for key in semantic_keys)
                      for item in released]
        turn_ids = sorted({str(_receipt_attrs(item).get("turn_message_id"))
                           for item in released
                           if _receipt_attrs(item).get("turn_message_id") is not None})
        if "released_receipt_multiplicity" in result["dimensions"]:
            kind = ("duplicate_semantic_release" if len(set(signatures)) == 1
                    else "competing_semantic_releases")
        else:
            kind = "semantic_field_mismatch"
        rows.append({
            "id": result["id"],
            "dimensions": list(result["dimensions"]),
            "cause": kind,
            "released_receipt_count": len(released),
            "turn_message_ids": turn_ids,
            "semantic_signatures": [list(signature) for signature in signatures],
            "receipt_selection_performed": False,
        })
    rows.sort(key=lambda row: row["id"])
    return {
        "schema": SCHEMA,
        "classification_counts": dict(measured["classification_counts"]),
        "mismatch_count": len(rows),
        "mismatches": rows,
        "receipt_selection_performed": False,
        "surface_text_used_as_evidence": False,
        "status": "measured" if measured["status"] == "measured" else "incomplete",
    }


__all__ = ["SCHEMA", "audit_receipt_mismatches"]
