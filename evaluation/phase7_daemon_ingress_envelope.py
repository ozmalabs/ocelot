"""Profile daemon chat ingress, native cycles, and optional host completion.

This keeps request-thread work separate from the legacy synchronous
``WorldAdapter.converse`` measurement. It uses the daemon's actual text ingress
and graph-authored async cycle budget. Signal-only mode omits host actions;
completion mode runs the daemon host-action dispatcher and drains bounded
retrieval I/O so pending work and full-turn latency are measured.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.phase7_production_envelope import (
    RSS_GROWTH_LIMIT,
    _graph_counts,
    _rss_bytes,
    _stable_observation,
)
from evaluation.phase8_corpus_runner import _runtime_context
from substrate.boot_profiles import (
    load_conversation_seed_profile,
    prepass_conversation_turn,
)
from substrate.world_adapter import WorldAdapter


SCHEMA = "phase7-daemon-chat-ingress-envelope.v10"
RSS_LIMIT = RSS_GROWTH_LIMIT
INGRESS_LIMIT_MS = 50.0
NATIVE_CYCLE_LIMIT_MS = 150.0


def _graph_node_type_counts(agent: WorldAdapter) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for node_id in agent.s.nodes():
        if not agent.s.has_node(node_id):
            continue
        node = agent.s.node(node_id)
        counts[str(node.get("type") or "unknown")] += 1
    return dict(sorted(counts.items()))


def _graph_node_retention_details(
        agent: WorldAdapter, node_types: Sequence[str]) -> dict[str, Any]:
    details: dict[str, Any] = {}
    for node_type in node_types:
        node_ids = agent.s.nodes(node_type)
        attr_keys: Counter[str] = Counter()
        outgoing_types: Counter[str] = Counter()
        incoming_types: Counter[str] = Counter()
        outgoing_links = incoming_links = 0
        isolated = 0
        samples = []
        for node_id in node_ids:
            if not agent.s.has_node(node_id):
                continue
            node = agent.s.node(node_id)
            attrs = node.get("attrs", {})
            attr_keys.update(str(key) for key in attrs)
            out_neighbors = agent.s.neighbours(node_id)
            in_neighbors = agent.s.in_neighbours(node_id)
            outgoing_links += len(out_neighbors)
            incoming_links += len(in_neighbors)
            if not out_neighbors and not in_neighbors:
                isolated += 1
            for neighbor in out_neighbors:
                if agent.s.has_node(neighbor):
                    outgoing_types[str(agent.s.node(neighbor).get("type") or "unknown")] += 1
            for neighbor in in_neighbors:
                if agent.s.has_node(neighbor):
                    incoming_types[str(agent.s.node(neighbor).get("type") or "unknown")] += 1
            if len(samples) < 3:
                def neighbor_samples(neighbors):
                    rows = []
                    for neighbor in neighbors[:3]:
                        if not agent.s.has_node(neighbor):
                            continue
                        neighbor_node = agent.s.node(neighbor)
                        neighbor_attrs = neighbor_node.get("attrs", {})
                        rows.append({
                            "id": int(neighbor.value),
                            "type": str(neighbor_node.get("type") or "unknown"),
                            "attribute_keys": sorted(
                                str(key) for key in neighbor_attrs),
                            "identity_attrs": {
                                key: neighbor_attrs[key]
                                for key in ("text", "name", "unknown_kind",
                                            "kind", "tick")
                                if key in neighbor_attrs
                            },
                        })
                    return rows

                samples.append({
                    "id": int(node_id.value),
                    "attribute_keys": sorted(str(key) for key in attrs),
                    "identity_attrs": {
                        key: attrs[key]
                        for key in ("text", "name", "unknown_kind",
                                    "kind", "tick")
                        if key in attrs
                    },
                    # Keep a bounded, read-only provenance window around each
                    # sample. Aggregate edge counts alone cannot distinguish
                    # a graph-owned retained value from an orphan eligible for
                    # collection, and are not sufficient grounds for pruning.
                    "incoming_neighbors": neighbor_samples(in_neighbors),
                    "outgoing_neighbors": neighbor_samples(out_neighbors),
                })
        details[node_type] = {
            "count": len(node_ids),
            "attribute_key_counts": dict(sorted(attr_keys.items())),
            "outgoing_edge_count": outgoing_links,
            "incoming_edge_count": incoming_links,
            "outgoing_edge_target_types": dict(sorted(outgoing_types.items())),
            "incoming_edge_source_types": dict(sorted(incoming_types.items())),
            "isolated_node_count": isolated,
            "sample_nodes": samples,
        }
    return details


def measure_daemon_ingress_envelope(
    corpus: Mapping[str, Any] | None = None,
    event_ids: Sequence[str] | None = None,
    *,
    content_keys: Sequence[str] = (),
    complete_host_actions: bool = False,
    shadow_read: bool = False,
    graph_type_census: bool = False,
    offline_retrieval_miss: bool = False,
    drain_timeout_s: float = 30.0,
) -> dict[str, Any]:
    """Replay signal-only corpus events through daemon ingress and native ticks.

    Corpus literal-form, force, goal, and evidence labels are never supplied
    to runtime cognition. Typed transport context (event mode and interaction
    relation) is preserved as communication-adapter evidence, per the Phase 6R
    contract. ``setup.held_answers`` remains an explicit graph-state fixture.
    By default the host-action executor is not run. When
    ``complete_host_actions`` is enabled, host actions are run after ingress
    and asynchronous retrieval is drained up to ``drain_timeout_s``.
    """
    corpus = load_corpus() if corpus is None else corpus
    if event_ids is None:
        events = list(corpus["events"])
    else:
        by_id = {str(event["id"]): event for event in corpus["events"]}
        missing = [str(value) for value in event_ids if str(value) not in by_id]
        if missing:
            raise ValueError(f"unknown Phase 0 event IDs: {missing}")
        events = [by_id[str(value)] for value in event_ids]
    if not events:
        raise ValueError("daemon ingress profile requires at least one event")
    if offline_retrieval_miss and not complete_host_actions:
        raise ValueError(
            "offline_retrieval_miss requires complete_host_actions=True")

    from scripts import jabberwock_daemon as daemon

    topic_grounding_module = None
    original_http_get = None
    original_retrieval_callbacks = {}
    topic_grounding_http_request_count = 0
    if complete_host_actions:
        from domains import topic_grounding as topic_grounding_module
        original_http_get = topic_grounding_module._http_get
        if offline_retrieval_miss:
            # Reproducible no-hit completion profile: exercise native host-
            # action lifecycle and final repair/error handling without any
            # external provider or network result becoming semantic evidence.
            for name in (
                    "ground_local_attempt", "retrieve_ground_payload",
                    "retrieve_search_candidate_payloads", "detail_local_chunks",
                    "retrieve_detail_payload"):
                original_retrieval_callbacks[name] = getattr(
                    topic_grounding_module, name)
            topic_grounding_module.ground_local_attempt = (
                lambda *_args, **_kwargs: {"settled": False, "answer": None})
            topic_grounding_module.retrieve_ground_payload = (
                lambda *_args, **_kwargs: {"attempts": []})
            topic_grounding_module.retrieve_search_candidate_payloads = (
                lambda *_args, **_kwargs: [])
            topic_grounding_module.detail_local_chunks = (
                lambda *_args, **_kwargs: [])
            topic_grounding_module.retrieve_detail_payload = (
                lambda *_args, **_kwargs: [])

        def _counted_http_get(url: str, timeout: int):
            nonlocal topic_grounding_http_request_count
            topic_grounding_http_request_count += 1
            return original_http_get(url, timeout)

        topic_grounding_module._http_get = _counted_http_get

    rss_before = _rss_bytes()
    boot_started = time.perf_counter_ns()
    agent = WorldAdapter(seeds=())
    selection = load_conversation_seed_profile(
        agent, content_keys=content_keys)
    # Match the daemon's post-boot switches. These are disabled for historical
    # signal-only measurements unless the caller explicitly requests the
    # production shadow/deep-ingest path.
    agent.shadow_read = bool(shadow_read)
    agent.deep_ingest = bool(shadow_read)
    scheduler_rules_added = daemon._ensure_supervisory_scheduler(agent)
    state = daemon.DaemonState(agent, "phase7-daemon-ingress-profile")
    boot_elapsed_ms = (time.perf_counter_ns() - boot_started) / 1_000_000.0
    rss_after_boot = _rss_bytes()
    graph_before = _graph_counts(agent)
    graph_type_counts_before = (
        _graph_node_type_counts(agent) if graph_type_census else None)
    all_inbounds: list[tuple[Mapping[str, Any], Any]] = []
    errors: list[str] = []
    samples: list[dict[str, Any]] = []
    turn_event_ids: dict[int, str] = {}
    turn_started: dict[int, float] = {}
    turn_completion_ms: dict[str, float] = {}
    turn_completion_status: dict[str, str] = {}
    content_prepass_by_event: dict[str, dict[str, Any] | None] = {}
    host_action_dispatch_count = 0
    host_action_io_started = False
    rss_peak_during_drain = rss_after_boot
    drain_timed_out = False

    try:
        for event in events:
            event_started = time.perf_counter_ns()
            rss_before_event = _rss_bytes()
            graph_before_event = _graph_counts(agent)
            modules_before = set(sys.modules)
            try:
                for held in (event.get("setup") or {}).get("held_answers") or ():
                    agent._persist_held_answer(
                        str(held["topic"]), str(held["answer"]))

                signal = str(event["signal"])
                content_prepass_by_event[str(event["id"])] = (
                    prepass_conversation_turn(agent, signal))
                ingress_started = time.perf_counter_ns()
                inbound = agent.ingest_turn(
                    signal, speech_act=agent.classify_speech_act(signal),
                    context=_runtime_context(event))
                ingress_elapsed_ms = (
                    time.perf_counter_ns() - ingress_started) / 1_000_000.0
                all_inbounds.append((event, inbound))
                state.pending_turns[int(inbound.value)] = signal
                turn_event_ids[int(inbound.value)] = str(event["id"])
                turn_started[int(inbound.value)] = time.perf_counter()

                budget, quantum = daemon._async_cycle_budget(agent)
                native_started = time.perf_counter_ns()
                if quantum is None:
                    rewrite_steps = agent.tick()
                else:
                    rewrite_steps = agent.tick(max_steps=quantum)
                    daemon._record_async_cycle_consumption(
                        agent, budget, quantum, rewrite_steps)
                if state.pending_turns:
                    agent.comprehend()
                    rewrite_steps += agent.settle_post_comprehension_authority(
                        list(state.pending_turns))
                    for turn_id in list(state.pending_turns):
                        reply = agent.release_graph_selected_response(turn_id)
                        if reply is not None:
                            terminal_status = "reply_released"
                        else:
                            terminal_status = agent.graph_turn_reply_outcome(
                                turn_id)
                            if terminal_status in {
                                    "expected", "unrepresented", "reply_ready"}:
                                continue
                            if terminal_status == "explicit_error":
                                terminal_status = "error"
                            elif terminal_status == "not_expected":
                                terminal_status = "no_response_expected"
                        event_id = turn_event_ids[turn_id]
                        state.pending_turns.pop(turn_id, None)
                        turn_completion_ms[event_id] = (
                            time.perf_counter() - turn_started[turn_id]
                        ) * 1000.0
                        turn_completion_status[event_id] = terminal_status
                if complete_host_actions:
                    with daemon.AGENT_LOCK:
                        host_action_dispatch_count += \
                            daemon._execute_host_action_requests(state)
                    host_action_io_started |= bool(state.pending_search_host_actions)
                native_elapsed_ms = (
                    time.perf_counter_ns() - native_started) / 1_000_000.0
                modules_after = set(sys.modules)
                rss_after_event = _rss_bytes()
                graph_after_event = _graph_counts(agent)
                samples.append({
                    "id": str(event["id"]),
                    "ingress_elapsed_ms": ingress_elapsed_ms,
                    "native_cycle_elapsed_ms": native_elapsed_ms,
                    "native_rewrite_steps": int(rewrite_steps),
                    "reply_ready": (
                        agent.release_graph_selected_response(inbound) is not None),
                    "rss_bytes": rss_after_event,
                    "rss_delta_bytes": max(0, rss_after_event - rss_before_event),
                    "graph": graph_after_event,
                    "graph_delta": {
                        key: graph_after_event[key] - graph_before_event[key]
                        for key in graph_before_event
                    },
                    "new_modules": sorted(modules_after - modules_before),
                    "event_elapsed_ms": (
                        time.perf_counter_ns() - event_started) / 1_000_000.0,
                })
            except Exception as exc:  # retain failures as measured outcomes
                errors.append(f"{event['id']}: {type(exc).__name__}: {exc}")

        drain_started = time.perf_counter()
        drain_deadline = time.monotonic() + max(0.0, float(drain_timeout_s))
        if complete_host_actions:
            stable_signature = None
            stable_passes = 0
            while time.monotonic() < drain_deadline:
                try:
                    with daemon.AGENT_LOCK:
                        budget, quantum = daemon._async_cycle_budget(agent)
                        if quantum is None:
                            agent.tick()
                        else:
                            steps = agent.tick(max_steps=quantum)
                            daemon._record_async_cycle_consumption(
                                agent, budget, quantum, steps)
                        if state.pending_turns:
                            agent.comprehend()
                            for turn_id in list(state.pending_turns):
                                mid = turn_id
                                reply = agent.release_graph_selected_response(mid)
                                if reply is not None:
                                    terminal_status = "reply_released"
                                else:
                                    terminal_status = agent.graph_turn_reply_outcome(
                                        mid)
                                    if terminal_status in {
                                            "expected", "unrepresented",
                                            "reply_ready"}:
                                        continue
                                    if terminal_status == "explicit_error":
                                        terminal_status = "error"
                                    elif terminal_status == "not_expected":
                                        terminal_status = "no_response_expected"
                                state.pending_turns.pop(turn_id, None)
                                event_id = turn_event_ids[turn_id]
                                turn_completion_ms[event_id] = (
                                    time.perf_counter() - turn_started[turn_id]
                                ) * 1000.0
                                turn_completion_status[event_id] = terminal_status
                        host_action_dispatch_count += \
                            daemon._execute_host_action_requests(state)
                        host_action_io_started |= bool(
                            state.pending_search_host_actions)
                    rss_peak_during_drain = max(rss_peak_during_drain, _rss_bytes())
                except Exception as exc:  # expose daemon drain failures in report
                    errors.append(f"daemon_drain: {type(exc).__name__}: {exc}")
                    break

                host_states = tuple(sorted(
                    (int(node.value), agent.s.node(node)["attrs"].get("status"))
                    for node in agent.s.nodes("HostActionRequest")
                    if agent.s.has_node(node)
                    and agent.s.node(node)["attrs"].get("status") in
                    ("requested", "running", "io_pending")
                ))
                signature = (
                    tuple(sorted(state.pending_turns)), host_states,
                    tuple(sorted(state.pending_search_host_actions)),
                )
                if signature == stable_signature and not state.pending_search_host_actions:
                    stable_passes += 1
                    if stable_passes >= 8:
                        break
                else:
                    stable_signature = signature
                    stable_passes = 0

                futures = [
                    job["future"]
                    for pending in state.pending_search_host_actions.values()
                    for job in pending["jobs"]
                ]
                if futures:
                    try:
                        futures[0].result(timeout=min(
                            0.05, max(0.0, drain_deadline - time.monotonic())))
                    except TimeoutError:
                        pass
                    except Exception:
                        # The owner-thread completion pass records worker errors.
                        pass
                elif time.perf_counter() - drain_started > 0:
                    time.sleep(0.002)

            drain_timed_out = bool(
                time.monotonic() >= drain_deadline
                and (state.pending_turns or state.pending_search_host_actions)
            )
            for event, inbound in all_inbounds:
                for sample in samples:
                    if sample["id"] == str(event["id"]):
                        sample["reply_ready"] = (
                            agent.graph_turn_reply(inbound) is not None)
                        sample["completion_latency_ms"] = turn_completion_ms.get(
                            str(event["id"]))
                        sample["terminal_status"] = turn_completion_status.get(
                            str(event["id"]))
                        break

        observations = [
            _stable_observation(
                agent, event, agent.graph_turn_reply(inbound) or "", inbound)
            for event, inbound in all_inbounds
        ]
        for observation in observations:
            observation["content_prepass"] = content_prepass_by_event.get(
                str(observation.get("id")))
        graph_reply_candidates = []
        for event, inbound in all_inbounds:
            expectation = agent.graph_turn_reply_expectation(inbound)
            expected_response_acts = expectation["expected_response_acts"]
            candidates = []
            for reply in agent.agent_outbound_messages():
                if inbound not in agent.responds_to(reply):
                    continue
                attrs = agent.s.node(reply)["attrs"]
                speech_acts = [
                    agent.s.node(act)["attrs"].get("name")
                    for act in agent.inner.neighbours(reply, "has_speech_act")
                    if agent.s.has_node(act)
                ]
                candidates.append({
                    "id": int(reply.value),
                    "text_present": bool(str(attrs.get("text") or "").strip()),
                    "speech_acts": speech_acts,
                    "floor": attrs.get("floor"),
                })
            graph_reply_candidates.append({
                "event_id": str(event["id"]),
                "reply_expectation": expectation["status"],
                "expected_response_acts": expected_response_acts,
                "graph_text_reply_ready": agent.graph_turn_reply(inbound) is not None,
                "messages": candidates,
            })
        graph_after = _graph_counts(agent)
        rss_after = _rss_bytes()
        rss_peak = max([rss_after_boot, rss_after, rss_peak_during_drain]
                       + [sample["rss_bytes"] for sample in samples])
        graph_type_counts_after = (
            _graph_node_type_counts(agent) if graph_type_census else None)
        graph_type_census_report = None
        if graph_type_counts_before is not None and graph_type_counts_after is not None:
            all_types = sorted(set(graph_type_counts_before) | set(graph_type_counts_after))
            graph_type_census_report = {
                "before": graph_type_counts_before,
                "after": graph_type_counts_after,
                "growth": {
                    node_type: graph_type_counts_after.get(node_type, 0)
                    - graph_type_counts_before.get(node_type, 0)
                    for node_type in all_types
                    if graph_type_counts_after.get(node_type, 0)
                    != graph_type_counts_before.get(node_type, 0)
                },
                "retention_details": _graph_node_retention_details(
                    agent, (
                        "Mention", "Message", "Intent", "Unknown",
                        "UnderstandingCheck", "Episode",
                    )),
            }
        ingress_max = max(
            (sample["ingress_elapsed_ms"] for sample in samples), default=0.0)
        native_max = max(
            (sample["native_cycle_elapsed_ms"] for sample in samples), default=0.0)
        disposition_count = sum(
            row.get("cognitive_disposition") is not None
            for row in observations)
        interpretation_count = sum(
            bool(row.get("interpretation_schema")) for row in observations)
        observation_hash = hashlib.sha256(json.dumps(
            observations, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, default=str).encode("utf-8")).hexdigest()
        pending_host_actions = []
        for node in agent.s.nodes("HostActionRequest"):
            if not agent.s.has_node(node):
                continue
            attrs = agent.s.node(node)["attrs"]
            if attrs.get("status") not in ("requested", "running", "io_pending"):
                continue
            source = attrs.get("source")
            source_type = source_status = None
            if source is not None and agent.s.has_node(source):
                source_node = agent.s.node(source)
                source_type = source_node.get("type")
                source_status = source_node.get("attrs", {}).get("status")
            pending_host_actions.append({
                "id": int(node.value), "action": attrs.get("action"),
                "status": attrs.get("status"), "source_type": source_type,
                "source_status": source_status,
            })
        host_action_type_counts: dict[str, dict[str, int]] = {}
        for node in agent.s.nodes("HostActionRequest"):
            if not agent.s.has_node(node):
                continue
            attrs = agent.s.node(node)["attrs"]
            action = str(attrs.get("action") or "unknown")
            status = str(attrs.get("status") or "unknown")
            action_counts = host_action_type_counts.setdefault(action, {})
            action_counts[status] = action_counts.get(status, 0) + 1
        receipt_outcome_counts: dict[str, int] = {}
        for node in agent.s.nodes("HostActionReceipt"):
            if not agent.s.has_node(node):
                continue
            outcome = str(agent.s.node(node)["attrs"].get("status") or "unknown")
            receipt_outcome_counts[outcome] = (
                receipt_outcome_counts.get(outcome, 0) + 1)
        search_request_lifecycle = []
        for request in agent.s.nodes("SearchRequest"):
            if not agent.s.has_node(request):
                continue
            attrs = agent.s.node(request)["attrs"]
            linked_actions = []
            for action_node in agent.s.nodes("HostActionRequest"):
                if not agent.s.has_node(action_node):
                    continue
                action_attrs = agent.s.node(action_node)["attrs"]
                if action_attrs.get("source") != request:
                    continue
                linked_actions.append({
                    "id": int(action_node.value),
                    "action": action_attrs.get("action"),
                    "status": action_attrs.get("status"),
                    "source_type": action_attrs.get("source_type"),
                    "receipt_statuses": [
                        agent.s.node(receipt)["attrs"].get("status")
                        for receipt in agent.inner.neighbours(
                            action_node, "has_receipt")
                        if agent.inner.has_node(receipt)
                    ],
                })
            search_request_lifecycle.append({
                "id": int(request.value),
                "status": attrs.get("status"),
                "query": str(attrs.get("query") or ""),
                "source": attrs.get("source"),
                "epistemic_status": attrs.get("epistemic_status"),
                "evidence_path": attrs.get("evidence_path"),
                "error": attrs.get("error"),
                "has_search_io_token": bool(attrs.get("search_io_token")),
                "linked_host_actions": linked_actions,
            })
        return {
            "schema": SCHEMA,
            "event_ids": [str(event["id"]) for event in events],
            "event_count": len(events),
            "seed_profile": "conversation+daemon_scheduler",
            "shadow_read_enabled": bool(agent.shadow_read),
            "deep_ingest_enabled": bool(agent.deep_ingest),
            "content_keys": sorted(set(content_keys)),
            "seed_selection_complete": bool(selection.get("selection_complete")),
            "selected_seed_ids": selection.get("selection", {}).get(
                "selected_seed_ids", []),
            "selection_unresolved": selection.get("selection", {}).get("unresolved"),
            "daemon_scheduler_rules_added": int(scheduler_rules_added),
            "boot_elapsed_ms": boot_elapsed_ms,
            "rss_before_bytes": rss_before,
            "rss_after_boot_bytes": rss_after_boot,
            "rss_after_bytes": rss_after,
            "rss_peak_bytes": rss_peak,
            "rss_limit_bytes": RSS_LIMIT,
            "graph_before": graph_before,
            "graph_after": graph_after,
            "graph_growth": {
                key: graph_after[key] - graph_before[key]
                for key in graph_before
            },
            "graph_type_census": graph_type_census_report,
            "ingress_latency_max_ms": ingress_max,
            "native_cycle_latency_max_ms": native_max,
            "interpretation_count": interpretation_count,
            "disposition_authority_count": disposition_count,
            "replies_ready_count": sum(row["reply_ready"] for row in samples),
            "pending_turn_count": len(state.pending_turns),
            "pending_turn_events": [
                {"event_id": turn_event_ids.get(turn_id),
                 "graph_outcome": agent.graph_turn_reply_outcome(turn_id)}
                for turn_id in sorted(state.pending_turns)
            ],
            "pending_ground_request_count": sum(
                agent.s.node(node)["attrs"].get("status") == "requested"
                for node in agent.s.nodes("GroundRequest")),
            "pending_search_request_count": sum(
                agent.s.node(node)["attrs"].get("status") == "requested"
                for node in agent.s.nodes("SearchRequest")),
            "search_request_lifecycle": search_request_lifecycle,
            "pending_host_action_count": len(pending_host_actions),
            "pending_host_actions": pending_host_actions,
            "pending_host_action_io_count": len(state.pending_search_host_actions),
            "host_action_type_counts": host_action_type_counts,
            "host_actions_completed": state.host_actions_completed,
            "host_action_dispatch_count": host_action_dispatch_count,
            "host_action_receipt_count": sum(receipt_outcome_counts.values()),
            "host_action_receipt_outcomes": receipt_outcome_counts,
            "host_action_dispatch_performed": bool(complete_host_actions),
            "retrieval_fixture": (
                "offline_miss" if offline_retrieval_miss else "runtime"),
            "retrieval_io_submitted": host_action_io_started,
            "external_io_performed": topic_grounding_http_request_count > 0,
            "topic_grounding_http_request_count": topic_grounding_http_request_count,
            "host_action_drain_timeout_s": float(drain_timeout_s),
            "host_action_drain_elapsed_ms": (
                time.perf_counter() - drain_started) * 1000.0,
            "host_action_drain_timed_out": drain_timed_out,
            "turn_completion_latency_max_ms": max(
                turn_completion_ms.values(), default=None),
            "turn_completion_count": len(turn_completion_ms),
            "turn_completion_status_counts": {
                status: sum(value == status
                            for value in turn_completion_status.values())
                for status in sorted(set(turn_completion_status.values()))
            },
            "reply_release_count": sum(
                status == "reply_released"
                for status in turn_completion_status.values()),
            "no_reply_terminal_count": sum(
                status == "no_response_expected"
                for status in turn_completion_status.values()),
            "rss_peak_during_drain_bytes": rss_peak_during_drain,
            "observations": observations,
            "graph_reply_candidates": graph_reply_candidates,
            "canonical_observation_sha256": observation_hash,
            "samples": samples,
            "errors": errors,
            "resource_assertions": {
                "seed_selection_complete": bool(selection.get("selection_complete")),
                "ingress_latency_bounded": ingress_max < INGRESS_LIMIT_MS,
                "native_cycle_latency_bounded": native_max < NATIVE_CYCLE_LIMIT_MS,
                "absolute_rss_bounded": rss_peak < RSS_LIMIT,
                "pending_host_actions_drained": (
                    not complete_host_actions
                    or (not drain_timed_out
                        and not state.pending_search_host_actions
                        and not pending_host_actions)
                ),
                "pending_turns_drained": (
                    not complete_host_actions or not state.pending_turns
                ),
            },
            "replay_determinism_verified": False,
            "surface_text_used_as_semantics": False,
        }
    finally:
        state.search_io_executor.shutdown(wait=True, cancel_futures=True)
        if topic_grounding_module is not None and original_http_get is not None:
            topic_grounding_module._http_get = original_http_get
            for name, callback in original_retrieval_callbacks.items():
                setattr(topic_grounding_module, name, callback)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure daemon ingress and optionally drain host actions.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--event-id", action="append", dest="event_ids")
    parser.add_argument("--content-key", action="append", dest="content_keys")
    parser.add_argument("--complete-host-actions", action="store_true")
    parser.add_argument(
        "--offline-retrieval-miss", action="store_true",
        help="Complete host actions with deterministic no-result providers; "
             "requires --complete-host-actions and performs no retrieval I/O")
    parser.add_argument("--shadow-read", action="store_true",
                        help="Enable the daemon's default shadow/deep-ingest path")
    parser.add_argument("--graph-type-census", action="store_true",
                        help="Add an instrumented before/after node-type census; "
                             "do not use its RSS values for resource acceptance")
    parser.add_argument("--drain-timeout-s", type=float, default=30.0)
    args = parser.parse_args(argv)
    report = measure_daemon_ingress_envelope(
        event_ids=args.event_ids,
        content_keys=args.content_keys or (),
        complete_host_actions=args.complete_host_actions,
        shadow_read=args.shadow_read,
        graph_type_census=args.graph_type_census,
        offline_retrieval_miss=args.offline_retrieval_miss,
        drain_timeout_s=args.drain_timeout_s,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "events": report["event_count"],
        "interpretations": report["interpretation_count"],
        "disposition_authority": report["disposition_authority_count"],
        "pending_turns": report["pending_turn_count"],
        "rss_peak_bytes": report["rss_peak_bytes"],
        "ingress_latency_max_ms": report["ingress_latency_max_ms"],
        "native_cycle_latency_max_ms": report["native_cycle_latency_max_ms"],
        "host_actions_completed": report["host_actions_completed"],
        "topic_grounding_http_request_count": report[
            "topic_grounding_http_request_count"],
        "turn_completion_count": report["turn_completion_count"],
        "turn_completion_latency_max_ms": report["turn_completion_latency_max_ms"],
        "host_action_drain_timed_out": report["host_action_drain_timed_out"],
        "resource_assertions": report["resource_assertions"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
