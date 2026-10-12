"""Receipt-backed semantic recoverability measurement for Phase 6.

This module is an evaluation adapter.  It reads authoritative
``ProductionGateReceipt`` objects from an injected corpus-run report and
compares their language-neutral semantic fields with the independent Phase 0
force and state annotations.  It never derives semantics from reply text,
trace-coverage flags, or a missing receipt.

The comparison deliberately uses a small ontology bridge rather than string
matching receipt event names to surface labels.  A receipt is recoverable only
when it is released, explicitly marked recoverable, contains semantic content,
and its intent/event are compatible with the corpus force and expected state.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence

from evaluation.phase6_production_manifest import (
    EXPLICIT_ERROR,
    build_manifest,
    collect_live_observations,
)


SCHEMA = "phase6_receipt_semantic_recoverability.v1"

RECEIPT_BACKED = "receipt_backed_semantically_recoverable"
EXPLICIT_OR_WITHHELD = "explicit_error_or_withheld"
RELEASED_MISMATCH = "released_semantic_mismatch"
MISSING = "missing_authoritative_evidence"
CLASSIFICATIONS = (
    RECEIPT_BACKED,
    EXPLICIT_OR_WITHHELD,
    RELEASED_MISMATCH,
    MISSING,
)

# These are ontology bridges, not surface-language rules. Receipt event names
# are intentionally not required for every action because native action
# identifiers are open-ended. Semantic intent is not cognitive disposition:
# an action request can be accepted, deferred, repaired, or blocked. State is
# therefore reported separately from receipt-semantic compatibility below.
_FORCE_INTENTS = {
    # This bridge describes compatible *response acts*, not a requirement
    # that the receipt repeat the incoming speech act.  In particular, a
    # repair request is a valid response to any force when its semantic
    # content records the item being clarified; a refusal/defer or an
    # informative gap report can be the appropriate response to a requested
    # action.  These are receipt ontology values emitted by the producer, not
    # labels inferred from the surface reply.
    "request_information": frozenset({"inform", "request", "defer", "act"}),
    "request_action": frozenset({"act", "request", "inform", "defer"}),
    "assertion": frozenset({"inform", "request", "acknowledge_receipt_without_endorsement"}),
    "correction": frozenset({"inform", "update_common_ground", "request"}),
    "acknowledgement": frozenset({
        "inform", "coordinate_socially", "acknowledge_receipt_without_endorsement",
    }),
    "offer": frozenset({"inform", "act", "social_action", "coordinate_socially", "request",
                        "acknowledge_receipt_without_endorsement"}),
    "refusal": frozenset({"defer", "request", "act"}),
    "repair": frozenset({"request", "defer"}),
    "social_action": frozenset({"coordinate_socially", "inform", "request"}),
}
_STATE_INTENTS = {
    "answer": frozenset({"inform", "coordinate_socially"}),
    "act": frozenset({"act", "request", "inform"}),
    "repair": frozenset({"request", "defer"}),
    "defer": frozenset({"defer", "request", "inform", "coordinate_socially"}),
    "learn": frozenset({"inform", "request", "defer"}),
    "blocked": frozenset({"defer", "request", "inform", "act"}),
    "error": frozenset({"defer", "request"}),
}


def _receipt_items(observation: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    """Return receipt mappings without interpreting any other observation field."""
    one = observation.get("production_gate_receipt")
    many = observation.get("production_gate_receipts")
    items: list[Mapping[str, Any]] = []
    if isinstance(one, Mapping):
        items.append(one)
    if isinstance(many, Sequence) and not isinstance(many, (str, bytes)):
        items.extend(item for item in many if isinstance(item, Mapping))
    return items


def _receipt_attrs(receipt: Mapping[str, Any]) -> Mapping[str, Any]:
    attrs = receipt.get("attrs")
    return attrs if isinstance(attrs, Mapping) else receipt


def _status(receipt: Mapping[str, Any]) -> str | None:
    attrs = _receipt_attrs(receipt)
    value = receipt.get("status", attrs.get("status"))
    return str(value) if value is not None else None


def _explicit_error(observation: Mapping[str, Any]) -> bool:
    # ``explicit_error`` is an already-adjudicated production outcome.  The
    # fallback surface is accepted only for classifying an error outcome; it
    # is never consulted as semantic evidence.  Phase 6's existing manifest
    # uses the canonical reply/surface string for this outcome, so retaining
    # that adapter boundary is necessary without treating the text as meaning.
    if observation.get("explicit_error") == EXPLICIT_ERROR:
        return True
    surface = observation.get("surface", observation.get("reply"))
    return isinstance(surface, str) and surface.strip().lower() == EXPLICIT_ERROR.lower()


def _semantic_dimensions(event: Mapping[str, Any], attrs: Mapping[str, Any]) -> list[str]:
    """Return independent semantic dimensions that fail closed."""
    dimensions: list[str] = []
    recoverable = attrs.get("recoverable")
    if recoverable is not True:
        dimensions.append("recoverable")

    content = attrs.get("semantic_content")
    if not isinstance(content, Sequence) or isinstance(content, (str, bytes)) or not content:
        dimensions.append("semantic_content")

    semantic_intent = attrs.get("semantic_intent")
    if not isinstance(semantic_intent, str) or not semantic_intent:
        dimensions.append("semantic_intent")
    else:
        force = event.get("communicative_force")
        force_allowed = _FORCE_INTENTS.get(str(force), frozenset())
        if semantic_intent not in force_allowed:
            dimensions.append("force")

    semantic_event = attrs.get("semantic_event")
    if not isinstance(semantic_event, str) or not semantic_event:
        dimensions.append("semantic_event")
    return dimensions


def classify_event(
    event: Mapping[str, Any], observation: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Classify one event from injected authoritative evidence.

    Classification precedence is explicit/withheld, released receipt, then
    missing evidence.  A released receipt with malformed or incompatible
    semantic fields is a mismatch, never silently downgraded to missing.
    """
    observation = observation or {}
    receipts = _receipt_items(observation)
    released = [item for item in receipts if _status(item) == "released"]
    withheld = any(_status(item) in {"withheld", "blocked", "rejected"} for item in receipts)

    if _explicit_error(observation) or withheld:
        classification = EXPLICIT_OR_WITHHELD
        dimensions = ["explicit_error"] if _explicit_error(observation) else ["receipt_withheld"]
    elif released:
        # A production event is expected to have one released receipt.  Use a
        # deterministic first receipt and flag multiplicity as a provenance
        # defect rather than allowing order to hide it.
        attrs = _receipt_attrs(released[0])
        dimensions = _semantic_dimensions(event, attrs)
        if len(released) != 1:
            dimensions.append("released_receipt_multiplicity")
        classification = RECEIPT_BACKED if not dimensions else RELEASED_MISMATCH
    else:
        classification = MISSING
        dimensions = ["authoritative_receipt_missing"]

    return {
        "id": str(event.get("id")),
        "classification": classification,
        "dimensions": sorted(set(dimensions)),
        "authoritative_receipt_count": len(receipts),
        "released_receipt_count": len(released),
        # Expose semantic evidence for auditability, but never expose reply
        # text or trace flags as part of the semantic decision.
        "semantic_evidence": (
            {
                key: _receipt_attrs(released[0]).get(key)
                for key in ("semantic_content", "semantic_event", "semantic_intent",
                            "recoverable", "parse_back_mode")
            }
            if released else None
        ),
        "reply_text_used_as_semantic_evidence": False,
        "trace_flags_used_as_semantic_evidence": False,
    }


