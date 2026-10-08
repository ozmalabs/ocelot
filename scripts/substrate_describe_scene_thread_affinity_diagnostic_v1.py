#!/usr/bin/env python3
"""Compare one live describe-scene call on main and plain child threads."""
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
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_THREAD_AFFINITY_DIAGNOSTIC_V1_PREREG_20260927.md"
LOCK = ROOT / "evaluation/substrate_capability/describe_scene_thread_affinity_diagnostic_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/describe_scene_thread_affinity_diagnostic_v1_20260927.json"
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


def node_id(value) -> int:
    return int(value.value if hasattr(value, "value") else value)


def stage_snapshot(adapter, reply, turn_ns, boot_ns, error=None) -> dict:
    message = getattr(adapter, "_last_turn_inbound", None)
    attrs = dict(adapter.s.node(message)["attrs"]) if message is not None else {}
    interpretation_id = attrs.get("communication_interpretation_id")
    interpretation = (dict(adapter.s.node(interpretation_id)["attrs"])
                      if interpretation_id is not None and adapter.s.has_node(interpretation_id) else {})
    goals = []
    if message is not None:
        for goal in adapter.s.nodes("Goal"):
            if message in adapter.inner.neighbours(goal, "comprehends"):
                ga = dict(adapter.s.node(goal)["attrs"])
                goals.append({k: ga.get(k) for k in ("kind", "predicate", "status", "lifecycle_status", "outcome")})
    events = []
    state = attrs.get("discourse_state_id")
    if state is not None and adapter.s.has_node(state):
        for event in adapter.inner.neighbours(state, "has_event"):
            ea = dict(adapter.s.node(event)["attrs"])
            linked = bool(message is not None and any(
                message in adapter.inner.neighbours(goal, "comprehends")
                and goal in adapter.inner.neighbours(event, "for_goal")
                for goal in adapter.s.nodes("Goal")))
            events.append({"kind": ea.get("kind"), "goal_linked": linked})
    outbound = []
    if message is not None:
        for candidate in adapter.s.nodes("Message"):
            ca = dict(adapter.s.node(candidate)["attrs"])
            if ca.get("from") not in ("agent", "adapter"):
                continue
            if message not in adapter.inner.neighbours(candidate, "responds_to"):
                continue
            outbound.append({"from": ca.get("from"), "text": ca.get("text"),
                             "suppressed": bool(ca.get("turn_reply_suppressed"))})
    message_keys = ("sak_input_kind", "sak_kind", "comp_kind", "comp_predicate", "comp_content",
                    "comp_dispatch_path", "comp_intent", "communication_route", "instruction_outcome",
                    "turn_reply_surface", "turn_reply_source")
    return {
        "reply": str(reply), "error": error,
        "timing_ns": {"boot": boot_ns, "turn": turn_ns},
        "message_stage": {k: attrs.get(k) for k in message_keys if k in attrs},
        "interpretation_stage": {k: interpretation.get(k) for k in (
            "kind", "native_kind", "dispatch_path", "communicative_force", "cognitive_disposition",
            "cognitive_goal", "arbitration_basis", "grounding_status", "intent", "predicate", "object")
            if k in interpretation},
        "request_bound_goals": goals,
        "discourse_events": events,
        "outbound_messages": outbound,
    }


def run() -> dict:
    started = input_lock()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene

    fixture = [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False},
    ]

    def build_adapter():
        adapter = WorldAdapter(seeds=())
        start = time.perf_counter_ns(); load_all_seeds(adapter); boot_ns = time.perf_counter_ns() - start
        attach_scene(adapter, fixture)
        return adapter, boot_ns

    main_adapter, main_boot = build_adapter()
    start = time.perf_counter_ns()
    main_reply = main_adapter.converse("describe what you see", speech_act="instruction", speaker="alice")
    main_turn = time.perf_counter_ns() - start
    main = stage_snapshot(main_adapter, main_reply, main_turn, main_boot)

    thread_adapter, thread_boot = build_adapter()
    result = {}
    def child_turn():
        start = time.perf_counter_ns()
        try:
            reply = thread_adapter.converse("describe what you see", speech_act="instruction", speaker="alice")
            result["outcome"] = stage_snapshot(thread_adapter, reply, time.perf_counter_ns() - start, thread_boot)
        except BaseException as exc:
            result["error"] = {"type": type(exc).__name__, "message": str(exc)}

    child = threading.Thread(target=child_turn, name="plain-conversation-child")
    child.start(); child.join(120)
    joined = not child.is_alive()
    finished = input_lock()
    threaded = result.get("outcome", {"error": result.get("error", "child thread produced no result")})
    semantic_keys = ("reply", "message_stage", "interpretation_stage", "request_bound_goals", "discourse_events", "outbound_messages")
    parity = all(main.get(k) == threaded.get(k) for k in semantic_keys)
    return {
        "schema_version": 1,
        "run_id": "describe-scene-thread-affinity-diagnostic-v1-20260927",
        "locked_inputs": started,
        "post_run_inputs": finished,
        "source_stable": started == finished,
        "child_thread_joined": joined,
        "thread_exception": result.get("error"),
        "main_thread": main,
        "plain_child_thread": threaded,
        "semantic_parity": parity,
        "public_graph_message_parity": {
            "main": any(not m["suppressed"] and m["text"] == main["reply"] for m in main.get("outbound_messages", [])),
            "child": any(not m["suppressed"] and m["text"] == threaded.get("reply") for m in threaded.get("outbound_messages", [])),
        },
        "environment": {"python": sys.version, "platform": platform.platform()},
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": input_lock()}, indent=2, sort_keys=True)); return
    inputs = input_lock()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != inputs:
        raise SystemExit("missing or stale thread-affinity diagnostic lock")
    report = run()
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "source_stable": report["source_stable"],
                      "child_joined": report["child_thread_joined"], "semantic_parity": report["semantic_parity"],
                      "main_reply": report["main_thread"].get("reply"),
                      "child_reply": report["plain_child_thread"].get("reply")}, indent=2))
    if not report["source_stable"] or not report["child_thread_joined"]:
        raise SystemExit("thread-affinity diagnostic integrity gate failed")


if __name__ == "__main__":
    main()
