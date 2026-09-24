"""Audit collected Phase 8 reference envelopes without scoring outputs.

This is the safe bridge between raw collection and blinded adjudication.  It
checks corpus binding, protocol identity, observation completeness, and
collection failures.  It deliberately never interprets response text or
turns raw outputs into capability scores.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from evaluation.comparative_release_gate import BASELINES


SCHEMA = "phase8_raw_reference_audit.v1"


def audit_raw_reference_runs(
    corpus: Mapping[str, Any], runs: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    expected_ids = [str(item.get("id")) for item in corpus.get("events", ())]
    expected = set(expected_ids)
    rows: list[dict[str, Any]] = []
    for system in BASELINES:
        run = runs.get(system)
        if not isinstance(run, Mapping):
            rows.append({"system": system, "status": "missing",
                         "observation_count": 0,
                         "missing_case_count": len(expected_ids),
                         "duplicate_case_count": 0,
                         "unknown_case_count": 0,
                         "collection_failure_count": 0,
                         "score_interpretation_performed": False})
            continue
        observations = run.get("observations")
        observations = observations if isinstance(observations, list) else []
        ids = [str(item.get("case_id", ""))
               for item in observations if isinstance(item, Mapping)]
        counts = Counter(ids)
        duplicate_ids = sorted(key for key, count in counts.items() if count > 1)
        unknown_ids = sorted(set(ids) - expected)
        missing_ids = sorted(expected - set(ids))
        failures = run.get("collection_failures")
        failures = failures if isinstance(failures, list) else []
        protocol_ok = run.get("protocol_id") == corpus.get(
            "protocol_id", run.get("protocol_id"))
        complete = (len(observations) == len(expected_ids)
                    and not duplicate_ids and not unknown_ids
                    and not missing_ids and not failures and protocol_ok)
        rows.append({
            "system": system,
            "status": "complete_raw" if complete else "incomplete_raw",
            "observation_count": len(observations),
            "missing_case_count": len(missing_ids),
            "duplicate_case_count": len(duplicate_ids),
            "unknown_case_count": len(unknown_ids),
            "collection_failure_count": len(failures),
            "protocol_id": run.get("protocol_id"),
            "protocol_match": protocol_ok,
            "scorecard_collection_status": (
                (run.get("scorecard") or {}).get("collection_status")
                if isinstance(run.get("scorecard"), Mapping) else None),
            "score_interpretation_performed": False,
        })
    counts = Counter(row["status"] for row in rows)
    return {
        "schema": SCHEMA,
        "corpus_event_count": len(expected_ids),
        "reference_count": len(BASELINES),
        "status_counts": dict(sorted(counts.items())),
        "rows": rows,
        "surface_text_used_as_evidence": False,
        "score_interpretation_performed": False,
        "human_reference_status": "missing",
        "status": "measured" if all(
            row["status"] == "complete_raw" for row in rows
        ) else "incomplete",
    }


__all__ = ["SCHEMA", "audit_raw_reference_runs"]