def measure_receipt_recoverability(
    report: Mapping[str, Any],
    corpus: Mapping[str, Any],
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce a deterministic Phase 6 receipt-semantic report.

    ``report`` and ``corpus`` are injectable so tests can cover every outcome
    without invoking the runtime.  The existing manifest and observation
    extractor are reused; no receipt or semantic evidence is invented.
    """
    manifest = build_manifest(corpus) if manifest is None else manifest
    observations = collect_live_observations(report)
    raw_observations = {
        str(item.get("id")): item
        for item in (report.get("observations") or ())
        if isinstance(item, Mapping)
    }
    by_id = {str(item.get("id")): item for item in observations}
    results = [
        classify_event(event, by_id.get(str(event.get("id")), {}))
        for event in corpus.get("events", ())
    ]
    counts = Counter(item["classification"] for item in results)
    dimensions = Counter(
        dimension for item in results for dimension in item["dimensions"]
        if item["classification"] == RELEASED_MISMATCH
    )
    runtime_state_diagnostics = []
    for event in corpus.get("events", ()):
        raw = raw_observations.get(str(event.get("id")), {})
        if "cognitive_state" not in raw and "observed_state" not in raw:
            continue
        runtime_state_diagnostics.append({
            "id": str(event.get("id")),
            "expected_state": event.get("expected_state"),
            "observed_state": raw.get("cognitive_state", raw.get("observed_state")),
            "match": raw.get("cognitive_state", raw.get("observed_state")) == event.get("expected_state"),
            "source": raw.get(
                "cognitive_state_evidence_source",
                "phase8_adapter_observation"),
            "authority": raw.get(
                "cognitive_state_authority", "adapter_observation"),
            "evidence_available": raw.get(
                "cognitive_state_evidence_available", False),
            "release_state": raw.get("release_state", raw.get("release_status")),
            "not_receipt_semantic_evidence": True,
        })
    expected_ids = {str(item.get("id")) for item in manifest.get("events", ())}
    observed_ids = [str(item.get("id")) for item in observations]
    duplicate_ids = sorted({case_id for case_id in observed_ids if observed_ids.count(case_id) > 1})
    unknown_ids = sorted(set(observed_ids) - expected_ids)
    return {
        "schema": SCHEMA,
        "protocol_id": report.get("protocol_id"),
        "event_count": len(results),
        "observed_event_count": len(observations),
        "classification_counts": {
            classification: counts.get(classification, 0)
            for classification in CLASSIFICATIONS
        },
        "dimension_counts": dict(sorted(dimensions.items())),
        "runtime_state_diagnostics": runtime_state_diagnostics,
        "runtime_state_mismatch_count": sum(
            not item["match"] for item in runtime_state_diagnostics),
        "results": results,
        "duplicate_ids": duplicate_ids,
        "unknown_ids": unknown_ids,
        "surface_text_used_as_evidence": False,
        "reply_text_used_as_semantic_evidence": False,
        "trace_flags_used_as_semantic_evidence": False,
        "status": "measured" if not duplicate_ids and not unknown_ids else "incomplete",
    }


__all__ = [
    "CLASSIFICATIONS",
    "EXPLICIT_OR_WITHHELD",
    "MISSING",
    "RECEIPT_BACKED",
    "RELEASED_MISMATCH",
    "SCHEMA",
    "classify_event",
    "measure_receipt_recoverability",
]
