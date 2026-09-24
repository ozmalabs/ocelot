"""Phase 2 grounding precision/recall measurement.

This is an evaluation-only adapter.  It does not alter routing, retrieval, or
the cognition graph.  The corpus' grounding annotations are collapsed into a
small epistemic label set so that referent grounding is not conflated with
coreference, unknown-world state, or contradiction.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from evaluation.conversational_manifold_phase0 import load_corpus, validate_corpus
from evaluation.phase8_corpus_runner import run_system_under_test


GROUNDING_LABELS = ("referent", "coreference", "unknown", "contradiction")
GROUNDING_CATEGORIES = (
    "selected_graph_faculty",
    "graph_referent",
    "held_topic_or_relation",
    "resolved_discourse_reference",
    "declared_graph_path_unverified",
    "declared_discourse_state_unverified",
    "surface_or_uncertainty_only",
    "non_grounded_control",
)
SOURCE_STATUS_TO_LABEL = {
    "grounded": "referent",
    "partially_grounded": "referent",
    "candidate_grounded": "referent",
    "supported": "referent",
    "unresolved_reference": "coreference",
    "unresolved": "coreference",
    "unknown": "unknown",
    "unavailable_world": "unknown",
    "search_failed": "unknown",
    "contradicted": "contradiction",
}


def expected_grounding_label(event: Mapping[str, Any]) -> str:
    """Return the corpus annotation's explicit Phase 2 epistemic label."""
    status = event.get("grounding_status")
    try:
        return SOURCE_STATUS_TO_LABEL[status]
    except KeyError as exc:
        raise ValueError(f"unsupported corpus grounding status: {status!r}") from exc


def observed_grounding_label(observation: Mapping[str, Any]) -> str:
    """Classify only the runtime grounding status, never the reply text.

    Reply presence and answer-shaped prose are deliberately excluded: a reply
    is not evidence that a referent was grounded.
    """
    status = observation.get("grounding_status")
    try:
        return SOURCE_STATUS_TO_LABEL[status]
    except KeyError as exc:
        raise ValueError(
            f"runtime observation has no recognized grounding status: {status!r}"
        ) from exc


def grounding_cognitive_category(
    event: Mapping[str, Any], observation: Mapping[str, Any]
) -> str:
    """Classify the cognitive source of a grounding decision.

    The category is intentionally provenance-first.  An event annotation such
    as ``graph_path`` is only a *declared* source until the runtime observation
    carries an actual evidence path.  Reply text, reply presence, and a parsed
    noun never select a supported category.  This lets the report distinguish
    recall that is safe to pursue from corpus labels whose graph support has
    not been demonstrated.
    """
    status = observation.get("grounding_status")
    path = str(observation.get("grounding_evidence_path") or "")
    if "selected_graph_faculty" in path:
        return "selected_graph_faculty"
    # An action can be grounded by a substantive Concept node even when it is
    # not a topic lookup or a faculty selection.  Keep this distinct from a
    # corpus-declared graph path: only the runtime path emitted by the
    # communication interpretation proves that the graph referent was used.
    if "Concept.referent" in path:
        return "graph_referent"
    if "HeldAnswer" in path or "RetrievalEvidence" in path:
        return "held_topic_or_relation"
    if ("resolved_referent" in path
            or "ReferenceResolutionEvidence" in path
            or "CurrentTopic.name + DiscourseReferent.concept" in path):
        return "resolved_discourse_reference"
    expected = expected_grounding_label(event)
    if expected != "referent":
        return "non_grounded_control"
    declared = {str(item) for item in (event.get("evidence") or [])}
    if "graph_path" in declared:
        return "declared_graph_path_unverified"
    if "discourse_state" in declared:
        return "declared_discourse_state_unverified"
    return "surface_or_uncertainty_only"


def _scores(rows: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    result: dict[str, dict[str, float | int]] = {}
    for label in GROUNDING_LABELS:
        tp = sum(row["expected_grounding_label"] == label and
                 row["observed_grounding_label"] == label for row in rows)
        fp = sum(row["expected_grounding_label"] != label and
                 row["observed_grounding_label"] == label for row in rows)
        fn = sum(row["expected_grounding_label"] == label and
                 row["observed_grounding_label"] != label for row in rows)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if precision + recall else 0.0)
        result[label] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "support": tp + fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    return result


