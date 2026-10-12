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
from evaluation.conversational_manifold_phase0 import (
    FIXTURE, load_corpus, validate_corpus,
)


REPORT_SCHEMA = "phase8_sut_corpus_report.v2"
PROTOCOL_ID = "phase8a-fixed-phase0-corpus-v4"
CONTEXT_AWARE_PROTOCOL_ID = "phase8a-fixed-phase0-corpus-v5-event-context-history8"
SUPPORTED_PROTOCOL_IDS = (PROTOCOL_ID, CONTEXT_AWARE_PROTOCOL_ID)
SUPPORTED_RUNTIME_SEED_PROFILES = (
    "full", "conversation_corpus_prepass", "conversation_incremental",
    "conversation_hybrid_prepass",
)
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
    """Use the production I/O classifier, never the corpus parse label.

    ``literal_form`` is an independent reference annotation.  Feeding it into
    ``WorldAdapter.converse`` would let the target provide its own parse cue.
    """
    from substrate.world_adapter import WorldAdapter

    return WorldAdapter.classify_speech_act(str(event.get("signal") or ""))


def _runtime_context(event: Mapping[str, Any]) -> dict[str, Any]:
    """Transport interaction metadata, never corpus evidence annotations."""
    return {
        # Synthetic/held-out profiles may provide only a signal. Preserve the
        # ordinary conversational boundary as the transport default without
        # inferring any reference labels from the corpus.
        "interaction_mode": event.get("event_mode", "turn_compatible"),
        "interaction_relation": event.get("interaction_relation"),
    }


def _observed_state(
    attrs: Mapping[str, Any], reply: str,
    goals: Sequence[Mapping[str, Any]] = (),
) -> str:
    # Cognitive state and release state are separate dimensions.  An explicit
    # error surface means production failed closed; it must not erase a
    # graph-resident repair/answer/goal state that was already established.
    # Read a disposition that was derived by native communication cognition.
    # This is deliberately ahead of every adapter/route heuristic: a surface
    # reply or missing-world hint cannot overwrite a graph-owned decision.
    native_disposition = attrs.get("cognitive_disposition")
    if native_disposition in {"act", "answer", "defer", "error", "learn",
                              "repair", "blocked"}:
        return str(native_disposition)
    if (attrs.get("language_world_support") == "missing"
            or attrs.get("grounding_status") == "authority_missing"
            or (attrs.get("dispatch_path") == "honest_no_world"
                and not attrs.get("anaphor"))):
        return "blocked"
    route = str(attrs.get("communication_route") or "")
    if route == "ask_back":
        return "repair"
    if route in {"goal_only", "self_report", "describe_scene",
                 "concern_authored"}:
        if any(str(goal.get("status") or "") == "deferred" for goal in goals):
            return "defer"
        return "act"
    kind = attrs.get("sak_kind") or attrs.get("comp_kind")
    if (kind == "question" and attrs.get("grounding_status") in {
            "unresolved", "unresolved_reference", "unknown"}):
        return "repair"
    # Preserve higher-priority graph interpretations above, but do not infer a
    # successful answer/action from a production diagnostic surface.
    if reply.strip().lower().rstrip(".!?") in ERROR_SURFACES:
        return "error"
    if kind == "instruction":
        # Action faculty either produces an action/repair reply.  The graph
        # interpretation remains the authoritative observation; an explicit
        # error is handled above.
        return "act"
    if kind == "question":
        return "answer" if reply.strip() or attrs.get("grounding_status") else "repair"
    if attrs.get("grounding_status") in {"unresolved", "unresolved_reference", "unknown"}:
        return "repair"
    return "defer"


