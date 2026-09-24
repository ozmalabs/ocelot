"""Phase 7 follow-up: bounded production-shaped communication envelope.

This evaluation harness reuses the fixed corpus and the live communication
boundary.  It does not add a parser, classifier, reply policy, or cognitive
state inference.  The stable readback is deliberately structural: typed
event/interpretation evidence, graph residence, and whether production had a
reply/error outcome.  Surface text is not included in replay semantics.
"""
from __future__ import annotations

import platform
import resource
import time
from typing import Any, Mapping, Sequence

from evaluation.conversational_manifold_phase0 import load_corpus
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


SCHEMA = "phase7-production-communication-envelope.v2"
RSS_GROWTH_LIMIT = 100 * 1024 * 1024
PROFILE_EVENT_IDS = (
    "information_question",
    "direct_action",
    "unresolved_reference",
    "overlap_signal",
    "correction",
    "social_greeting",
    "unavailable_world",
    "error_empty",
)


def _rss_bytes() -> int:
    try:
        for line in open("/proc/self/status", encoding="utf-8"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if platform.system() == "Darwin" else 1024
    ))


def _speech_act(event: Mapping[str, Any]) -> str:
    literal = event["literal_form"]
    if literal == "interrogative":
        return "question"
    if literal == "social":
        return "greeting"
    if literal in {"imperative", "compound_imperative",
                   "imperative_with_politeness_marker"}:
        return "instruction"
    return "statement"


def _graph_counts(agent: WorldAdapter) -> dict[str, int]:
    return {
        "nodes": agent.s.node_count(),
        "edges": agent.s.edge_count(),
        "messages": len(agent.s.nodes("Message")),
        "turns": len(agent.s.nodes("Turn")),
        "interpretations": len(agent.s.nodes("CommunicationInterpretation")),
        "discourse_events": len(agent.s.nodes("DiscourseEvent")),
    }


def _stable_observation(agent: WorldAdapter, event: Mapping[str, Any],
                        reply: str, inbound: Any) -> dict[str, Any]:
    message_attrs = dict(agent.s.node(inbound)["attrs"])
    interpretation_id = message_attrs.get("communication_interpretation_id")
    interpretation = (
        dict(agent.s.node(interpretation_id)["attrs"])
        if interpretation_id is not None and agent.s.has_node(interpretation_id)
        else {}
    )
    event_id = message_attrs.get("discourse_event_id")
    discourse_event = (
        dict(agent.s.node(event_id)["attrs"])
        if event_id is not None and agent.s.has_node(event_id)
        else {}
    )
    # Keep this readback semantic-free with respect to surfaces.  Presence of
    # an explicit error is a production outcome, not a meaning classifier.
    return {
        "id": event["id"],
        "interaction_mode": interpretation.get("interaction_mode"),
        "interaction_relation": interpretation.get("interaction_relation"),
        "literal_form": interpretation.get("literal_form"),
        "event_payload_relation": discourse_event.get("payload", {}).get(
            "interaction_relation"),
        "event_payload_literal_form": discourse_event.get("payload", {}).get(
            "literal_form"),
        "interpretation_schema": interpretation.get("schema"),
        "evidence_schema": interpretation.get("evidence_schema"),
        "cognitive_disposition": interpretation.get("cognitive_disposition"),
        "communication_route": message_attrs.get("communication_route"),
        "reply_present": bool(str(reply).strip()),
        "explicit_error": str(reply).strip().lower().rstrip(".!?") == (
            "error: no communicative response could be generated"),
        "trace_present": bool(agent.reply_turn_trace(inbound)),
    }