def measure_grounding(
    corpus: Mapping[str, Any] | None = None,
    observations: list[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Measure four-way grounding precision/recall over the fixed corpus.

    ``observations`` is injectable for deterministic contract tests.  A live
    measurement uses the existing Phase 8 SUT adapter and does not change it.
    """
    if corpus is None:
        corpus = load_corpus()
    errors = validate_corpus(dict(corpus))
    if errors:
        raise ValueError("invalid grounding corpus: " + "; ".join(errors))
    events = list(corpus["events"])
    if observations is None:
        observations = run_system_under_test(corpus)["observations"]
    if len(observations) != len(events):
        raise ValueError("observation count must equal corpus event count")

    rows: list[dict[str, Any]] = []
    for event, observation in zip(events, observations):
        expected = expected_grounding_label(event)
        observed = observed_grounding_label(observation)
        # This invariant is stronger than a textual-answer check: unknown,
        # unresolved, and contradicted events must never be scored as grounded
        # merely because the adapter returned a fluent or non-empty answer.
        unrelated_answer_resolution = (
            expected != "referent" and observed == "referent"
        )
        category = grounding_cognitive_category(event, observation)
        rows.append({
            "id": event["id"],
            "expected_grounding_label": expected,
            "observed_grounding_label": observed,
            "expected_source_status": event["grounding_status"],
            "observed_source_status": observation.get("grounding_status"),
            "reply_present": bool(observation.get("reply_present")),
            "unrelated_answer_resolution": unrelated_answer_resolution,
            "cognitive_category": category,
            "runtime_evidence_path": str(
                observation.get("grounding_evidence_path") or ""),
        })

    expected_counts = Counter(row["expected_grounding_label"] for row in rows)
    observed_counts = Counter(row["observed_grounding_label"] for row in rows)
    confusion = {
        expected: {
            observed: sum(
                row["expected_grounding_label"] == expected and
                row["observed_grounding_label"] == observed
                for row in rows
            )
            for observed in GROUNDING_LABELS
        }
        for expected in GROUNDING_LABELS
    }
    violations = [row["id"] for row in rows if row["unrelated_answer_resolution"]]
    category_report: dict[str, dict[str, Any]] = {}
    for category in GROUNDING_CATEGORIES:
        selected = [row for row in rows if row["cognitive_category"] == category]
        category_report[category] = {
            "support": len(selected),
            "false_negative": sum(
                row["expected_grounding_label"] == "referent"
                and row["observed_grounding_label"] != "referent"
                for row in selected),
            "false_positive": sum(
                row["expected_grounding_label"] != "referent"
                and row["observed_grounding_label"] == "referent"
                for row in selected),
            "runtime_evidence_verified": sum(
                bool(row["runtime_evidence_path"]) for row in selected),
        }
    return {
        "schema": "phase2_grounding_precision_recall.v1",
        "corpus_event_count": len(rows),
        "labels": list(GROUNDING_LABELS),
        "label_definition": {
            "referent": "grounded or partially grounded referent evidence",
            "coreference": "unresolved or unresolved-reference evidence",
            "unknown": "unknown referent or unavailable world",
            "contradiction": "explicitly contradicted grounding",
        },
        "expected_counts": dict(expected_counts),
        "observed_counts": dict(observed_counts),
        "confusion_matrix": confusion,
        "per_label": _scores(rows),
        "macro": {
            "precision": sum(_scores(rows)[label]["precision"] for label in GROUNDING_LABELS) / len(GROUNDING_LABELS),
            "recall": sum(_scores(rows)[label]["recall"] for label in GROUNDING_LABELS) / len(GROUNDING_LABELS),
            "f1": sum(_scores(rows)[label]["f1"] for label in GROUNDING_LABELS) / len(GROUNDING_LABELS),
        },
        "unrelated_answer_resolution": {
            "violations": violations,
            "count": len(violations),
            "passed": not violations,
        },
        "cognitive_category_analysis": category_report,
        "observations": rows,
    }


if __name__ == "__main__":
    import json
    import sys

    report = measure_grounding()
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
