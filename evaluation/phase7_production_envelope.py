"""Phase 7 follow-up: bounded production-shaped communication envelope.

This evaluation harness reuses the fixed corpus and the live communication
boundary.  It does not add a parser, classifier, reply policy, or cognitive
state inference.  The stable readback is deliberately structural: typed
event/interpretation evidence, graph residence, and whether production had a
reply/error outcome.  Surface text is not included in replay semantics.
"""
from __future__ import annotations

import json
import platform
import resource
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from evaluation.conversational_manifold_phase0 import load_corpus
from substrate.boot_all import (
    _read_seed_index,
    _select_seed_ids,
    load_all_seeds,
    resolve_graph_content_refs,
)
from substrate.boot_profiles import load_conversation_seed_profile
from substrate.seed_loader import SEED_DIR
from substrate.world_adapter import WorldAdapter


SCHEMA = "phase7-production-communication-envelope.v11"
PROFILE_PARITY_SCHEMA = "phase7-seed-profile-corpus-parity.v4"
RSS_MEMORY_LIMIT_BYTES = 200 * 1024 * 1024
# Retain the public name used by existing report schemas and callers. This
# bound is applied to both absolute RSS and measured growth fields.
RSS_GROWTH_LIMIT = RSS_MEMORY_LIMIT_BYTES
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
    """Use the same signal-only ingress classifier as production turns."""
    return WorldAdapter.classify_speech_act(str(event.get("signal") or ""))


def _event_content_candidates(events: Sequence[Mapping[str, Any]]) -> list[str]:
    """Collect mechanical lexical candidates without consulting corpus labels."""
    return sorted({
        token
        for event in events
        for token in WorldAdapter.lexical_candidates(
            str(event.get("signal") or ""))
    })


def _runtime_context(event: Mapping[str, Any]) -> dict[str, Any]:
    """Transport interaction metadata, never corpus evidence annotations."""
    return {
        "interaction_mode": event["event_mode"],
        "interaction_relation": event.get("interaction_relation"),
    }


def _graph_counts(agent: WorldAdapter) -> dict[str, int]:
    return {
        "nodes": agent.s.node_count(),
        "edges": agent.s.edge_count(),
        "messages": len(agent.s.nodes("Message")),
        "turns": len(agent.s.nodes("Turn")),
        "interpretations": len(agent.s.nodes("CommunicationInterpretation")),
        "discourse_events": len(agent.s.nodes("DiscourseEvent")),
    }


def _resolved_graph_content_evidence(
    agent: WorldAdapter, inbound: Any, *, indexed_edge_types=(),
    content_node_provenance=None,
) -> dict:
    """Read typed referents and direct edges among them from the live graph."""
    referents = {}
    ref_contexts = []
    provider_refs = set()
    for mention in agent.inner.neighbours(inbound, "has_mention"):
        for concept in agent.inner.neighbours(mention, "refers_to"):
            if not agent.s.has_node(concept):
                continue
            node = agent.s.node(concept)
            if node.get("type") != "Concept":
                continue
            name = node.get("attrs", {}).get("name")
            if isinstance(name, str) and name:
                referents[concept] = {"type": "Concept", "name": name}
                groups = set()
                for microtheory in agent.s.in_neighbours(
                        concept, "has_concept"):
                    if not agent.s.has_node(microtheory):
                        continue
                    group = agent.s.node(microtheory).get("attrs", {}).get("name")
                    if isinstance(group, str) and group:
                        groups.add(f"microtheory:{group}")
                if groups:
                    ref_contexts.append({
                        "ref": {"type": "Concept", "name": name},
                        "group_keys": sorted(groups),
                    })
                provider = (content_node_provenance or {}).get(
                    int(concept.value))
                if (provider and provider.get("type") == "Concept"
                        and provider.get("name") == name):
                    provider_refs.add((name, str(provider["seed_id"])))

    refs = sorted({(row["type"], row["name"])
                   for row in referents.values()})
    connections = set()
    for source_id, source_ref in referents.items():
        for edge_type in indexed_edge_types:
            for target_id in agent.s.neighbours(source_id, edge_type):
                target_ref = referents.get(target_id)
                if target_ref is not None:
                    connections.add((source_ref["type"], source_ref["name"],
                                     edge_type, target_ref["type"],
                                     target_ref["name"]))
    return {
        "refs": [{"type": node_type, "name": name}
                 for node_type, name in refs],
        "ref_contexts": sorted(
            ref_contexts,
            key=lambda row: (row["ref"]["type"], row["ref"]["name"],
                             row["group_keys"])),
        "graph_provider_refs": [
            {"ref": {"type": "Concept", "name": name},
             "seed_id": seed_id}
            for name, seed_id in sorted(provider_refs)
        ],
        "connections": [
            {"src": {"type": row[0], "name": row[1]},
             "edge": row[2],
             "tgt": {"type": row[3], "name": row[4]}}
            for row in sorted(connections)
        ],
    }


