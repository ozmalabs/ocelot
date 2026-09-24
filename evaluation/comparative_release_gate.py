"""Phase 8A comparative evaluation contract and release gate.

This module is deliberately evaluation-only.  It does not invoke a model,
alter runtime cognition, or turn qualitative expectations into scores.  A
runner supplies measured scorecards with evidence references; this module
checks their completeness and performs bounded interval comparisons.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


SCHEMA = "comparative_cognition_evaluation.v1"
TARGET = "conversational_manifold"
CORPUS_PROTOCOL_ID = "communication_event_corpus.v1"

BASELINES = (
    "eliza_floor",
    "small_llm",
    "modern_llm",
    "base_human",
    "advanced_human",
)

DIMENSIONS = (
    "interpretation",
    "grounding",
    "action",
    "repair",
    "memory",
    "learning",
    "calibration",
    "provenance",
    "cost",
)

BASELINE_DESCRIPTIONS = {
    "eliza_floor": "Pattern/reflection floor with no general cognitive state claim.",
    "small_llm": "Small language-model reference under a fixed, documented budget.",
    "modern_llm": "Modern general-purpose language-model reference under a fixed protocol.",
    "base_human": "Human reference sampled without specialist training for the task.",
    "advanced_human": "Human reference with demonstrated task expertise.",
}

REFERENCE_PROTOCOLS = {
    "eliza_floor": {"collection_mode": "deterministic scripted adapter", "adapter_entrypoint": "evaluation.reference_adapters.eliza_floor", "required_observation": "one output per corpus event plus failure trace", "annotation_source": "protocol adjudication against fixed case labels"},
    "small_llm": {"collection_mode": "fixed-model, fixed-prompt, repeated seeded runs", "adapter_entrypoint": "evaluation.reference_adapters.small_llm", "required_observation": "one output and raw request/response record per corpus event", "annotation_source": "blinded protocol adjudication plus raw model trace"},
    "modern_llm": {"collection_mode": "fixed-model, fixed-prompt, repeated seeded runs", "adapter_entrypoint": "evaluation.reference_adapters.modern_llm", "required_observation": "one output and raw request/response record per corpus event", "annotation_source": "blinded protocol adjudication plus raw model trace"},
    "base_human": {"collection_mode": "blinded human task session", "adapter_entrypoint": "evaluation.reference_adapters.base_human", "required_observation": "one response and annotation record per corpus event", "annotation_source": "blinded dual annotation with adjudication"},
    "advanced_human": {"collection_mode": "blinded expert human task session", "adapter_entrypoint": "evaluation.reference_adapters.advanced_human", "required_observation": "one response and annotation record per corpus event", "annotation_source": "blinded dual annotation with adjudication"},
}

MEASUREMENT_STATUSES = ("measured", "unavailable", "indeterminate")


@dataclass(frozen=True)
class DimensionMeasurement:
    dimension: str
    mean: float
    n: int
    ci95_low: float
    ci95_high: float
    evidence_refs: tuple[str, ...]
    raw_metric: str
    notes: str = ""
    status: str = "measured"

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.dimension not in DIMENSIONS:
            errors.append(f"unknown dimension: {self.dimension}")
        if self.status not in MEASUREMENT_STATUSES:
            errors.append(f"{self.dimension}: invalid status {self.status!r}")
        if self.status != "measured":
            if not self.notes.strip():
                errors.append(f"{self.dimension}: unavailable/indeterminate requires notes")
            if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
                errors.append(f"{self.dimension}: evidence_refs must identify the unavailable evidence")
            return errors
        if not 0.0 <= self.mean <= 1.0:
            errors.append(f"{self.dimension}: mean must be in [0, 1]")
        if self.n < 1:
            errors.append(f"{self.dimension}: n must be positive")
        if not 0.0 <= self.ci95_low <= self.mean <= self.ci95_high <= 1.0:
            errors.append(f"{self.dimension}: invalid confidence interval")
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            errors.append(f"{self.dimension}: evidence_refs must be non-empty")
        if not self.raw_metric.strip():
            errors.append(f"{self.dimension}: raw_metric is required")
        return errors


@dataclass(frozen=True)
class Scorecard:
    system: str
    protocol_id: str
    measurements: tuple[DimensionMeasurement, ...]
    reference_class: str = ""
    collection_status: str = "measured"
    adapter_entrypoint: str = ""
    run_id: str = ""
    annotation_protocol: str = ""

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.system.strip():
            errors.append("system is required")
        if not self.protocol_id.strip():
            errors.append(f"{self.system}: protocol_id is required")
        if self.collection_status not in MEASUREMENT_STATUSES:
            errors.append(f"{self.system}: invalid collection_status {self.collection_status!r}")
        if self.system in BASELINES and self.reference_class != self.system:
            errors.append(f"{self.system}: reference_class must identify the baseline")
        seen: set[str] = set()
        for measurement in self.measurements:
            if measurement.dimension in seen:
                errors.append(f"{self.system}: duplicate dimension {measurement.dimension}")
            seen.add(measurement.dimension)
            errors.extend(f"{self.system}: {error}" for error in measurement.validate())
        missing = set(DIMENSIONS) - seen
        errors.extend(f"{self.system}: missing dimension {dimension}" for dimension in sorted(missing))
        return errors

    def by_dimension(self) -> dict[str, DimensionMeasurement]:
        return {measurement.dimension: measurement for measurement in self.measurements}


def comparison(target: DimensionMeasurement, reference: DimensionMeasurement) -> str:
    """Compare higher-is-better normalized capability intervals.

    ``cost`` is intentionally normalized as efficiency/cost-effectiveness by
    the protocol.  Raw latency, tokens, dollars, and RSS remain in the
    evidence referenced by the measurement and are never silently inverted.
    """
    if target.status != "measured" or reference.status != "measured":
        return "unavailable"
    if target.ci95_low > reference.ci95_high:
        return "above"
    if target.ci95_high < reference.ci95_low:
        return "below"
    return "indeterminate"


def _coerce_measurement(value: Mapping[str, Any]) -> DimensionMeasurement:
    return DimensionMeasurement(
        dimension=str(value["dimension"]),
        mean=float(value["mean"]),
        n=int(value["n"]),
        ci95_low=float(value["ci95_low"]),
        ci95_high=float(value["ci95_high"]),
        evidence_refs=tuple(str(ref) for ref in value.get("evidence_refs", ())),
        raw_metric=str(value.get("raw_metric", "")),
        notes=str(value.get("notes", "")),
        status=str(value.get("status", "measured")),
    )


def scorecard_from_dict(value: Mapping[str, Any]) -> Scorecard:
    return Scorecard(
        system=str(value["system"]),
        protocol_id=str(value["protocol_id"]),
        measurements=tuple(_coerce_measurement(item) for item in value.get("measurements", ())),
        reference_class=str(value.get("reference_class", "")),
        collection_status=str(value.get("collection_status", "measured")),
        adapter_entrypoint=str(value.get("adapter_entrypoint", "")),
        run_id=str(value.get("run_id", "")),
        annotation_protocol=str(value.get("annotation_protocol", "")),
    )


def protocol_contract() -> dict[str, Any]:
    """Return the versioned, model-agnostic protocol contract."""
    return {
        "schema": SCHEMA,
        "target": TARGET,
        "baselines": [
            {"id": baseline, "description": BASELINE_DESCRIPTIONS[baseline]}
            for baseline in BASELINES
        ],
        "dimensions": list(DIMENSIONS),
        "corpus_protocol": {
            "id": CORPUS_PROTOCOL_ID,
            "fixture": "tests/fixtures/conversational_manifold/phase0_events.json",
            "event_count": 74,
            "case_binding": "all corpus event IDs are required; exclusions must be recorded",
        },
        "reference_protocols": [
            {"id": baseline, **REFERENCE_PROTOCOLS[baseline]}
            for baseline in BASELINES
        ],
        "score_semantics": {
            "range": [0.0, 1.0],
            "direction": "higher_is_better",
            "cost": "normalized cost-effectiveness; retain raw resource metrics in evidence",
            "confidence": "95% interval supplied by the measurement protocol; no interval is fabricated here",
            "availability": "measured, unavailable, or indeterminate; unavailable is not zero",
        },
        "required_evidence": [
            "fixed_case_or_task_ids",
            "raw_metric_or_annotation_record",
            "provenance_reference",
            "sample_count",
        ],
    }


def evaluate_release_gate(
    scorecards: Iterable[Scorecard], *, target: str = TARGET
) -> dict[str, Any]:
    """Validate scorecards and produce a non-authoritative release decision."""
    scorecard_list = list(scorecards)
    cards = {card.system: card for card in scorecard_list}
    required = (target,) + BASELINES
    errors: list[str] = []
    for system in required:
        if system not in cards:
            errors.append(f"missing scorecard: {system}")
        else:
            errors.extend(cards[system].validate())
    duplicate_systems = len(cards) != len(scorecard_list)
    if duplicate_systems:
        errors.append("duplicate scorecard system")

    comparisons: dict[str, dict[str, str]] = {}
    target_card = cards.get(target)
    if target_card is not None and not target_card.validate():
        target_measurements = target_card.by_dimension()
        for baseline in BASELINES:
            reference = cards.get(baseline)
            if reference is None or reference.validate():
                continue
            comparisons[baseline] = {
                dimension: comparison(target_measurements[dimension], reference.by_dimension()[dimension])
                for dimension in DIMENSIONS
            }

    regressions = [
        {"baseline": baseline, "dimension": dimension}
        for baseline, dimensions in comparisons.items()
        for dimension, result in dimensions.items()
        if result == "below"
    ]
    complete = not errors
    empirically_complete = complete and all(
        measurement.status == "measured"
        for card in scorecard_list
        for measurement in card.measurements
    )
    return {
        "schema": SCHEMA,
        "target": target,
        "status": "ready" if empirically_complete and not regressions else "blocked",
        "complete": complete,
        "empirically_complete": empirically_complete,
        "errors": errors,
        "comparisons": comparisons,
        "regressions": regressions,
        "next_bottleneck": _next_bottleneck(comparisons, errors),
    }


def comparison_summary(
    scorecards: Iterable[Scorecard], *, target: str = TARGET
) -> dict[str, Any]:
    """Summarize whether each required reference is actually comparable.

    This is a reporting aid, not a scoring path.  In particular, an
    unavailable reference is reported as unavailable/not_comparable rather
    than being converted to zero or treated as evidence of superiority.
    """
    cards = {card.system: card for card in scorecards}
    target_card = cards.get(target)
    target_valid = target_card is not None and not target_card.validate()
    result: dict[str, Any] = {
        "target": target,
        "target_status": (
            "measured" if target_valid and target_card.collection_status == "measured"
            else "unavailable" if target_card is None or target_card.collection_status == "unavailable"
            else "indeterminate"
        ),
        "baselines": {},
    }
    for baseline in BASELINES:
        reference = cards.get(baseline)
        if reference is None:
            result["baselines"][baseline] = {
                "collection_status": "missing",
                "comparison_status": "missing",
                "reason": "No scorecard was supplied; no result inferred.",
                "dimensions": {},
            }
            continue
        valid = not reference.validate()
        if not valid:
            status = "invalid"
            reason = "Scorecard validation failed; inspect release_gate.errors."
        elif reference.collection_status != "measured":
            status = reference.collection_status
            reason = "Reference was not measured under this protocol; no result inferred."
        elif not target_valid or target_card.collection_status != "measured":
            status = "not_comparable"
            reason = "Target was not measured under this protocol; no result inferred."
        else:
            status = "measured"
            reason = "Interval comparison is available for all measured dimensions."
        dimensions = {}
        if (valid and target_valid and
                reference.collection_status == "measured" and
                target_card.collection_status == "measured"):
            dimensions = {
                dimension: comparison(target_card.by_dimension()[dimension], reference.by_dimension()[dimension])
                for dimension in DIMENSIONS
            }
        result["baselines"][baseline] = {
            "collection_status": reference.collection_status,
            "comparison_status": status,
            "reason": reason,
            "dimensions": dimensions,
        }
    return result


def _next_bottleneck(comparisons: Mapping[str, Mapping[str, str]], errors: list[str]) -> str:
    if errors:
        return "complete_missing_scorecard_or_evidence"
    for baseline in BASELINES:
        dimensions = comparisons.get(baseline, {})
        for dimension in DIMENSIONS:
            if dimensions.get(dimension) == "below":
                return dimension
    for baseline in BASELINES:
        dimensions = comparisons.get(baseline, {})
        for dimension in DIMENSIONS:
            if dimensions.get(dimension) == "indeterminate":
                return dimension
    return "none"
