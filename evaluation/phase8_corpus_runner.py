"""Reproducible Phase 8 system-under-test run over the Phase 0 corpus.

This is an evaluation adapter only.  It reads the existing communication
corpus, invokes the public conversation entry point, and records observations;
it does not alter cognition or infer missing baseline results.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Mapping

from evaluation.comparative_release_gate import (
    BASELINES,
    DIMENSIONS,
    DimensionMeasurement,
    Scorecard,
    TARGET,
    comparison_summary,
    evaluate_release_gate,
    scorecard_from_dict,
)
from evaluation.conversational_manifold_phase0 import FIXTURE, load_corpus


REPORT_SCHEMA = "phase8_sut_corpus_report.v2"
PROTOCOL_ID = "phase8a-fixed-phase0-corpus-v3"
ERROR_SURFACES = {"error: no communicative response could be generated"}
FORCE_ALIASES = {
    "assertion": "assertion_or_correction",
    "correction": "assertion_or_correction",
    "offer": "social_action",
    "refusal": "repair_or_defer",
}
_GROUNDED_EXPECTED = {"grounded", "partially_grounded"}
_GROUNDED_OBSERVED = {"candidate_grounded", "grounded", "partially_grounded", "supported"}


def grounding_precision_recall(observations: list[Mapping[str, Any]],
                               corpus: Mapping[str, Any]) -> dict[str, Any]:
    """Measure grounding as a binary evidence decision over every event.

    The prior score used only cases expected to be grounded, which could not
    expose false-positive answers to unknown or unavailable-world requests.
    This contract deliberately retains those negatives in the denominator.
    """
    counts = {"true_positive": 0, "false_positive": 0,
              "false_negative": 0, "true_negative": 0}
    for observation, event in zip(observations, corpus["events"]):
        expected = event.get("grounding_status") in _GROUNDED_EXPECTED
        observed = observation.get("grounding_status") in _GROUNDED_OBSERVED
        if expected and observed:
            counts["true_positive"] += 1
        elif not expected and observed:
            counts["false_positive"] += 1
        elif expected and not observed:
            counts["false_negative"] += 1
        else:
            counts["true_negative"] += 1
    tp, fp, fn = (counts[key] for key in
                  ("true_positive", "false_positive", "false_negative"))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if precision + recall else 0.0)
    return {**counts, "precision": precision, "recall": recall, "f1": f1,
            "denominator": len(corpus["events"])}


def _ci95(successes: int, n: int) -> tuple[float, float, float]:
    mean = successes / n if n else 0.0
    if not n:
        return mean, mean, mean
    margin = 1.96 * (mean * (1.0 - mean) / n) ** 0.5
    return mean, max(0.0, mean - margin), min(1.0, mean + margin)


def _speech_act(event: Mapping[str, Any]) -> str:
    if event["literal_form"] == "interrogative":
        return "question"
    if event["literal_form"] == "social":
        return "greeting"
    if event["literal_form"] in {"imperative", "compound_imperative",
                                  "imperative_with_politeness_marker"}:
        return "instruction"
    return "statement"


def _observed_state(
    attrs: Mapping[str, Any], reply: str,
    goals: Sequence[Mapping[str, Any]] = (),
) -> str:
    # Cognitive state and release state are separate dimensions.  An explicit
    # error surface means production failed closed; it must not erase a
    # graph-resident repair/answer/goal state that was already established.
    if (attrs.get("language_world_support") == "missing"
            or attrs.get("grounding_status") == "authority_missing"
            or (attrs.get("dispatch_path") == "honest_no_world"
                and not attrs.get("anaphor"))):
        return "blocked"
    # Read a disposition that was derived by native communication cognition.
    # This is deliberately ahead of route/reply heuristics: a surface reply
    # cannot overwrite a graph-owned cognitive state.
    native_disposition = attrs.get("cognitive_disposition")
    if native_disposition in {"act", "answer", "defer", "error", "learn",
                              "repair", "blocked"}:
        return str(native_disposition)
    route = str(attrs.get("communication_route") or "")
    if route == "ask_back":
        return "repair"
    if route in {"goal_only", "self_report", "describe_scene",
                 "concern_authored"}:
        if any(str(goal.get("status") or "") == "deferred" for goal in goals):
            return "defer"
        return "act"
    kind = attrs.get("sak_kind") or attrs.get("comp_kind")
    if kind == "instruction":
        # Action faculty either produces an action/repair reply.  The graph
        # interpretation remains the authoritative observation; an explicit
        # error is handled above.
        return "act"
    if kind == "question":
        if attrs.get("grounding_status") in {
                "unresolved", "unresolved_reference", "unknown",
        }:
            return "repair"
        return "answer" if reply.strip() or attrs.get("grounding_status") else "repair"
    if attrs.get("grounding_status") in {"unresolved", "unresolved_reference", "unknown"}:
        return "repair"
    if reply.strip().lower().rstrip(".!?") in ERROR_SURFACES:
        return "error"
    return "defer"


def _state_evidence_metadata(
    attrs: Mapping[str, Any],
    goals: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Describe where the runtime-state observation came from.

    This does not promote a route or reply into cognition.  A graph goal with
    an explicit lifecycle status is the strongest available state evidence;
    interpretation fields are graph-resident but do not constitute a native
    disposition authority.  The final fallback is deliberately labeled as an
    adapter heuristic.
    """
    if attrs.get("cognitive_disposition") not in (None, ""):
        return {
            "source": "native_graph_cognitive_disposition",
            "authority": "native_graph_readback",
            "available": True,
        }
    if any(goal.get("status") not in (None, "") for goal in goals):
        return {
            "source": "graph_resident_goal_lifecycle",
            "authority": "graph_readback",
            "available": True,
        }
    if any(key in attrs for key in (
            "communication_route", "dispatch_path", "grounding_status",
            "language_world_support", "comp_kind", "sak_kind")):
        return {
            "source": "graph_resident_communication_interpretation",
            "authority": "interpretation_readback_not_disposition",
            "available": True,
        }
    return {
        "source": "phase8_adapter_heuristic",
        "authority": "adapter_only",
        "available": False,
    }