def _run(events: Sequence[Mapping[str, Any]], *,
         prewarm_wordnet: bool = False) -> dict[str, Any]:
    rss_before_boot = _rss_bytes()
    boot_started = time.perf_counter_ns()
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    prewarm_started = time.perf_counter_ns()
    prewarm_completed = False
    prewarm_error = None
    if prewarm_wordnet:
        try:
            from nltk.corpus import wordnet as _wn
            _wn.ensure_loaded()
            prewarm_completed = True
        except Exception as exc:  # keep optional reference data non-fatal
            prewarm_error = f"{type(exc).__name__}: {exc}"
    prewarm_elapsed_ms = (
        (time.perf_counter_ns() - prewarm_started) / 1_000_000.0
        if prewarm_wordnet else 0.0
    )
    boot_elapsed_ms = (time.perf_counter_ns() - boot_started) / 1_000_000.0
    rss_after_boot = _rss_bytes()
    before = _graph_counts(agent)
    rss_before = _rss_bytes()
    observations: list[dict[str, Any]] = []
    rss_samples: list[dict[str, Any]] = []
    started = time.perf_counter_ns()
    errors: list[str] = []
    for event in events:
        event_started = time.perf_counter_ns()
        event_rss_before = _rss_bytes()
        event_graph_before = _graph_counts(agent)
        try:
            reply = agent.converse(
                event["signal"],
                speech_act=_speech_act(event),
                context={
                    "interaction_mode": event["event_mode"],
                    "interaction_relation": event.get("interaction_relation"),
                    "literal_form": event.get("literal_form"),
                },
            ) or ""
            inbound = agent._last_turn_inbound
            observations.append(_stable_observation(agent, event, reply, inbound))
            rss_samples.append({
                "id": event["id"],
                "rss_bytes": _rss_bytes(),
                "graph": _graph_counts(agent),
                "elapsed_ms": (time.perf_counter_ns() - event_started)
                / 1_000_000.0,
                "rss_delta_bytes": max(0, _rss_bytes() - event_rss_before),
                "graph_delta": {
                    key: _graph_counts(agent)[key] - event_graph_before[key]
                    for key in event_graph_before
                },
            })
        except Exception as exc:  # preserve a failed workload observation
            errors.append(f"{event['id']}: {type(exc).__name__}: {exc}")
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    after = _graph_counts(agent)
    rss_after = _rss_bytes()
    first_event_rss = (rss_samples[0]["rss_bytes"]
                       if rss_samples else rss_after)
    cold_start_growth = max(0, first_event_rss - rss_before)
    steady_state_growth = max(0, rss_after - first_event_rss)
    return {
        "schema": SCHEMA,
        "event_ids": [event["id"] for event in events],
        "event_count": len(events),
        "boot_elapsed_ms": boot_elapsed_ms,
        "prewarm_wordnet_requested": bool(prewarm_wordnet),
        "prewarm_wordnet_completed": prewarm_completed,
        "prewarm_wordnet_elapsed_ms": prewarm_elapsed_ms,
        "prewarm_wordnet_error": prewarm_error,
        "rss_before_boot_bytes": rss_before_boot,
        "rss_after_boot_bytes": rss_after_boot,
        "boot_rss_growth_bytes": max(0, rss_after_boot - rss_before_boot),
        "observations": observations,
        "errors": errors,
        "rss_samples": rss_samples,
        "graph_before": before,
        "graph_after": after,
        "graph_growth": {
            key: after[key] - before[key] for key in before
        },
        "latency_ms": elapsed_ms,
        "rss_before_bytes": rss_before,
        "rss_after_bytes": rss_after,
        "rss_growth_bytes": max(0, rss_after - rss_before),
        "boot_and_event_rss_growth_bytes": max(
            0, rss_after - rss_before_boot),
        "cold_start_rss_growth_bytes": cold_start_growth,
        "steady_state_rss_growth_bytes": steady_state_growth,
        "resource_assertions": {
            "rss_measured": rss_after >= 0,
            "rss_growth_bounded": (rss_after - rss_before) < RSS_GROWTH_LIMIT,
            "boot_and_event_rss_growth_bounded": (
                rss_after - rss_before_boot) < RSS_GROWTH_LIMIT,
            "steady_state_rss_growth_bounded": steady_state_growth < RSS_GROWTH_LIMIT,
        },
        "surface_text_used_as_semantics": False,
        "turn_boundary_required": False,
    }


def measure_production_envelope(
    corpus: Mapping[str, Any] | None = None,
    event_ids: Sequence[str] = PROFILE_EVENT_IDS,
    *,
    prewarm_wordnet: bool = False,
) -> dict[str, Any]:
    corpus = load_corpus() if corpus is None else corpus
    by_id = {str(event["id"]): event for event in corpus["events"]}
    events = [by_id[event_id] for event_id in event_ids]
    first = _run(events, prewarm_wordnet=prewarm_wordnet)
    replay = _run(events, prewarm_wordnet=prewarm_wordnet)
    stable_keys = ("event_ids", "event_count", "observations", "errors",
                   "graph_growth", "surface_text_used_as_semantics",
                   "turn_boundary_required")
    left = {key: first[key] for key in stable_keys}
    right = {key: replay[key] for key in stable_keys}
    first["replay_equal"] = left == right
    first["replay_difference"] = None if first["replay_equal"] else {
        "first": left, "replay": right,
    }
    return first


__all__ = ["PROFILE_EVENT_IDS", "RSS_GROWTH_LIMIT", "SCHEMA",
           "measure_production_envelope"]