def _resolve_graph_ref_plan(
    event_evidence: Sequence[Mapping[str, Any]], *, seed_index=None,
) -> dict:
    """Resolve graph-readback evidence into a diagnostic seed-scope plan."""
    if seed_index is None:
        seed_index, _ = _read_seed_index(SEED_DIR)
    resolved_by_seed: dict[str, set[tuple[str, str]]] = {}
    event_plans = []
    unresolved_total = {
        "missing_graph_refs": 0, "ambiguous_graph_refs": 0,
        "invalid_graph_providers": 0, "unprovided_graph_refs": 0,
    }
    for event in event_evidence:
        scoped, unresolved = resolve_graph_content_refs(
            event.get("refs") or (), seed_index=seed_index,
            graph_connections=event.get("connections") or (),
            graph_ref_contexts=event.get("ref_contexts") or (),
            graph_provider_refs=event.get("graph_provider_refs") or (),
        )
        for seed_id, refs in scoped.items():
            resolved_by_seed.setdefault(seed_id, set()).update(
                (str(ref["type"]), str(ref["name"])) for ref in refs)
        for key in unresolved_total:
            unresolved_total[key] += len(unresolved[key])
        event_plans.append({
            "event_id": event.get("id"),
            "graph_ref_count": len(event.get("refs") or ()),
            "graph_connection_count": len(event.get("connections") or ()),
            "graph_ref_context_count": len(event.get("ref_contexts") or ()),
            "graph_provider_ref_count": len(
                event.get("graph_provider_refs") or ()),
            "resolved_scoped_content_refs": scoped,
            "unresolved": unresolved,
        })
    scoped_content_refs = {
        seed_id: [{"type": node_type, "name": name}
                  for node_type, name in sorted(refs)]
        for seed_id, refs in sorted(resolved_by_seed.items())
    }
    _, selection_unresolved = _select_seed_ids(
        seed_index, scoped_content_refs=scoped_content_refs)
    return {
        "method": "live_graph_referents_and_direct_edges_v1",
        "surface_text_used": False,
        "expected_labels_used": False,
        "event_plans": event_plans,
        "scoped_content_refs": scoped_content_refs,
        "unresolved_reference_counts": unresolved_total,
        "provider_scope_resolution_complete": not any(
            unresolved_total[key] for key in (
                "missing_graph_refs", "ambiguous_graph_refs",
                "invalid_graph_providers")),
        "seed_provider_coverage_complete": not unresolved_total[
            "unprovided_graph_refs"],
        "selection_unresolved": selection_unresolved,
        "selection_closure_complete": not any(selection_unresolved.values()),
    }


