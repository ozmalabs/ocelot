#!/usr/bin/env python3
"""Probe two plain concurrent describe-scene calls on one serialized adapter."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_PLAIN_CONCURRENCY_DIAGNOSTIC_V1_PREREG_20260927.md"
LOCK = ROOT / "evaluation/substrate_capability/describe_scene_plain_concurrency_diagnostic_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/describe_scene_plain_concurrency_diagnostic_v1_20260927.json"
TRACE_RUNNER = ROOT / "scripts/substrate_live_describe_scene_access_trace_v2_2.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_lock() -> dict:
    spec = importlib.util.spec_from_file_location("scene_trace_v2_2", TRACE_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return {"protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
            "trace_runtime_inputs": module.lock_inputs()}


def stage(adapter, inbound, reply) -> dict:
    attrs = dict(adapter.s.node(inbound)["attrs"])
    iid = attrs.get("communication_interpretation_id")
    interpretation = dict(adapter.s.node(iid)["attrs"]) if iid is not None and adapter.s.has_node(iid) else {}
    goals = []
    for goal in adapter.s.nodes("Goal"):
        if inbound in adapter.inner.neighbours(goal, "comprehends"):
            ga = dict(adapter.s.node(goal)["attrs"])
            goals.append({k: ga.get(k) for k in ("kind", "status", "lifecycle_status", "outcome")})
    events = []
    state = attrs.get("discourse_state_id")
    if state is not None and adapter.s.has_node(state):
        for event in adapter.inner.neighbours(state, "has_event"):
            ea = dict(adapter.s.node(event)["attrs"])
            goal_ids = [g for g in adapter.inner.neighbours(event, "for_goal")
                        if inbound in adapter.inner.neighbours(g, "comprehends")]
            events.append({"kind": ea.get("kind"), "bound_to_request_goal": bool(goal_ids)})
    outbound = []
    for message in adapter.s.nodes("Message"):
        ma = dict(adapter.s.node(message)["attrs"])
        if ma.get("from") in ("agent", "adapter") and inbound in adapter.inner.neighbours(message, "responds_to"):
            outbound.append({"from": ma.get("from"), "text": ma.get("text"),
                             "suppressed": bool(ma.get("turn_reply_suppressed"))})
    return {
        "inbound_message_attrs": {k: attrs.get(k) for k in (
            "text", "sak_kind", "comp_kind", "comp_predicate", "comp_content",
            "comp_dispatch_path", "communication_route", "turn_reply_surface", "turn_reply_source") if k in attrs},
        "interpretation": {k: interpretation.get(k) for k in (
            "kind", "dispatch_path", "communicative_force", "cognitive_disposition", "arbitration_basis") if k in interpretation},
        "goal_count": len(goals), "goals": goals,
        "discourse_event_kinds": [e["kind"] for e in events], "events": events,
        "reply": str(reply), "outbound_messages": outbound,
        "public_reply_matches_outbound": any(not x["suppressed"] and str(x["text"] or "").strip() == str(reply or "").strip() for x in outbound),
    }


def run() -> dict:
    started = input_lock()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene

    adapter = WorldAdapter(seeds=())
    boot0 = time.perf_counter_ns(); load_all_seeds(adapter); boot_ns = time.perf_counter_ns() - boot0
    attach_scene(adapter, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False},
    ])
    barrier = threading.Barrier(3)
    outputs, errors, timings = {}, {}, {}
    def call(label):
        barrier.wait()
        t0 = time.perf_counter_ns()
        try:
            outputs[label] = adapter.converse("describe what you see", speech_act="instruction", speaker="alice")
        except BaseException as exc:
            errors[label] = {"type": type(exc).__name__, "message": str(exc)}
        timings[label] = time.perf_counter_ns() - t0

    threads = [threading.Thread(target=call, args=(label,), name=f"plain-{label}") for label in ("A", "B")]
    for thread in threads: thread.start()
    barrier.wait()
    for thread in threads: thread.join(120)
    joined = all(not thread.is_alive() for thread in threads)
    inbound_nodes = [node for node in adapter.s.nodes("Message")
                     if adapter.s.node(node)["attrs"].get("from") == "interlocutor"
                     and adapter.s.node(node)["attrs"].get("text") == "describe what you see"]
    inbound_nodes.sort(key=lambda node: node_id(node))
    requests = [stage(adapter, node, adapter.s.node(node)["attrs"].get("turn_reply_surface"))
                for node in inbound_nodes]
    finished = input_lock()
    return {
        "schema_version": 1,
        "run_id": "describe-scene-plain-concurrency-diagnostic-v1-20260927",
        "locked_inputs": started, "post_run_inputs": finished,
        "source_stable": started == finished,
        "child_threads_joined": joined, "thread_errors": errors,
        "fixture": {"text": "describe what you see", "speech_act": "instruction", "shared_scene_percepts": 3},
        "worker_replies": {k: str(v) for k, v in outputs.items()},
        "requests_recovered_in_message_order": requests,
        "boot_ns": boot_ns, "thread_turn_ns": timings,
        "matched_inbound_count": len(inbound_nodes),
        "environment": {"python": sys.version, "platform": platform.platform()},
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": input_lock()}, indent=2, sort_keys=True)); return
    inputs = input_lock()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != inputs:
        raise SystemExit("missing or stale plain-concurrency source lock")
    report = run(); OUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "source_stable": report["source_stable"],
                      "threads_joined": report["child_threads_joined"], "errors": report["thread_errors"],
                      "replies": report["worker_replies"], "request_goals": [r["goal_count"] for r in report["requests_recovered_in_message_order"]]}, indent=2))
    if not report["source_stable"] or not report["child_threads_joined"] or report["matched_inbound_count"] != 2:
        raise SystemExit("plain-concurrency diagnostic integrity gate failed")


def node_id(node):
    return int(node.value if hasattr(node, "value") else node)


if __name__ == "__main__":
    main()
