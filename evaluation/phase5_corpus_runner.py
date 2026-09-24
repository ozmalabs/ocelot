"""Phase 5 graph-native recurrence measurement over the fixed corpus.

This module is an evaluation adapter.  It does not create learning data,
canonicalise surface text, or alter the conversation substrate.  The runtime
graph remains the authority for gap identity and recurrence; this adapter only
records newly observed graph nodes and reads the existing Phase 5 nodes back.

The fixed Phase 0 corpus is not a learning corpus.  In particular, it does
not contain repeated graph-native gap observations, correction evidence, or
repair verification events.  The report therefore keeps ordinary gap filings
separate from production recurrence and marks recurrence unavailable when the
required evidence is absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping

from evaluation.conversational_manifold_phase0 import FIXTURE, load_corpus
from evaluation.phase8_corpus_runner import _speech_act


REPORT_SCHEMA = "phase5_graph_native_recurrence_corpus_report.v1"
PROTOCOL_ID = "phase5g-fixed-phase0-corpus-recurrence-v1"
IDENTITY_SOURCE = "SelfConcern.attrs.gap_identity"
RECURRENCE_NODE_TYPE = "GapRecurrence"
ASSESSMENT_NODE_TYPE = "GapLearningAssessment"


def learning_observation_contract(corpus: Mapping[str, Any]) -> dict[str, Any]:
    """Describe explicit Phase 5 evidence present in corpus event metadata.

    The communication corpus predates the Phase 5 learning protocol.  This
    check is intentionally structural: it never treats a repeated word or a
    similar signal as a stable learning identity.
    """
    events = list(corpus.get("events") or [])
    required = ("gap_identity", "learning_stage", "verification_status")
    observations = []
    for event in events:
        # The production-shaped overlay keeps learning metadata in an explicit
        # nested evidence envelope so the base communication corpus remains
        # unchanged.  Legacy top-level fields remain accepted for compatibility.
        evidence = event.get("learning_observation")
        evidence = evidence if isinstance(evidence, Mapping) else event
        if all(evidence.get(field) not in (None, "") for field in required):
            observations.append((event, evidence))
    if observations:
        return {
            "status": "measured",
            "observation_count": len(observations),
            "required_fields": list(required),
            "event_ids": [str(event["id"]) for event, _ in observations],
            "evidence_source": "explicit_event_learning_observation",
        }
    return {
        "status": "unavailable",
        "observation_count": 0,
        "required_fields": list(required),
        "event_ids": [],
        "evidence_source": "corpus_event_metadata",
        "reason": (
            "The corpus contains no explicit stable gap identity plus "
            "learning-stage and verification observation. No production "
            "recurrence claim is permitted from surface repetition."
        ),
    }


def _node_id(node: Any) -> int:
    return int(node.value)


def _attrs(agent: Any, node: Any) -> dict[str, Any]:
    return dict(agent.s.node(node)["attrs"])


def _node_map(agent: Any, node_type: str) -> dict[int, Any]:
    return {_node_id(node): node for node in agent.s.nodes(node_type)}


def _identity_map(agent: Any, node_type: str) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for node in agent.s.nodes(node_type):
        identity = _attrs(agent, node).get("gap_identity")
        if identity not in (None, ""):
            grouped[str(identity)].append(node)
    return grouped


def _run_event(agent: Any, event: Mapping[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    """Run one corpus event and return its reply, error, and new gap evidence."""
    before = _node_map(agent, "SelfConcern")
    error = ""
    reply = ""
    try:
        setup = event.get("setup") or {}
        for held in setup.get("held_answers") or []:
            agent._persist_held_answer(str(held["topic"]), str(held["answer"]))
        reply = str(agent.converse(
            event["signal"],
            speech_act=_speech_act(event),
            context={
                "interaction_mode": event["event_mode"],
                **({"learning_observation": event["learning_observation"]}
                   if isinstance(event.get("learning_observation"), Mapping)
                   else {}),
            },
        ) or "")
    except Exception as exc:  # record evaluation failure without hiding it
        error = f"{type(exc).__name__}: {exc}"

    evidence: list[dict[str, Any]] = []
    by_identity: dict[str, dict[str, Any]] = {}
    for node_id, node in _node_map(agent, "SelfConcern").items():
        if node_id in before:
            continue
        attrs = _attrs(agent, node)
        identity = attrs.get("gap_identity")
        if identity in (None, ""):
            continue
        key = str(identity)
        record = by_identity.setdefault(key, {
            "event_id": str(event["id"]),
            "gap_identity": key,
            "gap_identity_schema": attrs.get("gap_identity_schema"),
            "kind": attrs.get("kind"),
            "source": attrs.get("source"),
            "status": attrs.get("status"),
            "event_stage": attrs.get("event_stage"),
            "self_concern_node_ids": [],
        })
        # A single event may cause several native settling firings. Preserve
        # all graph provenance, but count the stable identity once for this
        # event so rule-settling cannot manufacture recurrence pressure.
        record["self_concern_node_ids"].append(node_id)
    for record in by_identity.values():
        record["self_concern_node_id"] = record["self_concern_node_ids"][0]
        evidence.append(record)
    return reply, {"error": error}, evidence


def _recurrence_summary(agent: Any, observed: list[dict[str, Any]]) -> dict[str, Any]:
    by_identity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in observed:
        by_identity[item["gap_identity"]].append(item)

    recurrence_nodes = _identity_map(agent, RECURRENCE_NODE_TYPE)
    assessment_nodes = _identity_map(agent, ASSESSMENT_NODE_TYPE)
    identities: list[dict[str, Any]] = []
    measured_recurrences = 0
    for identity in sorted(by_identity):
        observations = by_identity[identity]
        recurrence = recurrence_nodes.get(identity, [])
        assessment = assessment_nodes.get(identity, [])
        recurrence_attrs = _attrs(agent, recurrence[0]) if recurrence else {}
        assessment_attrs = _attrs(agent, assessment[0]) if assessment else {}
        count = float(recurrence_attrs.get("recurrence_count", 0.0) or 0.0)
        qualifies = len(observations) >= 2 and count >= 2.0
        measured_recurrences += int(qualifies)
        identities.append({
            # This is the existing graph identity.  The adapter never derives
            # an identity from text or replaces it with an event-local key.
            "gap_identity": identity,
            "identity_source": IDENTITY_SOURCE,
            "observation_count": len(observations),
            "event_ids": [item["event_id"] for item in observations],
            "self_concern_node_ids": [item["self_concern_node_id"] for item in observations],
            "recurrence": {
                "status": "measured" if recurrence else "unavailable",
                "node_type": RECURRENCE_NODE_TYPE,
                "node_ids": [_node_id(node) for node in recurrence],
                "recurrence_count": count if recurrence else None,
                "priority": recurrence_attrs.get("priority"),
                "lifecycle_status": recurrence_attrs.get("status"),
            },
            "assessment": {
                "status": "measured" if assessment else "unavailable",
                "node_type": ASSESSMENT_NODE_TYPE,
                "node_ids": [_node_id(node) for node in assessment],
                "promotion_status": assessment_attrs.get("promotion_status"),
                "failed_repair_count": assessment_attrs.get("failed_repair_count"),
            },
            "recurrence_qualification": qualifies,
        })

    if measured_recurrences:
        status = "measured"
        reason = "At least one stable graph identity has repeated graph observations and a native recurrence node."
    else:
        status = "unavailable"
        reason = (
            "The corpus produced no identity with two observed SelfConcern "
            "nodes and a native GapRecurrence count of at least two. This "
            "does not establish production recurrence."
        )
    return {
        "status": status,
        "identity_source": IDENTITY_SOURCE,
        "recurrence_node_type": RECURRENCE_NODE_TYPE,
        "assessment_node_type": ASSESSMENT_NODE_TYPE,
        "observed_identity_count": len(identities),
        "measured_recurrence_identity_count": measured_recurrences,
        "identities": identities,
        "reason": reason,
    }


def production_recurrence_diagnostic(
    learning: Mapping[str, Any],
    recurrence: Mapping[str, Any],
) -> dict[str, Any]:
    """Gate a production claim on both corpus and native recurrence evidence.

    ``GapRecurrence`` remains the recurrence authority.  The corpus-side
    learning observation contract is a separate admission requirement: native
    recurrence alone cannot turn a communication corpus into a production
    learning claim.  This helper reports the missing evidence explicitly and
    does not create or persist any learning state.
    """
    missing_evidence: list[str] = []
    if learning.get("status") != "measured":
        missing_evidence.append("learning_observation_contract")
    if recurrence.get("status") != "measured":
        missing_evidence.append("repeated_graph_native_recurrence")

    if missing_evidence:
        reasons: list[str] = []
        if "learning_observation_contract" in missing_evidence:
            reasons.append("the corpus lacks the required learning observations")
        if "repeated_graph_native_recurrence" in missing_evidence:
            reasons.append(
                "the corpus did not produce a measured repeated graph-native gap identity"
            )
        return {
            "status": "unavailable",
            "claim_permitted": False,
            "missing_evidence": missing_evidence,
            "reason": "; ".join(reasons) + ".",
        }

    return {
        "status": "measured",
        "claim_permitted": True,
        "missing_evidence": [],
        "reason": recurrence.get(
            "reason",
            "The corpus contains the required learning observations and native recurrence evidence.",
        ),
    }


def run_phase5_recurrence_measurement(
    corpus: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the existing system against the corpus and report Phase 5 evidence."""
    using_fixed_fixture = corpus is None
    if corpus is None:
        corpus = load_corpus()
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    started = time.perf_counter()
    observations: list[dict[str, Any]] = []
    gap_observations: list[dict[str, Any]] = []
    for event in corpus["events"]:
        event_started = time.perf_counter()
        reply, result, evidence = _run_event(agent, event)
        gap_observations.extend(evidence)
        observations.append({
            "event_id": str(event["id"]),
            "reply_present": bool(reply.strip()),
            "error": result["error"] or None,
            "new_gap_observation_count": len(evidence),
            "elapsed_ms": (time.perf_counter() - event_started) * 1000.0,
        })

    learning = learning_observation_contract(corpus)
    recurrence = _recurrence_summary(agent, gap_observations)
    production = production_recurrence_diagnostic(learning, recurrence)

    raw = FIXTURE.read_bytes() if using_fixed_fixture else None
    # Identity comparison is graph-native; corpus hashing is only provenance.
    corpus_provenance = {"event_count": len(corpus["events"])}
    if raw is not None:
        corpus_provenance.update({"path": str(FIXTURE), "sha256": hashlib.sha256(raw).hexdigest()})
    return {
        "schema": REPORT_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "status": "measured" if observations else "unavailable",
        "corpus": corpus_provenance,
        "system_under_test": {
            "system": "conversational_manifold",
            "elapsed_ms": (time.perf_counter() - started) * 1000.0,
        },
        "learning_observation_evidence": learning,
        "observations": observations,
        "gap_observations": gap_observations,
        "recurrence": recurrence,
        "production_recurrence": production,
    }


def write_report(path: Path, corpus: Mapping[str, Any] | None = None) -> dict[str, Any]:
    report = run_phase5_recurrence_measurement(corpus)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = write_report(args.output)
    print(json.dumps({
        "output": str(args.output),
        "status": report["status"],
        "production_recurrence": report["production_recurrence"],
        "observed_identity_count": report["recurrence"]["observed_identity_count"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
