#!/usr/bin/env python3
"""Source-locked one-turn stage diagnostic for the live describe-scene path."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DESCRIBE_SCENE_CURRENT_PATH_DIAGNOSTIC_V1_PREREG_20260927.md"
LOCK = ROOT / "evaluation/substrate_capability/describe_scene_current_path_diagnostic_v1_lock_20260927.json"
OUT = ROOT / "evaluation/reports/describe_scene_current_path_diagnostic_v1_20260927.json"
TRACE_RUNNER = ROOT / "scripts/substrate_live_describe_scene_access_trace_v2_2.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_lock() -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location("scene_trace_v2_2", TRACE_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "trace_runtime_inputs": module.lock_inputs(),
    }


def nid(node) -> int:
    return int(node.value if hasattr(node, "value") else node)


def node_projection(adapter, node) -> dict:
    if node is None or not adapter.s.has_node(node):
        return {}
    return {"id": nid(node), "type": adapter.s.node(node)["type"],
            "attrs": dict(adapter.s.node(node)["attrs"])}


def run() -> dict:
    started = input_lock()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene

    adapter = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns()
    load_all_seeds(adapter)
    boot_ns = time.perf_counter_ns() - boot_start
    scene = attach_scene(adapter, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False},
    ])
    turn_start = time.perf_counter_ns()
    reply = adapter.converse("describe what you see", speech_act="instruction", speaker="alice")
    turn_ns = time.perf_counter_ns() - turn_start

    message = getattr(adapter, "_last_turn_inbound", None)
    attrs = dict(adapter.s.node(message)["attrs"]) if message is not None else {}
    interpretation_id = attrs.get("communication_interpretation_id")
    interpretation = (node_projection(adapter, interpretation_id)
                      if interpretation_id is not None else {})
    goals = []
    if message is not None:
        for goal in adapter.s.nodes("Goal"):
            if message in adapter.inner.neighbours(goal, "comprehends"):
                goals.append(node_projection(adapter, goal))
    state_id = attrs.get("discourse_state_id")
    events = []
    if state_id is not None and adapter.s.has_node(state_id):
        for event in adapter.inner.neighbours(state_id, "has_event"):
            row = node_projection(adapter, event)
            row["for_goal_ids"] = [nid(g) for g in adapter.inner.neighbours(event, "for_goal")]
            events.append(row)
    outbound = []
    if message is not None:
        for candidate in adapter.outbound_messages():
            if message in adapter.responds_to(candidate):
                outbound.append(node_projection(adapter, candidate))
    finished = input_lock()

    selected_message_attrs = {
        key: attrs.get(key) for key in (
            "text", "speech_act", "sak_input_kind", "sak_kind", "comp_kind",
            "comp_predicate", "comp_content", "comp_topic", "comp_dispatch_path",
            "comp_dispatch_meta", "comp_intent", "comp_anaphor", "communication_route",
            "communication_repair_route", "reply_from", "turn_reply_surface",
            "turn_reply_source", "instruction_outcome", "discourse_state_id",
            "communication_interpretation_id",
        ) if key in attrs
    }
    semantic_payload = {"message_attrs": selected_message_attrs,
                        "interpretation": interpretation, "goals": goals,
                        "events": events, "outbound": outbound, "reply": str(reply)}
    return {
        "schema_version": 1,
        "run_id": "describe-scene-current-path-diagnostic-v1-20260927",
        "locked_inputs": started,
        "post_run_inputs": finished,
        "source_stable": started == finished,
        "fixture": {"text": "describe what you see", "speech_act": "instruction",
                    "speaker": "alice", "scene_id": nid(scene), "percept_count": 3},
        "timing_ns": {"boot": boot_ns, "turn": turn_ns},
        "message_attrs": selected_message_attrs,
        "interpretation": interpretation,
        "goals_linked_to_message": goals,
        "discourse_events_for_state": events,
        "outbound_messages_for_turn": outbound,
        "reply": str(reply),
        "semantic_sha256": hashlib.sha256(json.dumps(
            semantic_payload, sort_keys=True, default=str,
            separators=(",", ":")).encode()).hexdigest(),
        "environment": {"python": sys.version, "platform": platform.platform()},
    }


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        print(json.dumps({"locked_inputs": input_lock()}, indent=2, sort_keys=True))
        return
    inputs = input_lock()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != inputs:
        raise SystemExit("missing or stale diagnostic source lock")
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    report = run()
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)),
                      "source_stable": report["source_stable"],
                      "reply": report["reply"],
                      "message_attrs": report["message_attrs"],
                      "goal_count": len(report["goals_linked_to_message"]),
                      "discourse_event_count": len(report["discourse_events_for_state"])}, indent=2, default=str))
    if not report["source_stable"]:
        raise SystemExit("source changed during diagnostic")


if __name__ == "__main__":
    main()