def _measurement(
    dimension: str,
    successes: int,
    n: int,
    refs: tuple[str, ...],
    raw_metric: str,
    notes: str = "",
) -> DimensionMeasurement:
    mean, low, high = _ci95(successes, n)
    return DimensionMeasurement(
        dimension=dimension,
        mean=mean,
        n=n,
        ci95_low=low,
        ci95_high=high,
        evidence_refs=refs,
        raw_metric=raw_metric,
        notes=notes,
    )


def _deliberation_readback(trace: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize only serialized native deliberation readback.

    This evaluator never infers a candidate from a reply or from a goal.  The
    summary is deliberately source/status oriented so a corpus run can
    distinguish a native ``no_candidate`` result from absent trace data.
    """
    raw = trace.get("deliberations")
    if not isinstance(raw, list):
        return {
            "trace_status": "unavailable",
            "deliberation_count": 0,
            "statuses": [],
            "candidate_sources": [],
            "candidate_count": 0,
            "selection_count": 0,
            "settlement_count": 0,
        }
    rows = [item for item in raw if isinstance(item, Mapping)]
    return {
        "trace_status": "measured",
        "deliberation_count": len(rows),
        "statuses": sorted({str(item.get("status")) for item in rows
                             if item.get("status") is not None}),
        "candidate_sources": sorted({str(item.get("candidate_source"))
                                      for item in rows
                                      if item.get("candidate_source") is not None}),
        "candidate_count": sum(len(item.get("candidates") or []) for item in rows),
        "selection_count": sum(len(item.get("selections") or []) for item in rows),
        "settlement_count": sum(len(item.get("settlements") or []) for item in rows),
    }


def _unavailable(dimension: str, reason: str) -> DimensionMeasurement:
    return DimensionMeasurement(
        dimension=dimension,
        mean=0.0,
        n=0,
        ci95_low=0.0,
        ci95_high=0.0,
        evidence_refs=(f"phase0://corpus/{dimension}/not-measured",),
        raw_metric="",
        notes=reason,
        status="unavailable",
    )


def _run_eliza_floor_reference(corpus: Mapping[str, Any]) -> tuple[Scorecard, dict[str, Any]]:
    """Run the existing deterministic floor and retain its raw evidence.

    The adapter owns its scoring contract: it measures provenance only and
    leaves every capability dimension unavailable.  This runner merely
    converts its scorecard back to the native comparison type and carries the
    raw, case-bound adapter observations into the report for auditability.
    """
    from evaluation.reference_adapters.eliza_floor import run_eliza_floor

    adapter_report = run_eliza_floor(corpus)
    card = scorecard_from_dict(adapter_report["scorecard"])
    observations = list(adapter_report.get("observations") or [])
    raw_provenance = {
        "schema": adapter_report.get("schema"),
        "report_schema": adapter_report.get("report_schema"),
        "protocol_id": adapter_report.get("protocol_id"),
        "corpus_protocol_id": adapter_report.get("corpus_protocol_id"),
        "adapter": dict(adapter_report.get("adapter") or {}),
        "adapter_entrypoint": card.adapter_entrypoint,
        "deterministic": bool((adapter_report.get("adapter") or {}).get("deterministic")),
        "observation_count": len(observations),
        "complete_observation_count": sum(
            bool(item.get("raw_trace_complete")) for item in observations
        ),
        "failure_count": sum(bool(item.get("failure")) for item in observations),
        "observations": observations,
    }
    return card, raw_provenance


def run_system_under_test(corpus: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Run the booted system once per fixed corpus event and score observations."""
    if corpus is None:
        corpus = load_corpus()
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from evaluation.phase4_partial_evidence_audit import audit_live_event

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    observations: list[dict[str, Any]] = []
    started = time.perf_counter()
    for event in corpus["events"]:
        case_started = time.perf_counter()
        try:
            setup = event.get("setup") or {}
            for held in setup.get("held_answers") or []:
                agent._persist_held_answer(
                    str(held["topic"]), str(held["answer"]))
            reply = agent.converse(
                event["signal"],
                speech_act=_speech_act(event),
                context={
                    "interaction_mode": event["event_mode"],
                    "interaction_relation": event.get("interaction_relation"),
                    "literal_form": event.get("literal_form"),
                    "evidence": list(event.get("evidence") or []),
                },
            ) or ""
            inbound = agent._last_turn_inbound
            attrs = dict(agent.s.node(inbound)["attrs"])
            interpretation_id = attrs.get("communication_interpretation_id")
            if interpretation_id is not None and agent.s.has_node(interpretation_id):
                # CommunicationInterpretation is the authoritative event
                # record; the inbound Message carries transport facts and a
                # link to it, not the complete cognitive interpretation.
                interpretation = dict(agent.s.node(interpretation_id)["attrs"])
                attrs = {**attrs, **interpretation}
            runtime_trace = agent.reply_turn_trace(agent.last_turn_inbound_id()) or {}
            discourse_event_id = attrs.get("discourse_event_id")
            phase4_partial_evidence = (
                audit_live_event(agent, discourse_event_id)
                if discourse_event_id is not None
                else {
                    "schema": "phase4_partial_evidence_audit.v1",
                    "required_dimensions": [], "source_count": 0,
                    "complete_tuple_count": 0,
                    "promotion_eligible_count": 0, "promotion_count": 0,
                    "records": [], "replay_deterministic": True,
                }
            )
            production_evidence = agent.production_turn_evidence(inbound)
            observed = _observed_state(
                attrs, str(reply), runtime_trace.get("goals") or ())
            state_evidence = _state_evidence_metadata(
                attrs, runtime_trace.get("goals") or ())
            error = None
        except Exception as exc:  # record a failed case; do not hide it
            reply, attrs, runtime_trace = "", {}, {}
            production_evidence, observed = {}, "error"
            phase4_partial_evidence = {
                "schema": "phase4_partial_evidence_audit.v1",
                "required_dimensions": [], "source_count": 0,
                "complete_tuple_count": 0,
                "promotion_eligible_count": 0, "promotion_count": 0,
                "records": [], "replay_deterministic": True,
            }
            state_evidence = {
                "source": "phase8_adapter_exception",
                "authority": "adapter_only",
                "available": False,
            }
            error = f"{type(exc).__name__}: {exc}"
        release_status = (
            "error" if str(reply).strip().lower().rstrip(".!?")
            in ERROR_SURFACES else "released" if str(reply).strip() else "unavailable"
        )
        trace_coverage = {
            "interpretation": bool(attrs.get("communication_interpretation_id")),
            "grounding": "grounding_status" in attrs,
            "goal_lifecycle": isinstance(runtime_trace.get("goals"), list),
            "mention_referent": isinstance(runtime_trace.get("mentions"), list),
            "self_concern": isinstance(runtime_trace.get("concerns"), list),
            "parse_evidence": bool(runtime_trace.get("parse") or attrs.get("evidence_schema")),
            "reply_provenance": bool(attrs.get("evidence_provider") and runtime_trace.get("reply_from")),
            "selected_candidate": bool(
                attrs.get("selected_candidate_id")
                or runtime_trace.get("selected_candidate_id")
                or runtime_trace.get("candidate_id")
                or any(
                    item.get("selections")
                    for item in (runtime_trace.get("deliberations") or [])
                    if isinstance(item, Mapping)
                )
            ),
        }
        observation = {
            "id": event["id"],
            "expected_state": event["expected_state"],
            "observed_state": observed,
            "state_match": observed == event["expected_state"],
            "expected_force": event["communicative_force"],
            "canonical_expected_force": FORCE_ALIASES.get(
                event["communicative_force"], event["communicative_force"]),
            "observed_force": attrs.get("communicative_force"),
            "grounding_status": attrs.get("grounding_status"),
            "release_status": release_status,
            "cognitive_state": observed,
            "cognitive_state_evidence_source": state_evidence["source"],
            "cognitive_state_authority": state_evidence["authority"],
            "cognitive_state_evidence_available": state_evidence["available"],
            "release_state": release_status,
            # This is read from the graph-resident CommunicationInterpretation
            # above.  It is deliberately kept separate from reply text and
            # from trace_coverage: Phase 2 may count grounding only when the
            # cognition layer exposes an actual evidence path.
            "grounding_evidence_path": str(
                attrs.get("grounding_evidence_path") or ""),
            "expected_grounding_status": event["grounding_status"],
            "provenance_complete": all(
                attrs.get(key) is not None
                for key in ("communication_interpretation_id", "evidence_schema", "evidence_provider")
            ),
            "reply_present": bool(str(reply).strip()),
            "reply": str(reply),
            "elapsed_ms": (time.perf_counter() - case_started) * 1000.0,
            "error": error,
            "trace_coverage": trace_coverage,
            "deliberation_readback": _deliberation_readback(runtime_trace),
            "phase4_partial_evidence": phase4_partial_evidence,
        }
        # These are serialized graph objects, not assertions about coverage.
        # Keep an empty receipt list explicit for diagnostics, but omit a null
        # cognitive trace so extraction cannot mistake its presence for proof.
        if isinstance(production_evidence, Mapping):
            observation["production_gate_receipts"] = list(
                production_evidence.get("production_gate_receipts") or [])
            if production_evidence.get("cognitive_trace") is not None:
                observation["cognitive_trace"] = production_evidence[
                    "cognitive_trace"]
        observations.append(observation)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    n = len(observations)
    state_matches = sum(item["state_match"] for item in observations)
    interpretation_matches = sum(
        item["observed_force"] == item["canonical_expected_force"] for item in observations
    )
    grounded_expected = [
        item for item, event in zip(observations, corpus["events"])
        if event["grounding_status"] in {"grounded", "partially_grounded"}
    ]
    grounding_matches = sum(
        item["grounding_status"] in {"candidate_grounded", "grounded", "partially_grounded"}
        for item in grounded_expected
    )
    action_cases = [item for item in observations if item["expected_state"] == "act"]
    repair_cases = [item for item in observations if item["expected_state"] == "repair"]
    calibration_cases = [
        item for item in observations
        if item["expected_state"] in {"repair", "defer", "blocked", "error"}
    ]
    provenance_matches = sum(item["provenance_complete"] for item in observations)
    phase4_audits = [item["phase4_partial_evidence"] for item in observations]
    phase4_evidence_summary = {
        "event_count": len(phase4_audits),
        "events_with_sources": sum(bool(item["source_count"]) for item in phase4_audits),
        "source_record_count": sum(item["source_count"] for item in phase4_audits),
        "complete_tuple_count": sum(item["complete_tuple_count"] for item in phase4_audits),
        "promotion_eligible_count": sum(item["promotion_eligible_count"] for item in phase4_audits),
        "actual_promotion_count": sum(item["promotion_count"] for item in phase4_audits),
        "replay_deterministic": all(item["replay_deterministic"] for item in phase4_audits),
    }
    grounding_metrics = grounding_precision_recall(observations, corpus)
    refs = ("corpus://tests/fixtures/conversational_manifold/phase0_events.json",)
    measurements = [
        _measurement("interpretation", interpretation_matches, n, refs, "force_exact_match"),
        _measurement("grounding", grounding_matches, len(grounded_expected), refs, "grounding_status_support_match",
                     "Only grounded and partially_grounded cases are in denominator."),
        _measurement("action", sum(item["observed_state"] == "act" for item in action_cases), len(action_cases), refs, "expected_act_route_match"),
        _measurement("repair", sum(item["observed_state"] == "repair" for item in repair_cases), len(repair_cases), refs, "expected_repair_route_match"),
        _measurement("calibration", sum(item["state_match"] for item in calibration_cases), len(calibration_cases), refs, "abstention_or_error_state_match"),
        _measurement("provenance", provenance_matches, n, refs, "interpretation_provenance_fields_present"),
        _unavailable("memory", "The fixed corpus has no repeated-memory probe."),
        _unavailable("learning", "The fixed corpus has no teacher-learning or post-learning probe."),
        _unavailable("cost", "No preregistered normalized cost-effectiveness denominator was run."),
    ]
    card = Scorecard(TARGET, PROTOCOL_ID, tuple(measurements))
    eliza_card, eliza_raw_provenance = _run_eliza_floor_reference(corpus)
    baseline_cards = {
        baseline: unrun_scorecard(baseline) for baseline in BASELINES
    }
    baseline_cards[eliza_card.system] = eliza_card
    cards = [card, *baseline_cards.values()]
    comparison = comparison_summary(cards)
    # Keep the generic comparative summary as the authority for availability
    # and interval comparisons, then attach the adapter-owned scorecard and
    # raw case provenance to the one measured reference.  No raw trace is
    # converted into a capability label here.
    comparison["baselines"][eliza_card.system].update({
        "scorecard": scorecard_to_dict(eliza_card),
        "raw_provenance": eliza_raw_provenance,
    })
    return {
        "schema": REPORT_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "corpus": {"path": str(FIXTURE), "event_count": n},
        "system_under_test": {"system": "conversational_manifold", "elapsed_ms": elapsed_ms},
        "observations": observations,
        "scorecard": scorecard_to_dict(card),
        "grounding_evaluation": grounding_metrics,
        "phase4_partial_evidence_summary": phase4_evidence_summary,
        "baseline_scorecards": {
            baseline: scorecard_to_dict(baseline_card)
            for baseline, baseline_card in baseline_cards.items()
        },
        "release_gate": evaluate_release_gate(cards),
        "comparison_summary": comparison,
    }


def scorecard_to_dict(card: Scorecard) -> dict[str, Any]:
    return {
        "system": card.system,
        "protocol_id": card.protocol_id,
        "reference_class": card.reference_class,
        "collection_status": card.collection_status,
        "adapter_entrypoint": card.adapter_entrypoint,
        "run_id": card.run_id,
        "annotation_protocol": card.annotation_protocol,
        "measurements": [
            {"dimension": m.dimension, "mean": m.mean, "n": m.n,
             "ci95_low": m.ci95_low, "ci95_high": m.ci95_high,
             "evidence_refs": list(m.evidence_refs), "raw_metric": m.raw_metric,
             "notes": m.notes, "status": m.status}
            for m in card.measurements
        ],
    }


def unrun_scorecard(system: str) -> Scorecard:
    return Scorecard(
        system=system,
        protocol_id=PROTOCOL_ID,
        reference_class=system if system in BASELINES else "",
        collection_status="unavailable",
        adapter_entrypoint=(f"evaluation.reference_adapters.{system}" if system in BASELINES else ""),
        annotation_protocol="phase8-reference-protocol-v1" if system in BASELINES else "",
        measurements=tuple(_unavailable(dimension, "Baseline was not run in this increment; no score inferred.")
                           for dimension in DIMENSIONS),
    )


def build_report_scaffold(corpus: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Create a report envelope before any live system or baseline is run."""
    if corpus is None:
        corpus = load_corpus()
    target = unrun_scorecard(TARGET)
    baselines = [unrun_scorecard(baseline) for baseline in BASELINES]
    return {
        "schema": REPORT_SCHEMA,
        "protocol_id": PROTOCOL_ID,
        "corpus": {"path": str(FIXTURE), "event_count": len(corpus["events"])},
        "system_under_test": {
            "system": TARGET,
            "status": "not_run",
            "notes": "Live run is not included in this scaffold.",
        },
        "scorecard": scorecard_to_dict(target),
        "baseline_scorecards": {
            card.system: scorecard_to_dict(card) for card in baselines
        },
        "release_gate": evaluate_release_gate([target] + baselines),
        "comparison_summary": comparison_summary([target] + baselines),
    }


def write_report(path: Path, corpus: Mapping[str, Any] | None = None) -> dict[str, Any]:
    report = run_system_under_test(corpus)
    raw = FIXTURE.read_bytes()
    report["corpus"]["sha256"] = hashlib.sha256(raw).hexdigest()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scaffold", action="store_true")
    args = parser.parse_args()
    if args.scaffold:
        result = build_report_scaffold()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        result = write_report(args.output)
    print(json.dumps({"output": str(args.output), "status": result["release_gate"]["status"],
                      "events": result["corpus"]["event_count"]}))
