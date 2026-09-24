"""Phase 6 production-corpus coverage contract.

This module builds a manifest from the fixed communication corpus; it does not
run the system and never invents a ``ProductionGateReceipt``.  Completed
utterances are substantive production surfaces.  Incomplete fragments are
classified as cognition-only results because the cognition may defer, repair,
or wait for completion without releasing an outbound surface.

The coverage checker consumes observed evidence from a real run.  A
substantive event is covered only by a released production receipt or by the
canonical explicit error surface.  ``noted`` and other text are never treated
as errors or releases.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from evaluation.conversational_manifold_phase0 import FIXTURE, load_corpus

EXPLICIT_ERROR = "ERROR: no communicative response could be generated."
_ERROR_NORMALIZED = EXPLICIT_ERROR.lower()
_SUBSTANTIVE_FORMS = {"declarative", "interrogative", "imperative", "social"}


def build_manifest(corpus: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return a deterministic manifest for every event in the fixed corpus."""
    corpus = load_corpus() if corpus is None else corpus
    records = []
    for event in corpus["events"]:
        form = str(event.get("literal_form", ""))
        classification = (
            "substantive_surface" if form in _SUBSTANTIVE_FORMS
            else "cognition_only"
        )
        records.append({
            "id": event["id"],
            "signal": event["signal"],
            "literal_form": form,
            "communicative_force": event["communicative_force"],
            "cognitive_goal": event["cognitive_goal"],
            "expected_state": event["expected_state"],
            "classification": classification,
            "surface_required": classification == "substantive_surface",
            "evidence_requirements": (
                ["ProductionGateReceipt", "explicit_error"]
                if classification == "substantive_surface"
                else ["cognitive_trace"]
            ),
        })
    counts = Counter(record["classification"] for record in records)
    return {
        "schema": "phase6_production_corpus_manifest.v1",
        "corpus_schema": corpus.get("schema"),
        "corpus_path": str(FIXTURE),
        "event_count": len(records),
        "classification_counts": dict(sorted(counts.items())),
        "events": records,
    }


def _has_released_receipt(observation: Mapping[str, Any]) -> bool:
    """Accept only explicit released receipt evidence, never a reply string."""
    receipt = observation.get("production_gate_receipt")
    if isinstance(receipt, Mapping):
        return receipt.get("type") == "ProductionGateReceipt" and receipt.get("status") == "released"
    receipts = observation.get("production_gate_receipts")
    return any(
        isinstance(item, Mapping)
        and item.get("type") == "ProductionGateReceipt"
        and item.get("status") == "released"
        for item in (receipts if isinstance(receipts, Sequence) and not isinstance(receipts, (str, bytes)) else ())
    )


def _has_explicit_error(observation: Mapping[str, Any]) -> bool:
    surface = str(observation.get("reply", observation.get("surface", ""))).strip().lower()
    return surface == _ERROR_NORMALIZED or observation.get("explicit_error") == EXPLICIT_ERROR


def check_coverage(manifest: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Check receipt/error coverage without promoting unverified observations."""
    by_id = {str(item.get("id")): item for item in observations}
    results = []
    for event in manifest["events"]:
        observation = by_id.get(event["id"], {})
        receipt = _has_released_receipt(observation)
        explicit_error = _has_explicit_error(observation)
        if event["classification"] == "cognition_only":
            status = "cognition_only" if observation.get("cognitive_trace") is not None else "missing_cognitive_trace"
            covered = status == "cognition_only"
        else:
            status = "receipt" if receipt else "explicit_error" if explicit_error else "missing_surface_evidence"
            covered = receipt or explicit_error
        results.append({"id": event["id"], "classification": event["classification"],
                        "status": status, "covered": covered})
    return {
        "event_count": len(results),
        "covered": sum(item["covered"] for item in results),
        "uncovered": [item["id"] for item in results if not item["covered"]],
        "results": results,
    }


__all__ = ["EXPLICIT_ERROR", "build_manifest", "check_coverage"]


def collect_live_observations(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract only production evidence actually serialized by a corpus run.

    The Phase 8 runner currently records replies and trace *coverage flags*,
    not the underlying receipt or cognitive trace objects.  Coverage flags are
    deliberately not copied into this evidence envelope: a claim that a trace
    exists is not the trace itself.
    """
    raw = report.get("observations")
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return []
    evidence_keys = (
        "reply", "surface", "explicit_error", "production_gate_receipt",
        "production_gate_receipts", "cognitive_trace",
    )
    extracted = []
    for item in raw:
        if not isinstance(item, Mapping):
            continue
        evidence = {"id": item.get("id")}
        for key in evidence_keys:
            if key in item:
                evidence[key] = item[key]
        extracted.append(evidence)
    return extracted


def diagnose_live_manifest(
    report: Mapping[str, Any],
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a fail-closed live-manifest diagnostic.

    ``ready`` is returned only when every manifest event has an accepted
    receipt, canonical explicit error, or (for cognition-only events) an
    actual cognitive trace object.  Missing objects are reported as blocked;
    this function never upgrades the Phase 8 runner's summary flags into
    evidence.
    """
    manifest = build_manifest() if manifest is None else manifest
    observations = collect_live_observations(report)
    coverage = check_coverage(manifest, observations)
    expected_ids = {str(item["id"]) for item in manifest["events"]}
    observed_ids = [str(item.get("id")) for item in observations]
    duplicate_ids = sorted({case_id for case_id in observed_ids if observed_ids.count(case_id) > 1})
    unknown_ids = sorted(set(observed_ids) - expected_ids)
    trace_flags = sum(
        isinstance(item, Mapping) and isinstance(item.get("trace_coverage"), Mapping)
        for item in (report.get("observations") or [])
        if isinstance(report.get("observations"), Sequence)
        and not isinstance(report.get("observations"), (str, bytes))
    )
    actual_traces = sum(item.get("cognitive_trace") is not None for item in observations)
    receipts = sum(_has_released_receipt(item) for item in observations)
    explicit_errors = sum(_has_explicit_error(item) for item in observations)

    blockers = []
    if len(observations) != len(manifest["events"]):
        blockers.append("observation_count_does_not_match_manifest")
    if duplicate_ids:
        blockers.append("duplicate_event_ids")
    if unknown_ids:
        blockers.append("unknown_event_ids")
    if coverage["uncovered"]:
        blockers.append("accepted_production_evidence_missing")
    if trace_flags and actual_traces == 0:
        blockers.append("trace_coverage_flags_are_not_cognitive_trace_objects")

    return {
        "schema": "phase6_live_manifest_diagnostic.v1",
        "status": "ready" if not blockers else "blocked",
        "source_schema": report.get("schema"),
        "protocol_id": report.get("protocol_id"),
        "manifest_event_count": len(manifest["events"]),
        "observed_event_count": len(observations),
        "evidence_inventory": {
            "released_receipts": receipts,
            "explicit_errors": explicit_errors,
            "cognitive_traces": actual_traces,
            "trace_coverage_flags_ignored": trace_flags,
        },
        "blockers": blockers,
        "coverage": coverage,
        "duplicate_ids": duplicate_ids,
        "unknown_ids": unknown_ids,
    }


__all__ += ["collect_live_observations", "diagnose_live_manifest"]