def _state_evidence_metadata(
    attrs: Mapping[str, Any],
    goals: Sequence[Mapping[str, Any]],
    reply_commitment: Mapping[str, Any] | None = None,
    answer_commitment: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe where the runtime-state observation came from.

    This does not promote a route or reply into cognition.  A graph goal with
    an explicit lifecycle status is the strongest available state evidence;
    interpretation fields are graph-resident but do not constitute a native
    disposition authority.  An unrelated active Goal is not evidence for the
    event's state; lifecycle authority is credited only when the selected goal
    route reads an explicit deferred status.  The final fallback is
    deliberately labeled as an adapter heuristic.
    """
    if attrs.get("cognitive_disposition") not in (None, ""):
        return {
            "source": "native_graph_cognitive_disposition",
            "authority": "native_graph_readback",
            "available": True,
        }
    route = str(attrs.get("communication_route") or "")
    goal_routes = {"goal_only", "self_report", "describe_scene",
                   "concern_authored"}
    if (route in goal_routes
            and any(str(goal.get("status") or "") == "deferred"
                    for goal in goals)):
        return {
            "source": "graph_resident_goal_lifecycle",
            "authority": "graph_readback",
            "available": True,
        }
    action_goal_kinds = {
        "instruction", "report_self", "describe_scene", "concern_authored",
    }
    if any(goal.get("event_bound") is True
           and str(goal.get("kind") or "") in action_goal_kinds
           for goal in goals):
        return {
            "source": "graph_resident_event_bound_action_goal",
            "authority": "graph_readback",
            "available": True,
        }
    if (isinstance(reply_commitment, Mapping)
            and reply_commitment.get("graph_linked_to_turn") is True
            and reply_commitment.get("expects_response") is True
            and "clarification" in (reply_commitment.get("speech_acts") or [])):
        return {
            "source": "graph_resident_clarification_pair",
            "authority": "graph_readback",
            "available": True,
        }
    if (isinstance(answer_commitment, Mapping)
            and answer_commitment.get("graph_linked_to_turn") is True
            and answer_commitment.get("kind") in {
                "supported_event_bound_topic_answer",
            }
            or isinstance(answer_commitment, Mapping)
            and answer_commitment.get("graph_linked_to_turn") is True
            and answer_commitment.get("kind") == "linked_graph_answer_message"
            and answer_commitment.get("surface_bound") is True):
        return {
            "source": "graph_resident_answer_commitment",
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
    if n == 0:
        return DimensionMeasurement(
            dimension=dimension, mean=0.0, n=0, ci95_low=0.0, ci95_high=0.0,
            evidence_refs=refs, raw_metric=raw_metric,
            notes=(notes + " " if notes else "")
            + "Unavailable: no observations with disposition-grade authority.",
            status="unavailable",
        )
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


def _authoritative_state_match(observed: str, expected: str, authority: str) -> bool:
    """Only graph/native disposition readback validates outcome labels."""
    return observed == expected and authority in {
        "graph_readback", "native_graph_readback"}


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
    def graph_or_flat(item: Mapping[str, Any], key: str) -> Any:
        if item.get(key) is not None:
            return item.get(key)
        attrs = item.get("attrs")
        return attrs.get(key) if isinstance(attrs, Mapping) else None

    return {
        "trace_status": "measured",
        "deliberation_count": len(rows),
        "statuses": sorted({str(graph_or_flat(item, "status")) for item in rows
                             if graph_or_flat(item, "status") is not None}),
        "candidate_sources": sorted({str(graph_or_flat(item, "candidate_source"))
                                      for item in rows
                                      if graph_or_flat(item, "candidate_source") is not None}),
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


def _run_eliza_floor_reference(corpus: Mapping[str, Any], *,
                               protocol_id: str) -> tuple[Scorecard, dict[str, Any]]:
    """Run the existing deterministic floor and retain its raw evidence.

    The adapter owns its scoring contract: it measures provenance only and
    leaves every capability dimension unavailable.  This runner merely
    converts its scorecard back to the native comparison type and carries the
    raw, case-bound adapter observations into the report for auditability.
    """
    from evaluation.reference_adapters.eliza_floor import run_eliza_floor

    adapter_report = run_eliza_floor(corpus, protocol_id=protocol_id)
    card = scorecard_from_dict(adapter_report["scorecard"])
    observations = list(adapter_report.get("observations") or [])
    raw_provenance = {
        "schema": adapter_report.get("schema"),
        "report_schema": adapter_report.get("report_schema"),
        "protocol_id": adapter_report.get("protocol_id"),
        "corpus_protocol_id": adapter_report.get("corpus_protocol_id"),
        "input_profile": adapter_report.get("input_profile"),
        "session_history_limit": adapter_report.get("session_history_limit"),
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


def _information_learning_request_summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize serialized learning intent without treating it as execution."""
    requests = [request for item in observations
                for request in item.get("information_learning_requests", [])]
    status_counts: dict[str, int] = {}
    for request in requests:
        attrs = request.get("attrs") or {}
        status = str(attrs.get("status") or "unspecified")
        status_counts[status] = status_counts.get(status, 0) + 1
    return {
        "request_count": len(requests),
        "event_bound_count": sum(bool(request.get("event_bound")) for request in requests),
        "status_counts": dict(sorted(status_counts.items())),
        "requests_with_answer_authority": sum(
            str(request.get("answer_authority",
                            (request.get("attrs") or {}).get("answer_authority"))
                or "").strip().lower() not in {"", "none", "null"}
            for request in requests),
        "execution_performed": False,
        "notes": "Typed requests are intent only; this report does not establish retrieval or answer authority.",
    }


def production_release_summary(
    observations: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Audit whether each substantive surface has an exact release receipt.

    This reports production authority coverage only. Explicit error surfaces
    and deliberate silence are separate terminal outcomes, not substantive
    releases; no reply text is used to infer cognition or capability scores.
    """
    status_counts: dict[str, int] = {}
    no_reply_reason_counts: dict[str, int] = {}
    substantive = released_substantive = errors = silence = 0
    authorized_no_reply = unclassified_silence = 0
    withheld_errors = 0
    unreleased_ids = []
    for observation in observations:
        reply = str(observation.get("reply") or "").strip()
        is_error = reply.lower().rstrip(".!?") in ERROR_SURFACES
        if not reply:
            silence += 1
            reason = _explicit_no_reply_reason(observation)
            if reason is None:
                unclassified_silence += 1
            else:
                authorized_no_reply += 1
                no_reply_reason_counts[reason] = (
                    no_reply_reason_counts.get(reason, 0) + 1)
        elif is_error:
            errors += 1
        else:
            substantive += 1

        receipts = observation.get("production_gate_receipts") or []
        for receipt in receipts:
            attrs = receipt.get("attrs") if isinstance(receipt, Mapping) else {}
            attrs = attrs if isinstance(attrs, Mapping) else {}
            status = str(attrs.get("status") or "unspecified")
            status_counts[status] = status_counts.get(status, 0) + 1
            if is_error and status == "withheld":
                withheld_errors += 1
        exact_release = any(
            isinstance(receipt, Mapping)
            and isinstance(receipt.get("attrs"), Mapping)
            and receipt["attrs"].get("status") == "released"
            and str(receipt["attrs"].get("surface") or "").strip() == reply
            for receipt in receipts
        )
        if reply and not is_error:
            if exact_release:
                released_substantive += 1
            else:
                unreleased_ids.append(str(observation.get("id") or ""))
    return {
        "schema": "phase8_production_release_summary.v2",
        "observation_count": len(observations),
        "substantive_reply_count": substantive,
        "released_substantive_reply_count": released_substantive,
        "unreleased_substantive_reply_count": len(unreleased_ids),
        "unreleased_substantive_event_ids": unreleased_ids,
        "explicit_error_reply_count": errors,
        "withheld_error_receipt_count": withheld_errors,
        "silent_event_count": silence,
        "silent_authorized_no_reply_count": authorized_no_reply,
        "silent_unclassified_count": unclassified_silence,
        "silent_no_reply_reason_counts": dict(sorted(
            no_reply_reason_counts.items())),
        "receipt_status_counts": dict(sorted(status_counts.items())),
        "substantive_release_coverage_complete": not unreleased_ids,
    }


def compound_communication_act_summary(
    observations: list[Mapping[str, Any]],
    corpus: Mapping[str, Any],
) -> dict[str, Any]:
    """Measure annotated co-acts and their separately released responses.

    This is an additive multi-label audit. It does not feed annotations into
    runtime; the standard corpus projection and scalar scorecard are unchanged.
    """
    records = []
    for event, observation in zip(corpus["events"], observations):
        expected_acts = event.get("communicative_acts")
        if not isinstance(expected_acts, list):
            continue
        trace = observation.get("cognitive_trace")
        trace = trace if isinstance(trace, Mapping) else {}
        raw_evidence = trace.get("communication_act_evidence") or []
        observed_acts = []
        for item in raw_evidence:
            if not isinstance(item, Mapping):
                continue
            attrs = item.get("attrs")
            if not isinstance(attrs, Mapping):
                continue
            observed_acts.append({
                "act_type": attrs.get("act_type"),
                "force": attrs.get("communicative_force"),
            })
        expected_pairs = [(item.get("act_type"), item.get("force"))
                          for item in expected_acts]
        observed_pairs = [(item.get("act_type"), item.get("force"))
                          for item in observed_acts]
        expected_releases = list(
            event.get("expected_released_semantic_events") or [])
        released = {
            str(receipt.get("attrs", {}).get("semantic_event"))
            for receipt in (observation.get("production_gate_receipts") or [])
            if isinstance(receipt, Mapping)
            and isinstance(receipt.get("attrs"), Mapping)
            and receipt["attrs"].get("status") == "released"
        }
        released_components = [name for name in expected_releases
                               if name in released]
        records.append({
            "event_id": str(event.get("id") or ""),
            "expected_communicative_acts": [dict(item)
                                             for item in expected_acts],
            "observed_communicative_acts": observed_acts,
            "act_evidence_exact_match": observed_pairs == expected_pairs,
            "expected_released_semantic_events": expected_releases,
            "released_semantic_events": released_components,
            "response_components_complete": (
                set(expected_releases).issubset(released)),
        })
    exact = sum(item["act_evidence_exact_match"] for item in records)
    complete = sum(item["response_components_complete"] for item in records)
    return {
        "schema": "phase8_compound_communication_act_audit.v1",
        "annotated_event_count": len(records),
        "act_evidence_exact_match_count": exact,
        "response_component_complete_count": complete,
        "complete": exact == len(records) and complete == len(records),
        "records": records,
    }


def _communication_act_pairs(observation: Mapping[str, Any]) -> list[tuple[Any, Any]]:
    trace = observation.get("cognitive_trace")
    trace = trace if isinstance(trace, Mapping) else {}
    pairs = []
    for item in trace.get("communication_act_evidence") or []:
        if not isinstance(item, Mapping):
            continue
        attrs = item.get("attrs")
        if isinstance(attrs, Mapping):
            pairs.append((attrs.get("act_type"),
                          attrs.get("communicative_force")))
    return pairs


def _interpretation_matches(observation: Mapping[str, Any],
                            event: Mapping[str, Any]) -> bool:
    """Score every annotated act when the reference is explicitly multi-label.

    The event-level force remains the legacy scalar projection. For an event
    with ``communicative_acts``, graph-resident native evidence must contain
    the full ordered set of act/force pairs; neither component can stand in
    for the other. Unannotated events retain the established scalar check.
    """
    expected_acts = event.get("communicative_acts")
    if isinstance(expected_acts, list):
        expected_pairs = [(item.get("act_type"), item.get("force"))
                          for item in expected_acts]
        return _communication_act_pairs(observation) == expected_pairs
    expected_force = FORCE_ALIASES.get(
        event.get("communicative_force"), event.get("communicative_force"))
    return observation.get("observed_force") == expected_force


def _explicit_no_reply_reason(observation: Mapping[str, Any]) -> str | None:
    """Classify silence only when native state explicitly closes the reply slot."""
    if (
        observation.get("disposition_authoritative") is True
        and observation.get("interaction_mode") == "turn_compatible"
        and observation.get("observed_force") == "refusal"
        and observation.get("observed_state") == "defer"
        and observation.get("reply_expectation") == "not_expected"
    ):
        return "native_typed_refusal_defer"
    if (observation.get("disposition_authoritative") is True
            and observation.get("observed_state") == "repair"
            and observation.get("cognitive_arbitration_basis")
            == "nonturn_knowledge_deficit_repair"
            and observation.get("interaction_mode") == "non_turn"
            and observation.get("interaction_relation") == "continuation"
            and observation.get("reply_expectation") == "not_expected"):
        return "native_nonturn_knowledge_deficit_repair"
    if (observation.get("disposition_authoritative") is True
            and observation.get("interaction_mode") == "turn_compatible"
            and observation.get("observed_state") == "defer"):
        if (observation.get("interaction_relation") == "overlap"
                and observation.get("literal_form") == "fragment"):
            return "native_overlap_fragment_defer"
        if observation.get("interaction_relation") == "continuation":
            return "native_continuation_defer"
    if (observation.get("disposition_authoritative") is not True
            or observation.get("interaction_mode") != "non_turn"):
        return None
    disposition = observation.get("observed_state")
    if disposition == "blocked":
        return "native_blocked_non_turn"
    if disposition == "defer":
        if observation.get("interaction_relation") == "continuation":
            return "native_nonturn_continuation_defer"
        if observation.get("literal_form") == "fragment":
            return "native_fragment_defer_non_turn"
        if observation.get("evidence_communicative_act") == \
                "ability_action_offer":
            return "native_incomplete_offer_defer_non_turn"
    return None


def run_system_under_test(
    corpus: Mapping[str, Any] | None = None, *, protocol_id: str = PROTOCOL_ID,
    runtime_seed_profile: str = "conversation_incremental",
) -> dict[str, Any]:
    """Run the booted system once per fixed corpus event and score observations.

    runtime_seed_profile="conversation_corpus_prepass" is an explicit
    offline fixed-corpus profile: it computes only lexical candidates from
    signal text, selects their connected seed/dependency closure before the
    first turn, then seals incremental loading. It never consumes reference
    parse, force, evidence, or expected-outcome annotations. The service-aligned
    conversation_incremental profile is the default; it boots conversation
    anchors and exercises the live per-turn content pre-pass.
    conversation_hybrid_prepass uses the same annotation-free lexical closure
    before turn one but keeps the live connected fallback enabled. It is an
    offline fixed-workload test of the hybrid service contract, not a claim
    that future online content is known at boot. Full boot remains available
    as a broad-boot control.
    """
    if protocol_id not in SUPPORTED_PROTOCOL_IDS:
        raise ValueError(f"unsupported Phase 8 input protocol: {protocol_id}")
    if runtime_seed_profile not in SUPPORTED_RUNTIME_SEED_PROFILES:
        raise ValueError(f"unsupported Phase 8 runtime seed profile: {runtime_seed_profile}")
    if corpus is None:
        corpus = load_corpus()
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter
    from evaluation.phase4_partial_evidence_audit import audit_live_event

    agent = WorldAdapter(seeds=())
    seed_profile_summary: dict[str, Any] = {
        "profile": runtime_seed_profile,
    }
    initial_profile_seed_ids: set[str] = set()
    if runtime_seed_profile == "full":
        load_report = load_all_seeds(agent)
        seed_profile_summary.update({
            "prepass_mode": "all_seed_boot",
            "loaded_seed_count": int(load_report.get("loaded", 0)),
            "selection_complete": load_report.get("selection_complete"),
        })
    elif runtime_seed_profile in {
            "conversation_corpus_prepass", "conversation_hybrid_prepass"}:
        from substrate.boot_profiles import load_conversation_seed_profile

        # Match the live message-boundary candidate producer exactly. Whole
        # utterances are not seed keys; reference labels are intentionally not
        # consulted when constructing this sealed fixed-corpus closure.
        lexical_candidates = sorted({
            candidate
            for event in corpus.get("events", ())
            for candidate in agent.lexical_candidates(
                str(event.get("signal") or ""))
        })
        load_report = load_conversation_seed_profile(
            agent,
            content_candidates=lexical_candidates,
            incremental_content_loading=(
                runtime_seed_profile == "conversation_hybrid_prepass"),
        )
        if (not load_report.get("selection_complete")
                or load_report.get("failed")):
            raise RuntimeError(
                "Phase 8 conversation corpus seed prepass was incomplete")
        seed_profile_summary.update({
            "prepass_mode": (
                "sealed_corpus_lexical_candidate_closure"
                if runtime_seed_profile == "conversation_corpus_prepass"
                else "corpus_connected_prepass_with_live_fallback"),
            "lexical_candidate_count": len(lexical_candidates),
            "loaded_seed_count": int(load_report.get("loaded", 0)),
            "selection_complete": True,
            "incremental_content_loading": (
                runtime_seed_profile == "conversation_hybrid_prepass"),
        })
    else:
        from substrate.boot_profiles import load_conversation_seed_profile

        load_report = load_conversation_seed_profile(agent)
        if (not load_report.get("selection_complete")
                or load_report.get("failed")):
            raise RuntimeError(
                "Phase 8 incremental conversation seed profile was incomplete")
        initial_profile_seed_ids = set(
            load_report.get("loaded_seed_ids") or ())
        seed_profile_summary.update({
            "prepass_mode": "per_turn_incremental_lexical_candidates",
            "initial_loaded_seed_count": len(initial_profile_seed_ids),
            "loaded_seed_count": len(initial_profile_seed_ids),
            "selection_complete": True,
            "incremental_content_loading": True,
            "prepass_status_counts": {},
        })
    observations: list[dict[str, Any]] = []
    started = time.perf_counter()
    for event in corpus["events"]:
        case_started = time.perf_counter()
        turn_elapsed_ms = 0.0
        try:
            setup = event.get("setup") or {}
            for held in setup.get("held_answers") or []:
                agent._persist_held_answer(
                    str(held["topic"]), str(held["answer"]))
            turn_started = time.perf_counter()
            try:
                reply = agent.converse(
                    event["signal"],
                    speech_act=_speech_act(event),
                    context=_runtime_context(event),
                ) or ""
                if runtime_seed_profile == "conversation_incremental":
                    prepass = getattr(
                        agent, "_last_conversation_content_prepass", None)
                    if isinstance(prepass, Mapping):
                        status = str(prepass.get("status") or "unreported")
                        counts = seed_profile_summary["prepass_status_counts"]
                        counts[status] = counts.get(status, 0) + 1
            finally:
                # Measure the actual synchronous turn boundary separately
                # from post-turn evidence extraction/Phase 4 auditing below.
                # Both values remain visible: diagnostic serialization must
                # not be mistaken for conversation latency, nor silently
                # disappear from total per-case cost.
                turn_elapsed_ms = (time.perf_counter() - turn_started) * 1000.0
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
                attrs, runtime_trace.get("goals") or (),
                runtime_trace.get("reply_commitment"),
                runtime_trace.get("answer_commitment"))
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
            "interaction_mode": attrs.get("interaction_mode",
                                           event.get("event_mode")),
            "interaction_relation": attrs.get(
                "interaction_relation", event.get("interaction_relation")),
            "literal_form": attrs.get("literal_form"),
            "evidence_communicative_act": attrs.get(
                "evidence_communicative_act"),
            "observed_state": observed,
            "cognitive_arbitration_basis": attrs.get("arbitration_basis"),
            "reply_expectation": agent.graph_turn_reply_expectation(
                inbound).get("status"),
            # Label equality is useful diagnostic data, but only a graph/native
            # disposition readback can validate it as an outcome.
            "observed_state_label_match": observed == event["expected_state"],
            "disposition_authoritative": state_evidence["authority"] in {
                "graph_readback", "native_graph_readback"},
            "state_match": _authoritative_state_match(
                observed, event["expected_state"], state_evidence["authority"]),
            "expected_force": event["communicative_force"],
            "canonical_expected_force": FORCE_ALIASES.get(
                event["communicative_force"], event["communicative_force"]),
            "observed_force": attrs.get("communicative_force"),
            "observed_literal_form": attrs.get("literal_form"),
            "literal_form_source": attrs.get("literal_form_source"),
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
            "reported_content_evidence_path": str(
                attrs.get("reported_content_evidence_path") or ""),
            "expected_grounding_status": event["grounding_status"],
            "provenance_complete": all(
                attrs.get(key) is not None
                for key in ("communication_interpretation_id", "evidence_schema", "evidence_provider")
            ),
            "reply_present": bool(str(reply).strip()),
            "reply": str(reply),
            "turn_elapsed_ms": turn_elapsed_ms,
            "elapsed_ms": (time.perf_counter() - case_started) * 1000.0,
            "error": error,
            "trace_coverage": trace_coverage,
            "deliberation_readback": _deliberation_readback(runtime_trace),
            "phase4_partial_evidence": phase4_partial_evidence,
            "information_learning_requests": [],
        }
        # These are serialized graph objects, not assertions about coverage.
        # Keep an empty receipt list explicit for diagnostics, but omit a null
        # cognitive trace so extraction cannot mistake its presence for proof.
        if isinstance(production_evidence, Mapping):
            observation["production_gate_receipts"] = list(
                production_evidence.get("production_gate_receipts") or [])
            observation["information_learning_requests"] = list(
                production_evidence.get("information_learning_requests") or [])
            if production_evidence.get("cognitive_trace") is not None:
                observation["cognitive_trace"] = production_evidence[
                    "cognitive_trace"]
        observations.append(observation)
    if runtime_seed_profile == "conversation_incremental":
        state = getattr(agent, "_conversation_seed_profile_state", {})
        final_seed_ids = set(state.get("loaded_seed_ids") or ())
        seed_profile_summary["loaded_seed_count"] = len(final_seed_ids)
        seed_profile_summary["incrementally_added_seed_count"] = len(
            final_seed_ids - initial_profile_seed_ids)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    n = len(observations)
    turn_latencies = sorted(float(item["turn_elapsed_ms"])
                            for item in observations)
    p95_index = max(0, min(len(turn_latencies) - 1,
                           int(0.95 * len(turn_latencies) + 0.999999) - 1))
    turn_latency_summary = {
        "scope": "WorldAdapter.converse synchronous call only",
        "event_count": len(turn_latencies),
        "median_ms": turn_latencies[len(turn_latencies) // 2]
        if turn_latencies else 0.0,
        "p95_ms": turn_latencies[p95_index] if turn_latencies else 0.0,
        "max_ms": turn_latencies[-1] if turn_latencies else 0.0,
        "over_150ms_count": sum(value > 150.0 for value in turn_latencies),
        "post_turn_audit_included": False,
    }
    interpretation_matches = sum(
        _interpretation_matches(item, event)
        for item, event in zip(observations, corpus["events"])
    )
    grounded_expected = [
        item for item, event in zip(observations, corpus["events"])
        if event["grounding_status"] in {"grounded", "partially_grounded"}
    ]
    grounding_matches = sum(
        item["grounding_status"] in {"candidate_grounded", "grounded", "partially_grounded"}
        for item in grounded_expected
    )
    action_cases = [item for item in observations
                    if item["expected_state"] == "act" and item["disposition_authoritative"]]
    repair_cases = [item for item in observations
                    if item["expected_state"] == "repair" and item["disposition_authoritative"]]
    calibration_cases = [
        item for item in observations
        if item["expected_state"] in {"repair", "defer", "blocked", "error"}
        and item["disposition_authoritative"]
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
    # Keep the fixed binary Phase 8 metric and the richer Phase 2 four-way
    # referent/source audit separate. This report is derived only from current
    # observations and the fixed corpus annotations; it never feeds labels
    # back into runtime cognition.
    grounding_source_errors = validate_corpus(dict(corpus))
    if grounding_source_errors:
        grounding_source_audit = {
            "schema": "phase2_grounding_precision_recall.v1",
            "status": "unavailable",
            "reason": "grounding source audit requires the validated fixed corpus",
            "validation_errors": grounding_source_errors,
        }
    else:
        from evaluation.phase2_grounding_measurement import measure_grounding
        grounding_source_audit = measure_grounding(corpus, observations)
    refs = ("corpus://tests/fixtures/conversational_manifold/phase0_events.json",)
    measurements = [
        _measurement(
            "interpretation", interpretation_matches, n, refs,
            "annotated_act_or_force_exact_match",
            "Multi-act annotations require exact graph-resident act/force pairs; "
            "other events retain scalar force matching."),
        _measurement("grounding", grounding_matches, len(grounded_expected), refs, "grounding_status_support_match",
                     "Only grounded and partially_grounded cases are in denominator."),
        _measurement("action", sum(item["state_match"] for item in action_cases), len(action_cases), refs, "authoritative_expected_act_route_match",
                     f"Disposition authority coverage: {len(action_cases)}/{sum(item['expected_state'] == 'act' for item in observations)} expected-act cases."),
        _measurement("repair", sum(item["state_match"] for item in repair_cases), len(repair_cases), refs, "authoritative_expected_repair_route_match",
                     f"Disposition authority coverage: {len(repair_cases)}/{sum(item['expected_state'] == 'repair' for item in observations)} expected-repair cases."),
        _measurement("calibration", sum(item["state_match"] for item in calibration_cases), len(calibration_cases), refs, "authoritative_abstention_or_error_state_match",
                     f"Disposition authority coverage: {len(calibration_cases)}/{sum(item['expected_state'] in {'repair', 'defer', 'blocked', 'error'} for item in observations)} calibration cases."),
        _measurement("provenance", provenance_matches, n, refs, "interpretation_provenance_fields_present"),
        _unavailable("memory", "The fixed corpus has no repeated-memory probe."),
        _unavailable("learning", "The fixed corpus has no teacher-learning or post-learning probe."),
        _unavailable("cost", "No preregistered normalized cost-effectiveness denominator was run."),
    ]
    card = Scorecard(TARGET, protocol_id, tuple(measurements))
    baseline_cards = {
        baseline: unrun_scorecard(baseline, protocol_id=protocol_id)
        for baseline in BASELINES
    }
    eliza_card, eliza_raw_provenance = _run_eliza_floor_reference(
        corpus, protocol_id=protocol_id)
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
        "protocol_id": protocol_id,
        "corpus": {"path": str(FIXTURE), "event_count": n},
        "system_under_test": {
            "system": "conversational_manifold",
            "elapsed_ms": elapsed_ms,
            "turn_latency_ms": turn_latency_summary,
            "runtime_seed_profile": runtime_seed_profile,
            "runtime_seed_profile_summary": seed_profile_summary,
            "input_profile": ("event_context_v5_history8"
                              if protocol_id == CONTEXT_AWARE_PROTOCOL_ID
                              else "signal_only_v4"),
            "memory_learning_comparable": protocol_id == PROTOCOL_ID,
        },
        "observations": observations,
        "disposition_authority_coverage": {
            "authoritative_count": sum(item["disposition_authoritative"] for item in observations),
            "observation_count": n,
            "label_matches_without_authority": sum(
                item["observed_state_label_match"] and not item["disposition_authoritative"]
                for item in observations),
        },
        "scorecard": scorecard_to_dict(card),
        "grounding_evaluation": grounding_metrics,
        "grounding_cognitive_source_audit": grounding_source_audit,
        "phase4_partial_evidence_summary": phase4_evidence_summary,
        "compound_communication_act_summary":
            compound_communication_act_summary(observations, corpus),
        "production_release_summary": production_release_summary(observations),
        "information_learning_request_summary":
            _information_learning_request_summary(observations),
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


def unrun_scorecard(system: str, *, protocol_id: str = PROTOCOL_ID) -> Scorecard:
    return Scorecard(
        system=system,
        protocol_id=protocol_id,
        reference_class=system if system in BASELINES else "",
        collection_status="unavailable",
        adapter_entrypoint=(f"evaluation.reference_adapters.{system}" if system in BASELINES else ""),
        annotation_protocol="phase8-reference-protocol-v1" if system in BASELINES else "",
        measurements=tuple(_unavailable(dimension, "Baseline was not run in this increment; no score inferred.")
                           for dimension in DIMENSIONS),
    )


def build_report_scaffold(
    corpus: Mapping[str, Any] | None = None, *, protocol_id: str = PROTOCOL_ID,
) -> dict[str, Any]:
    """Create a report envelope before any live system or baseline is run."""
    if protocol_id not in SUPPORTED_PROTOCOL_IDS:
        raise ValueError(f"unsupported Phase 8 input protocol: {protocol_id}")
    if corpus is None:
        corpus = load_corpus()
    target = unrun_scorecard(TARGET, protocol_id=protocol_id)
    baselines = [unrun_scorecard(baseline, protocol_id=protocol_id)
                 for baseline in BASELINES]
    return {
        "schema": REPORT_SCHEMA,
        "protocol_id": protocol_id,
        "corpus": {"path": str(FIXTURE), "event_count": len(corpus["events"])},
        "system_under_test": {
            "system": TARGET,
            "status": "not_run",
            "notes": "Live run is not included in this scaffold.",
        },
        "scorecard": scorecard_to_dict(target),
        "information_learning_request_summary":
            _information_learning_request_summary([]),
        "baseline_scorecards": {
            card.system: scorecard_to_dict(card) for card in baselines
        },
        "release_gate": evaluate_release_gate([target] + baselines),
        "comparison_summary": comparison_summary([target] + baselines),
    }


def write_report(path: Path, corpus: Mapping[str, Any] | None = None, *,
                 protocol_id: str = PROTOCOL_ID,
                 runtime_seed_profile: str = "conversation_incremental") -> dict[str, Any]:
    report = run_system_under_test(
        corpus, protocol_id=protocol_id,
        runtime_seed_profile=runtime_seed_profile)
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
    parser.add_argument("--protocol-id", choices=SUPPORTED_PROTOCOL_IDS,
                        default=PROTOCOL_ID)
    parser.add_argument("--runtime-seed-profile",
                        choices=SUPPORTED_RUNTIME_SEED_PROFILES,
                        default="conversation_incremental",
                        help=("Runtime seed-loading profile. The sealed "
                              "conversation_corpus_prepass uses only lexical "
                              "candidates from the fixed corpus, selects "
                              "connected dependencies before turn one, and "
                              "disables per-turn content loading."))
    args = parser.parse_args()
    if args.scaffold:
        result = build_report_scaffold(protocol_id=args.protocol_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        result = write_report(
            args.output, protocol_id=args.protocol_id,
            runtime_seed_profile=args.runtime_seed_profile)
    print(json.dumps({"output": str(args.output), "status": result["release_gate"]["status"],
                      "events": result["corpus"]["event_count"]}))