def _load_graph_ref_plan(path: str | Path) -> tuple[dict, list[str]]:
    """Load a validated full-profile graph-prepass report for replay."""
    with open(path, encoding="utf-8") as stream:
        report = json.load(stream)
    plan = report.get("graph_ref_plan")
    if report.get("seed_profile") != "full" or not isinstance(plan, dict):
        raise ValueError("graph-ref plan must come from a full-profile pre-pass")
    if report.get("errors"):
        raise ValueError("graph-ref pre-pass report contains execution errors")
    if plan.get("method") != "live_graph_referents_and_direct_edges_v1":
        raise ValueError("unsupported graph-ref plan method")
    event_ids = [str(event.get("event_id"))
                 for event in plan.get("event_plans", ())
                 if isinstance(event, dict) and event.get("event_id")]
    if len(event_ids) != len(set(event_ids)) or not event_ids:
        raise ValueError("graph-ref plan has missing or duplicate event IDs")
    if report.get("event_count") != len(event_ids):
        raise ValueError("graph-ref plan does not cover the full pre-pass event count")
    refs = plan.get("scoped_content_refs")
    if not isinstance(refs, dict):
        raise ValueError("graph-ref plan is missing scoped content refs")
    return plan, event_ids


def _parity_value(value: Any) -> Any:
    """Strip identity and overt wording from a structural graph readback."""
    if isinstance(value, Mapping):
        ignored = {
            "id", "node_id", "message_id", "turn_id", "turn_message_id",
            "goal_id", "held_answer_id", "grounding_evidence_id",
            "evidence_id", "production_receipt_id",
            "origin_turn_id", "text", "surface", "reply", "question",
            "comp_reply_text", "raw",
        }
        return {
            str(key): _parity_value(item)
            for key, item in value.items()
            if str(key) not in ignored
        }
    if isinstance(value, (list, tuple)):
        return [_parity_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


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
    trace = agent.reply_turn_trace(int(inbound.value)) or {}
    receipt_rows = []
    inbound_id = int(inbound.value)
    for receipt in agent.s.nodes("ProductionGateReceipt"):
        attrs = dict(agent.s.node(receipt)["attrs"])
        linked = inbound in agent.inner.neighbours(receipt, "for_message")
        if attrs.get("turn_message_id") == inbound_id or linked:
            receipt_rows.append(_parity_value(attrs))
    receipt_rows.sort(key=lambda row: json.dumps(row, sort_keys=True))
    interpretation_keys = (
        "schema", "evidence_schema", "evidence_force", "evidence_goal",
        "cognitive_disposition", "cognitive_goal", "arbitration_basis",
        "communicative_force", "cognitive_goal_hypothesis",
        "communicative_force_hypothesis", "grounding_status",
        "grounding_evidence_path", "interaction_mode", "interaction_relation",
        "literal_form", "relation_focus", "relation_support",
        "language_world_dependency", "language_world_support",
        "language_repair_evidence", "language_repair_focus",
        "language_referent_status", "language_resolved_reference_status",
        "authority_status",
    )
    message_keys = (
        "comp_kind", "comp_dispatch_path", "comp_intent",
        "comp_relation_focus", "comp_anaphor", "communication_route",
        "adjacency_replied_act", "instruction_outcome",
    )
    interpretation_readback = {
        key: interpretation[key]
        for key in interpretation_keys if key in interpretation
    }
    message_readback = {
        key: message_attrs[key]
        for key in message_keys if key in message_attrs
    }
    turn_readback = {
        "goals": _parity_value(trace.get("goals") or []),
        "intent": _parity_value(trace.get("intent")),
        # Mentions retain only graph referents, never token/surface spellings.
        "mention_referents": [
            _parity_value(item.get("refers_to") or [])
            for item in (trace.get("mentions") or [])
        ],
        "current_topic": trace.get("current_topic"),
        "concerns": _parity_value(trace.get("concerns") or []),
        "deliberations": _parity_value(trace.get("deliberations") or []),
        "reply_commitment": _parity_value(trace.get("reply_commitment")),
        "answer_commitment": _parity_value(trace.get("answer_commitment")),
        "reply_from": trace.get("reply_from"),
        "reply_message_present": trace.get("reply_id") is not None,
    }
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
        "interpretation": _parity_value(interpretation_readback),
        "message": _parity_value(message_readback),
        "turn": _parity_value(turn_readback),
        "production_receipts": receipt_rows,
        "communication_route": message_attrs.get("communication_route"),
        "reply_present": bool(str(reply).strip()),
        "explicit_error": str(reply).strip().lower().rstrip(".!?") == (
            "error: no communicative response could be generated"),
        "trace_present": bool(agent.reply_turn_trace(inbound)),
    }


