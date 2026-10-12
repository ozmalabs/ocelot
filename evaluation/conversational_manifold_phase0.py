"""Phase 0 evaluation contract for communication-event traces.

This module owns only evaluation data validation and trace assertions.  It does
not choose a runtime route or alter the cognition layer.  The corpus labels an
event independently from the way a current adapter happens to render it.
"""
from __future__ import annotations

import json
from pathlib import Path


FIXTURE = (Path(__file__).resolve().parents[1] / "tests" / "fixtures" /
           "conversational_manifold" / "phase0_events.json")

EVENT_MODES = {"non_turn", "turn_compatible"}
RELATIONS = {"standalone", "continuation", "overlap", "interruption",
             "response", "turn_compatible"}
FORCES = {"request_information", "request_action", "assertion",
          "correction", "acknowledgement", "offer", "repair", "refusal",
          "social_action"}
GOALS = {"answer", "act", "repair", "defer", "learn", "blocked", "error",
         "update_common_ground", "coordinate_socially"}
GROUNDING = {"grounded", "partially_grounded", "unknown", "contradicted",
             "unavailable_world", "unresolved_reference"}
STATES = {"answer", "act", "repair", "defer", "learn", "blocked", "error"}
EVIDENCE_KINDS = {"graph_path", "lexical_syntactic", "discourse_state",
                  "addressee_model", "explicit_uncertainty",
                  "explicit_failure"}
NEUTRAL_COMMUNICATIVE_ACTS = {
    "greeting", "thanks", "farewell", "polar_question",
    "information_question", "action_request", "assertion",
    "acknowledgement", "refusal", "inability_action",
    "ability_action_offer", "nonunderstanding_report",
}
NEUTRAL_ACT_FORCES = {
    "information_request", "action_request", "assertion_or_correction",
    "repair_or_defer", "social_action", "acknowledgement", "refusal",
}

# Candidate/lifecycle evidence is conditional.  The Phase 0 corpus is a
# communication-event corpus; an event does not acquire a deliberative
# candidate merely because its label says "answer" or "act".  When a runtime
# event actually creates a deliberation, its trace is governed by the native
# Phase 4 manifest below.
PHASE4_TRACE_CONTRACT = "seeds/conversation_deliberation_phase4a.json"
PHASE4_CANDIDATE_SOURCES = {
    "discourse_state", "thought_manifold", "live_thought_manifold",
}
PHASE4_LIFECYCLE_STATES = {
    "proposed", "selected", "executing", "resolved", "blocked",
    "repaired", "abandoned", "no_candidate",
}


def load_corpus(path: Path = FIXTURE) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_corpus(payload: dict) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != "communication_event_corpus.v1":
        errors.append("schema must be communication_event_corpus.v1")
    events = payload.get("events")
    if not isinstance(events, list) or not events:
        return errors + ["events must be a non-empty list"]
    if not 60 <= len(events) <= 100:
        errors.append("events must contain the planned 60-100 event corpus")
    coverage = payload.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("coverage must be an object")
    else:
        if coverage.get("target_event_count", 0) < 60:
            errors.append("coverage.target_event_count must be at least 60")
        required_dimensions = {
            "interpretation", "intent", "goal_lifecycle", "mention_referent",
            "topic", "self_concern", "parse_evidence", "reply_provenance",
        }
        if not required_dimensions.issubset(set(coverage.get("trace_dimensions", []))):
            errors.append("coverage.trace_dimensions is missing a Phase 0 dimension")
        if not set(coverage.get("strata", [])).issuperset({
                "event_mode", "literal_form", "communicative_force",
                "cognitive_goal", "grounding_status", "interaction_relation",
                "expected_state"}):
            errors.append("coverage.strata is missing a corpus stratum")
    seen: set[str] = set()
    for index, event in enumerate(events):
        prefix = f"events[{index}]"
        for key in ("id", "signal", "event_mode", "literal_form",
                    "communicative_force", "cognitive_goal",
                    "grounding_status", "interaction_relation",
                    "evidence", "expected_state"):
            if key not in event:
                errors.append(f"{prefix} missing {key}")
        event_id = event.get("id")
        if not isinstance(event_id, str) or not event_id:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif event_id in seen:
            errors.append(f"duplicate event id: {event_id}")
        else:
            seen.add(event_id)
        if not str(event.get("signal", "")).strip():
            errors.append(f"{prefix}.signal must be non-empty")
        if event.get("event_mode") not in EVENT_MODES:
            errors.append(f"{prefix}.event_mode is invalid")
        if event.get("interaction_relation") not in RELATIONS:
            errors.append(f"{prefix}.interaction_relation is invalid")
        if event.get("communicative_force") not in FORCES:
            errors.append(f"{prefix}.communicative_force is invalid")
        if event.get("cognitive_goal") not in GOALS:
            errors.append(f"{prefix}.cognitive_goal is invalid")
        if event.get("grounding_status") not in GROUNDING:
            errors.append(f"{prefix}.grounding_status is invalid")
        if event.get("expected_state") not in STATES:
            errors.append(f"{prefix}.expected_state is invalid")
        evidence = event.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence must be a non-empty list")
        else:
            for item in evidence:
                if item not in EVIDENCE_KINDS:
                    errors.append(f"{prefix}.evidence contains invalid kind {item!r}")
        if event.get("event_mode") == "turn_compatible" and not event.get("turn_id"):
            errors.append(f"{prefix} turn_compatible event needs turn_id")
        if "communicative_acts" in event:
            acts = event.get("communicative_acts")
            if not isinstance(acts, list) or not acts:
                errors.append(f"{prefix}.communicative_acts must be a non-empty list")
            else:
                for act_index, act in enumerate(acts):
                    if not isinstance(act, dict):
                        errors.append(
                            f"{prefix}.communicative_acts[{act_index}] must be an object")
                        continue
                    if act.get("act_type") not in NEUTRAL_COMMUNICATIVE_ACTS:
                        errors.append(
                            f"{prefix}.communicative_acts[{act_index}].act_type is invalid")
                    if act.get("force") not in NEUTRAL_ACT_FORCES:
                        errors.append(
                            f"{prefix}.communicative_acts[{act_index}].force is invalid")
        if "expected_released_semantic_events" in event:
            expected_events = event.get("expected_released_semantic_events")
            if (not isinstance(expected_events, list) or not expected_events
                    or any(not isinstance(item, str) or not item.strip()
                           for item in expected_events)
                    or len(set(expected_events)) != len(expected_events)):
                errors.append(
                    f"{prefix}.expected_released_semantic_events must be a unique non-empty list of strings")
    return errors