def _run(events: Sequence[Mapping[str, Any]], *,
         prewarm_wordnet: bool = False,
         seed_profile: str = "full",
         content_keys: Sequence[str] = (),
         content_candidates: Sequence[str] | None = None,
         incremental_content_prepass: bool = False,
         scoped_content_refs: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
         emit_graph_ref_plan: bool = False,
         ) -> dict[str, Any]:
    if seed_profile == "conversation":
        if incremental_content_prepass:
            content_candidates = ()
        elif content_candidates is None:
            content_candidates = _event_content_candidates(events)
    rss_before_boot = _rss_bytes()
    boot_started = time.perf_counter_ns()
    agent = WorldAdapter(seeds=())
    if seed_profile == "full":
        boot_report = load_all_seeds(
            agent, track_content_node_provenance=emit_graph_ref_plan)
        selection = None
    elif seed_profile == "conversation":
        boot_report = {}
        selection = load_conversation_seed_profile(
            agent, content_keys=content_keys,
            content_candidates=content_candidates,
            scoped_content_refs=scoped_content_refs,
            incremental_content_loading=incremental_content_prepass)
    else:
        raise ValueError(f"unknown Phase 7 seed profile: {seed_profile!r}")
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
    content_prepass_events: list[dict[str, Any]] = []
    graph_ref_evidence: list[dict[str, Any]] = []
    graph_seed_index = None
    graph_edge_types = ()
    content_node_provenance = (boot_report or {}).get(
        "content_node_provenance") or {}
    if emit_graph_ref_plan:
        graph_seed_index, _ = _read_seed_index(SEED_DIR)
        graph_edge_types = tuple(sorted({
            connection["edge"]
            for meta in graph_seed_index.values()
            for connection in meta.get("content_connections", ())
        }))
    rss_samples: list[dict[str, Any]] = []
    pending_io_dispatch_ns: list[int] = []
    dispatch_impl = agent._dispatch_pending_io

    def measured_pending_io_dispatch(*args: Any, **kwargs: Any) -> Any:
        dispatch_started = time.perf_counter_ns()
        try:
            return dispatch_impl(*args, **kwargs)
        finally:
            pending_io_dispatch_ns.append(
                time.perf_counter_ns() - dispatch_started)

    # Instrument the existing host-I/O boundary without changing its routing
    # choices. Keep these timings separate from the semantic replay record.
    agent._dispatch_pending_io = measured_pending_io_dispatch
    started = time.perf_counter_ns()
    errors: list[str] = []
    for event in events:
        event_started = time.perf_counter_ns()
        modules_before_event = set(sys.modules)
        event_rss_before = _rss_bytes()
        event_graph_before = _graph_counts(agent)
        pending_io_dispatch_ns.clear()
        try:
            for held in (event.get("setup") or {}).get("held_answers") or ():
                agent._persist_held_answer(
                    str(held["topic"]), str(held["answer"]))
            conversation_started = time.perf_counter_ns()
            reply = agent.converse(
                event["signal"],
                speech_act=_speech_act(event),
                context=_runtime_context(event),
            ) or ""
            if seed_profile == "conversation":
                content_prepass_events.append({
                    "id": str(event["id"]),
                    **(agent._last_conversation_content_prepass or {}),
                })
            conversation_elapsed_ms = (
                time.perf_counter_ns() - conversation_started
            ) / 1_000_000.0
            runtime_modules = set(sys.modules)
            rss_after_conversation = _rss_bytes()
            dispatch_durations_ms = [duration / 1_000_000.0
                                     for duration in pending_io_dispatch_ns]
            inbound = agent._last_turn_inbound
            if emit_graph_ref_plan:
                graph_ref_evidence.append({
                    "id": event["id"],
                    **_resolved_graph_content_evidence(
                        agent, inbound, indexed_edge_types=graph_edge_types,
                        content_node_provenance=content_node_provenance),
                })
            observation_started = time.perf_counter_ns()
            observations.append(_stable_observation(agent, event, reply, inbound))
            observation_elapsed_ms = (
                time.perf_counter_ns() - observation_started
            ) / 1_000_000.0
            modules_after_observation = set(sys.modules)
            rss_after_observation = _rss_bytes()
            rss_samples.append({
                "id": event["id"],
                "rss_bytes": rss_after_observation,
                "conversation_rss_bytes": rss_after_conversation,
                "graph": _graph_counts(agent),
                "elapsed_ms": (time.perf_counter_ns() - event_started)
                / 1_000_000.0,
                "conversation_elapsed_ms": conversation_elapsed_ms,
                "pending_io_dispatch": {
                    "call_count": len(dispatch_durations_ms),
                    "total_ms": sum(dispatch_durations_ms),
                    "max_ms": max(dispatch_durations_ms, default=0.0),
                },
                "observation_elapsed_ms": observation_elapsed_ms,
                "rss_delta_bytes": max(0, rss_after_observation - event_rss_before),
                "conversation_rss_delta_bytes": max(
                    0, rss_after_conversation - event_rss_before),
                "observation_rss_delta_bytes": max(
                    0, rss_after_observation - rss_after_conversation),
                "runtime_new_modules": sorted(
                    runtime_modules - modules_before_event),
                "observation_new_modules": sorted(
                    modules_after_observation - runtime_modules),
                "new_modules": sorted(
                    modules_after_observation - modules_before_event),
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
    conversation_rss_peak = max(
        [rss_after_boot] + [sample["conversation_rss_bytes"]
                            for sample in rss_samples])
    conversation_rss_growth = max(
        0, conversation_rss_peak - rss_before_boot)
    conversation_latency_total = sum(
        sample["conversation_elapsed_ms"] for sample in rss_samples)
    result = {
        "schema": SCHEMA,
        "seed_profile": seed_profile,
        "content_keys": sorted(set(content_keys)),
        "content_candidate_resolution": (selection or {}).get(
            "selection", {}).get("content_candidate_resolution"),
        "content_prepass_mode": (
            "per_turn_incremental" if incremental_content_prepass else
            "batch_before_boot" if seed_profile == "conversation" else "none"),
        "content_prepass_events": content_prepass_events,
        "scoped_content_refs": {
            str(seed_id): [dict(ref) for ref in refs]
            for seed_id, refs in sorted(
                ((scoped_content_refs or {})
                 if seed_profile == "conversation" else {}).items())
        },
        "content_slices": (selection or {}).get("content_slices", {}),
        "selection_complete": (selection or {}).get("selection_complete"),
        "selected_seed_ids": (selection or {}).get(
            "selection", {}).get("selected_seed_ids", []),
        "selection_unresolved": (selection or {}).get(
            "selection", {}).get("unresolved"),
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
        "conversation_rss_peak_bytes": conversation_rss_peak,
        "conversation_rss_growth_bytes": conversation_rss_growth,
        "conversation_latency_total_ms": conversation_latency_total,
        "conversation_latency_max_ms": max(
            (sample["conversation_elapsed_ms"] for sample in rss_samples),
            default=0.0),
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
            "conversation_rss_growth_bounded": (
                conversation_rss_growth < RSS_GROWTH_LIMIT),
            "conversation_absolute_rss_bounded": (
                conversation_rss_peak < RSS_GROWTH_LIMIT),
        },
        "surface_text_used_as_semantics": False,
        "turn_boundary_required": False,
    }
    if emit_graph_ref_plan:
        result["graph_ref_plan"] = _resolve_graph_ref_plan(
            graph_ref_evidence, seed_index=graph_seed_index)
    return result


def measure_production_envelope(
    corpus: Mapping[str, Any] | None = None,
    event_ids: Sequence[str] = PROFILE_EVENT_IDS,
    *,
    prewarm_wordnet: bool = False,
    seed_profile: str = "full",
    content_keys: Sequence[str] = (),
    incremental_content_prepass: bool = False,
    scoped_content_refs: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    emit_graph_ref_plan: bool = False,
) -> dict[str, Any]:
    corpus = load_corpus() if corpus is None else corpus
    by_id = {str(event["id"]): event for event in corpus["events"]}
    events = [by_id[event_id] for event_id in event_ids]
    first = _run(events, prewarm_wordnet=prewarm_wordnet,
                 seed_profile=seed_profile, content_keys=content_keys,
                 incremental_content_prepass=incremental_content_prepass,
                 scoped_content_refs=scoped_content_refs,
                 emit_graph_ref_plan=emit_graph_ref_plan)
    replay = _run(events, prewarm_wordnet=prewarm_wordnet,
                  seed_profile=seed_profile, content_keys=content_keys,
                  incremental_content_prepass=incremental_content_prepass,
                  scoped_content_refs=scoped_content_refs,
                  emit_graph_ref_plan=emit_graph_ref_plan)
    stable_keys = ("event_ids", "event_count", "observations", "errors",
                   "seed_profile", "content_keys", "scoped_content_refs",
                   "content_candidate_resolution",
                   "content_prepass_mode", "content_prepass_events",
                   "graph_ref_plan",
                   "content_slices",
                   "selected_seed_ids", "selection_unresolved",
                   "graph_growth", "surface_text_used_as_semantics",
                   "turn_boundary_required")
    left = {key: first.get(key) for key in stable_keys}
    right = {key: replay.get(key) for key in stable_keys}
    first["replay_equal"] = left == right
    first["replay_difference"] = None if first["replay_equal"] else {
        "first": left, "replay": right,
    }
    return first


def compare_seed_profile_corpus(
    corpus: Mapping[str, Any] | None = None,
    event_ids: Sequence[str] | None = None,
    content_keys: Sequence[str] = (),
    scoped_content_refs: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    incremental_content_prepass: bool = False,
) -> dict[str, Any]:
    """Compare full boot with the connected conversation profile structurally.

    This performs one corpus pass per profile. It is a parity audit, not a
    replay-determinism claim; ``measure_production_envelope`` remains the
    repeated-trial check for its selected workload. Surface strings and
    graph-identity numbers are excluded from the comparison.
    """
    corpus = load_corpus() if corpus is None else corpus
    if event_ids is None:
        events = list(corpus["events"])
    else:
        by_id = {str(event["id"]): event for event in corpus["events"]}
        missing = [str(event_id) for event_id in event_ids
                   if str(event_id) not in by_id]
        if missing:
            raise ValueError(f"unknown Phase 0 event IDs: {missing}")
        events = [by_id[str(event_id)] for event_id in event_ids]
    if not events:
        raise ValueError("profile parity requires at least one event")

    full = _run(events, seed_profile="full")
    content_candidates = _event_content_candidates(events)
    connected = _run(events, seed_profile="conversation",
                     content_keys=content_keys,
                     content_candidates=(None if incremental_content_prepass
                                          else content_candidates),
                     scoped_content_refs=scoped_content_refs,
                     incremental_content_prepass=incremental_content_prepass)
    full_rows = {row["id"]: row for row in full["observations"]}
    connected_rows = {row["id"]: row for row in connected["observations"]}
    mismatches = []
    for event in events:
        event_id = str(event["id"])
        left, right = full_rows.get(event_id), connected_rows.get(event_id)
        if left is None or right is None:
            mismatches.append({
                "id": event_id,
                "differing_fields": ["observation_missing"],
            })
            continue
        differing = sorted(
            key for key in set(left) | set(right)
            if left.get(key) != right.get(key)
        )
        if differing:
            mismatches.append({"id": event_id, "differing_fields": differing})

    return {
        "schema": PROFILE_PARITY_SCHEMA,
        "event_ids": [str(event["id"]) for event in events],
        "event_count": len(events),
        "content_candidate_prepass": {
            "method": ("world_adapter_per_turn_mention_tokenization_v1"
                       if incremental_content_prepass else
                       "world_adapter_mention_tokenization_v1"),
            "candidate_count": len(content_candidates),
            "candidates": content_candidates,
            "corpus_labels_used": False,
        },
        "profiles": {"full": full, "conversation": connected},
        "structural_parity": {
            "equal": not mismatches and not full["errors"]
            and not connected["errors"]
            and connected.get("selection_complete") is not False,
            "matched_event_count": len(events) - len(mismatches),
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "full_error_count": len(full["errors"]),
            "conversation_error_count": len(connected["errors"]),
            "conversation_seed_selection_complete": connected.get(
                "selection_complete"),
            "surface_text_used_as_semantics": False,
            "graph_identity_numbers_compared": False,
        },
        "replay_determinism_verified": False,
        "resource_measurements_independent_processes": False,
    }


__all__ = ["PROFILE_EVENT_IDS", "PROFILE_PARITY_SCHEMA",
           "RSS_GROWTH_LIMIT", "SCHEMA", "compare_seed_profile_corpus",
           "measure_production_envelope"]


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Compare full-boot and connected-profile corpus structure.")
    parser.add_argument("--output", required=True,
                        help="JSON report path")
    parser.add_argument("--event-id", action="append", dest="event_ids",
                        help=("Optional event subset. Comparison mode defaults "
                              "to the full corpus; --profile-run defaults to "
                              "the named eight-event profile slice."))
    parser.add_argument("--all-events", action="store_true",
                        help="With --profile-run, measure the full corpus instead of its eight-event default")
    parser.add_argument("--content-key", action="append", dest="content_keys",
                        help="Upstream lexical/content candidates for selective seeds")
    parser.add_argument(
        "--scoped-content-ref", action="append", default=[],
        help="Typed scoped seed ref as SEED_ID:TYPE:NAME (repeatable)")
    parser.add_argument("--profile-run", choices=("full", "conversation"),
                        help="Measure one profile only (use a fresh process per invocation)")
    parser.add_argument("--verify-replay", action="store_true",
                        help="Replay this profile twice and compare stable observations")
    parser.add_argument("--incremental-content-prepass", action="store_true",
                        help="Select content from each live event immediately before its turn")
    parser.add_argument(
        "--emit-graph-ref-plan", action="store_true",
        help=("On a full-profile run, emit seed-scoped refs derived only from "
              "live graph referents/connections; unresolved refs stay explicit"))
    parser.add_argument(
        "--graph-ref-plan", type=Path,
        help=("Replay a validated full-profile graph-reference pre-pass as "
              "scoped content refs (diagnostic, unresolved refs stay omitted)"))
    args = parser.parse_args()
    scoped_content_refs = {}
    for encoded in args.scoped_content_ref:
        seed_id, separator, typed_name = str(encoded).partition(":")
        node_type, separator2, name = typed_name.partition(":")
        if not separator or not separator2 or not seed_id or not node_type or not name:
            parser.error("--scoped-content-ref must be SEED_ID:TYPE:NAME")
        scoped_content_refs.setdefault(seed_id, []).append(
            {"type": node_type, "name": name})
    graph_ref_plan = None
    graph_plan_event_ids = None
    if args.graph_ref_plan:
        try:
            graph_ref_plan, graph_plan_event_ids = _load_graph_ref_plan(
                str(args.graph_ref_plan))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            parser.error(f"invalid --graph-ref-plan: {exc}")
        if scoped_content_refs:
            parser.error("--graph-ref-plan cannot be combined with --scoped-content-ref")
        scoped_content_refs = graph_ref_plan["scoped_content_refs"]
    if args.verify_replay and not args.profile_run:
        parser.error("--verify-replay requires --profile-run")
    if args.emit_graph_ref_plan and args.profile_run != "full":
        parser.error("--emit-graph-ref-plan requires --profile-run full")
    if args.emit_graph_ref_plan and args.graph_ref_plan:
        parser.error("--emit-graph-ref-plan cannot replay another graph-ref plan")
    if args.graph_ref_plan and args.profile_run == "full":
        parser.error("--graph-ref-plan is for conversation-profile/comparison replay")
    if args.profile_run:
        corpus = load_corpus()
        if args.all_events and args.event_ids:
            parser.error("--all-events cannot be combined with --event-id")
        selected_ids = (args.event_ids or
                        (graph_plan_event_ids if graph_plan_event_ids
                         and not args.all_events else None) or
                        ([str(event["id"]) for event in corpus["events"]]
                         if args.all_events else list(PROFILE_EVENT_IDS)))
        by_id = {str(event["id"]): event for event in corpus["events"]}
        missing = [event_id for event_id in selected_ids if event_id not in by_id]
        if missing:
            parser.error(f"unknown Phase 0 event IDs: {missing}")
        if args.verify_replay:
            result = measure_production_envelope(
                corpus=corpus,
                event_ids=selected_ids,
                seed_profile=args.profile_run,
                content_keys=args.content_keys or (),
                incremental_content_prepass=args.incremental_content_prepass,
                scoped_content_refs=scoped_content_refs or None,
                emit_graph_ref_plan=args.emit_graph_ref_plan,
            )
        else:
            result = _run(
                [by_id[event_id] for event_id in selected_ids],
                seed_profile=args.profile_run,
                content_keys=args.content_keys or (),
                incremental_content_prepass=args.incremental_content_prepass,
                scoped_content_refs=scoped_content_refs or None,
                emit_graph_ref_plan=args.emit_graph_ref_plan,
            )
        result["measurement_process"] = "fresh_cli_process"
        result["replay_determinism_verified"] = bool(args.verify_replay)
        result["resource_measurements_independent_processes"] = not args.verify_replay
        if graph_ref_plan is not None:
            if set(selected_ids) != set(graph_plan_event_ids):
                parser.error("selected events must match the graph-ref plan event coverage")
            result["graph_ref_plan_replay"] = {
                "source": str(args.graph_ref_plan),
                "provider_scope_resolution_complete": graph_ref_plan.get(
                    "provider_scope_resolution_complete"),
                "seed_provider_coverage_complete": graph_ref_plan.get(
                    "seed_provider_coverage_complete"),
                "unresolved_reference_counts": graph_ref_plan.get(
                    "unresolved_reference_counts"),
            }
    else:
        if graph_ref_plan is not None and args.event_ids:
            if set(args.event_ids) != set(graph_plan_event_ids):
                parser.error("selected events must match the graph-ref plan event coverage")
        result = compare_seed_profile_corpus(
            event_ids=args.event_ids,
            content_keys=args.content_keys or (),
            scoped_content_refs=scoped_content_refs or None,
            incremental_content_prepass=args.incremental_content_prepass,
        )
        if graph_ref_plan is not None:
            if set(result["event_ids"]) != set(graph_plan_event_ids):
                parser.error("graph-ref plan event coverage differs from comparison corpus")
            result["graph_ref_plan_replay"] = {
                "source": str(args.graph_ref_plan),
                "provider_scope_resolution_complete": graph_ref_plan.get(
                    "provider_scope_resolution_complete"),
                "seed_provider_coverage_complete": graph_ref_plan.get(
                    "seed_provider_coverage_complete"),
                "unresolved_reference_counts": graph_ref_plan.get(
                    "unresolved_reference_counts"),
            }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "events": result["event_count"],
        "profile": result.get("seed_profile"),
        "rss_after_bytes": result.get("rss_after_bytes"),
        "boot_and_event_rss_growth_bytes": result.get(
            "boot_and_event_rss_growth_bytes"),
        "parity": result.get("structural_parity"),
    }, sort_keys=True))