def assert_trace_contract(trace: dict, *, expected_mode: str) -> None:
    """Assert deterministic, inspectable trace fields without snapshotting prose."""
    assert trace["turn_id"] is not None
    assert isinstance(trace.get("question"), str) and trace["question"].strip()
    assert isinstance(trace.get("reply"), str) and trace["reply"].strip()
    assert trace.get("reply_from") in {"agent", "adapter"}
    assert trace.get("parse", {}).get("comp_reply_text") or trace["reply"]
    if expected_mode == "turn_compatible":
        assert trace["turn_id"] > 0


def validate_candidate_lifecycle_trace(trace: dict) -> list[str]:
    """Validate an *observed* Phase 4 trace without inventing candidates.

    The caller must pass a trace extracted from graph nodes created by the
    runtime.  An absent trace is therefore not an error here: most Phase 0
    communication events do not create a deliberation.  If a trace is
    present, this validator requires the native Phase 4 lifecycle markers and
    checks only evidence that can be observed in that trace.
    """
    errors: list[str] = []
    if not isinstance(trace, dict):
        return ["candidate/lifecycle trace must be an object"]
    if not isinstance(trace.get("event_id"), str) or not trace["event_id"]:
        errors.append("candidate/lifecycle trace needs event_id")
    event_mode = trace.get("event_mode")
    if event_mode is not None and event_mode not in EVENT_MODES:
        errors.append("candidate/lifecycle trace has an invalid event_mode")
    if event_mode == "turn_compatible" and not trace.get("turn_id"):
        errors.append("turn_compatible candidate/lifecycle trace needs turn_id")
    # A deliberation can be observed from an asynchronous or unsolicited
    # event.  Do not impose a turn identifier on the cognition trace.
    if not isinstance(trace.get("deliberation_id"), str) or not trace["deliberation_id"]:
        errors.append("candidate/lifecycle trace needs observed deliberation_id")
    if trace.get("contract") != PHASE4_TRACE_CONTRACT:
        errors.append("candidate/lifecycle trace must reference the Phase 4 contract")
    source = trace.get("candidate_source")
    if source not in PHASE4_CANDIDATE_SOURCES:
        errors.append("candidate/lifecycle trace has an invalid candidate_source")
    status = trace.get("status")
    if status not in PHASE4_LIFECYCLE_STATES:
        errors.append("candidate/lifecycle trace has an invalid lifecycle status")
    if trace.get("candidate_trace_complete") != 1.0:
        errors.append("candidate/lifecycle trace is not marked complete")
    count = trace.get("source_candidate_count")
    if not isinstance(count, (int, float)) or count < 0 or int(count) != count:
        errors.append("source_candidate_count must be a non-negative integer")
        count = 0
    candidates = trace.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidate/lifecycle trace needs observed candidates")
        candidates = []
    if int(count) != len(candidates):
        errors.append("source_candidate_count must equal observed candidate count")
    if int(count) == 0 and status != "no_candidate":
        errors.append("an empty observed candidate set must be no_candidate")
    for index, candidate in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not isinstance(candidate.get("candidate_id"), str) or not candidate["candidate_id"]:
            errors.append(f"{prefix} needs candidate_id")
        if candidate.get("status") not in PHASE4_LIFECYCLE_STATES | {"rejected"}:
            errors.append(f"{prefix} has an invalid lifecycle status")
    if status == "resolved":
        settlement = trace.get("settlement")
        if not isinstance(settlement, dict) or settlement.get("settle_back_trace") != 1.0:
            errors.append("resolved deliberation needs observed settle-back evidence")
    return errors
