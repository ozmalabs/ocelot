#!/usr/bin/env python3
"""Scoped owner-queue prototype on an incrementally growing discourse task."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONVERSATION_SCOPED_OWNER_WAKEUP_PREREG_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/conversation_scoped_owner_wakeup_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_conversation_scoped_owner_wakeup_v1_20260926.json"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json"
SEED = ROOT / "seeds/conversation_discourse_state.json"
MATERIALIZER = ROOT / "domains/discourse_state.py"
CAP = 100_000
MAX_TURNS = 1_000
ARMS = ("full", "owner_queue", "omit_owner_wakeup")
FRAME_FOR_EVENT = {0: 0, 1: 1, 2: 1, 3: 1, 4: 2, 5: 2,
                   6: 3, 7: 3, 8: 3, 9: 3}
ORIGINS = {0: 0, 5: 2}
EXPECTED_TRANSITIONS = {0: [1, 2, 3], 2: [6, 7, 8]}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nid(x) -> int:
    return int(x.value if hasattr(x, "value") else x)


def digest(graph: dict) -> str:
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"),
                                  default=str).encode()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    native = Path(_native.__file__).resolve()
    return {
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
        "fixture_sha256": sha(FIXTURE), "seed_sha256": sha(SEED),
        "materializer_sha256": sha(MATERIALIZER),
        "native_extension_sha256": sha(native),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
        "native_extension_path": str(native),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                           text=True).strip(),
        "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"],
                                                        cwd=ROOT, text=True).strip()),
        "rust_sources_sha256": {name: sha(ROOT / "runners/dsl/src" / name)
                                for name in ("graph.rs", "rewrite.rs", "substrate.rs",
                                             "term.rs", "access_trace.rs", "py.rs")},
    }


def add_receipt_rule(inner) -> int:
    return int(inner.add_rule({
        "name": "frame_consume_resolved_goal_receipt",
        "match_type": "Goal",
        "match": [["goal", "originated_in", "origin"]],
        "where": {"type": "And", "items": [
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "goal"},
                                      "key": "lifecycle_status"},
             "b": {"type": "Lit", "value": "resolved"}},
            {"type": "Eq", "a": {"type": "Attr", "node": {"type": "Var", "name": "origin"},
                                      "key": "resolution_receipt"},
             "b": {"type": "Lit", "value": 0.0}},
        ]},
        "effects": [["set_attr", "origin", "resolution_receipt", 1.0]],
    }))


def add_work_frame(agent, frames: list, index: int):
    if frames[index] is None:
        frames[index] = agent.s.add_node("Microtheory", {
            "name": f"conversation_work_frame_{index}", "frame_kind": "fixture_phase"})
    return frames[index]


def add_owned(agent, frame, node) -> None:
    agent.inner.add_edge_unchecked(frame, "has_concept", node)


def append_event(agent, state, user, row: dict, frames: list,
                 event_to_frame: dict, goals: dict, goal_frames: dict) -> int:
    from domains.discourse_state import close_expectation, open_goal, record_event
    index, kind = int(row["index"]), row["kind"]
    frame_idx = FRAME_FOR_EVENT[index]
    frame = add_work_frame(agent, frames, frame_idx)
    topic = "calendar" if index < 5 else "location"
    if kind in {"request", "question"}:
        expectation = row.get("expectation") or ("action" if kind == "request" else "answer")
        payload = {"common_ground_delta": "calendar_request"} if index == 0 else None
        event = record_event(agent, state, kind=kind, speaker=user, addressee=agent.agent,
                             topic=topic, expectation=expectation, payload=payload)
        agent.inner.set_attr(event, "resolution_receipt", 0.0)
        goal = open_goal(agent, state, kind="act_or_clarify", origin_event=event,
                         addressee=user)
        add_owned(agent, frame, goal)
        goals[index] = goal
        goal_frames[index] = frame_idx
    elif kind in {"selection", "execution"}:
        event = record_event(agent, state, kind=kind, speaker=agent.agent, addressee=user)
    elif kind == "action_result":
        claim = "calendar_checked" if index == 3 else "location_shared"
        event = record_event(agent, state, kind=kind, speaker=agent.agent, addressee=user,
                             payload={"common_ground_delta": claim})
    elif kind == "assertion":
        event = record_event(agent, state, kind=kind, speaker=user, addressee=agent.agent,
                             topic=topic, payload={"common_ground_delta": "calendar_shared"})
    elif kind == "epistemic_limit":
        event = record_event(agent, state, kind=kind, speaker=agent.agent, addressee=user,
                             topic=topic)
        close_expectation(agent, state, event=event, disposition="deferred",
                          residual="location_unresolved")
    else:
        raise RuntimeError(f"unknown task event {kind}")
    add_owned(agent, frame, event)
    event_id = nid(event)
    event_to_frame[event_id] = frame_idx
    return event_id


def call_full(inner) -> dict:
    inner.scale_audit_reset(); inner.scale_audit_set_enabled(True)
    wall, cpu = time.perf_counter_ns(), time.process_time_ns()
    report = dict(inner.run_rules_report(CAP, False))
    wall_ns, cpu_ns = time.perf_counter_ns() - wall, time.process_time_ns() - cpu
    counters = {str(k): int(v) for k, v in dict(inner.scale_audit_snapshot()).items()}
    inner.scale_audit_set_enabled(False)
    return {"report": report, "wall_ns": wall_ns, "cpu_ns": cpu_ns,
            "counters": counters, "calls": 1}


def call_scoped(inner, mt, frame_to_index: dict, mt_by_frame: dict, *, enqueue_owners: bool) -> dict:
    queue = deque([frame_to_index[nid(mt)]])
    queued = set(queue)
    turns = 0
    progress = 0
    notified = []
    call_reports = []
    counters_total: dict[str, int] = {}
    wall_start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
    while queue and turns < MAX_TURNS and progress < CAP:
        frame = queue.popleft(); queued.remove(frame)
        inner.scale_audit_reset(); inner.scale_audit_set_enabled(True)
        report = dict(inner.run_rules_scoped_delta_report(
            mt_by_frame[frame], CAP - progress, False))
        counters = {str(k): int(v) for k, v in dict(inner.scale_audit_snapshot()).items()}
        inner.scale_audit_set_enabled(False)
        for key, value in counters.items():
            counters_total[key] = counters_total.get(key, 0) + value
        turns += 1
        progress += int(report.get("progress_steps", 0))
        if report.get("hit_progress_budget") or report.get("deferred_effects_pending"):
            return {"complete": False, "turns": turns, "progress_steps": progress,
                    "wall_ns": time.perf_counter_ns() - wall_start,
                    "cpu_ns": time.process_time_ns() - cpu_start,
                    "counters": counters_total, "notifications": notified,
                    "reports": call_reports + [report], "failure": "budget_or_deferred"}
        mapped = []
        if enqueue_owners:
            for owner in report.get("affected_microtheories", []):
                owner = nid(owner)
                if owner not in frame_to_index:
                    return {"complete": False, "turns": turns, "progress_steps": progress,
                            "wall_ns": time.perf_counter_ns() - wall_start,
                            "cpu_ns": time.process_time_ns() - cpu_start,
                            "counters": counters_total, "notifications": notified,
                            "reports": call_reports + [report],
                            "failure": f"unmapped owner {owner}"}
                target = frame_to_index[owner]
                if target != frame:
                    mapped.append(target)
                    if target not in queued:
                        queue.append(target); queued.add(target)
        notified.append({"source_frame": frame, "native_owners": sorted(set(mapped)),
                         "affected_microtheories": [nid(x) for x in report.get("affected_microtheories", [])],
                         "affected_nodes": [int(x) for x in report.get("affected_nodes", [])],
                         "affected_edges": report.get("affected_edges", [])})
        call_reports.append(report)
    return {"complete": not queue and turns < MAX_TURNS and progress < CAP,
            "turns": turns, "progress_steps": progress,
            "wall_ns": time.perf_counter_ns() - wall_start,
            "cpu_ns": time.process_time_ns() - cpu_start,
            "counters": counters_total, "notifications": notified,
            "reports": call_reports,
            "failure": None if not queue else "turn_or_progress_cap"}


def run_arm(arm: str, fixture: dict) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_core import load_seeds_into
    from domains.discourse_state import ensure_common_ground, ensure_discourse_state
    agent = WorldAdapter(seeds=())
    load_seeds_into(agent.s, agent.agent, ["conversation_discourse_state"])
    sentinel_rule_index = add_receipt_rule(agent.inner)
    people = agent.attach_chat_world("user")
    user = people["interlocutor"]
    state = ensure_discourse_state(agent, conversation_id="owner_wakeup_census", addressee=user)
    ensure_common_ground(agent, state, addressee=user)
    frames = [None] * 4
    frame_setup_start = time.perf_counter_ns()
    for i in range(4):
        add_work_frame(agent, frames, i)
    frame_setup_ns = time.perf_counter_ns() - frame_setup_start
    mt_by_frame = {i: frames[i] for i in range(4)}
    frame_to_index = {nid(mt): i for i, mt in mt_by_frame.items()}
    event_to_frame: dict[int, int] = {}
    event_ids: dict[int, int] = {}
    event_objects: dict[int, object] = {}
    goals = {}
    goal_frames = {}
    checkpoints = []
    for index, row in enumerate(fixture["events"]):
        event_id = append_event(agent, state, user, row, frames,
                                event_to_frame, goals, goal_frames)
        current_frame = FRAME_FOR_EVENT[index]
        event_ids[index] = event_id
        event_objects[index] = next(n for n in agent.s.nodes("DiscourseEvent") if nid(n) == event_id)
        if arm == "full":
            settle = call_full(agent.inner)
            complete = settle["report"].get("status") == "fixed_point"
        else:
            settle = call_scoped(agent.inner, mt_by_frame[current_frame], frame_to_index, mt_by_frame,
                                 enqueue_owners=(arm == "owner_queue"))
            complete = bool(settle["complete"])
        graph = agent.inner.graph_to_dict()
        receipt_by_origin = {origin_index: float(agent.s.node(goal)["attrs"].get(
            "lifecycle_status") == "resolved") for origin_index, goal in goals.items()}
        origin_receipts = {}
        for origin_index in ORIGINS:
            if origin_index in event_objects:
                event = event_objects[origin_index]
                origin_receipts[origin_index] = float(agent.s.node(event)["attrs"].get("resolution_receipt", 0.0))
        checkpoints.append({
            "event_index": index, "event_id": event_id, "event_frame": current_frame,
            "complete": complete, "settlement": settle,
            "graph_digest": digest(graph), "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "goal_lifecycle_resolved": receipt_by_origin,
            "origin_resolution_receipts": origin_receipts,
        })
    before_recovery_graph = agent.inner.graph_to_dict()
    recovery = None
    if arm == "omit_owner_wakeup":
        recovery = call_full(agent.inner)
    final_graph = agent.inner.graph_to_dict()
    final_goals = {origin: {
        "node": nid(goal), "frame": goal_frames[origin],
        "lifecycle_status": agent.s.node(goal)["attrs"].get("lifecycle_status"),
        "transition_event_indices": sorted(int(agent.s.node(e)["attrs"]["event_index"])
                                            for e in agent.inner.neighbours(goal, "transitioned_by")),
    } for origin, goal in goals.items()}
    origins = {origin: event_objects[origin] for origin in ORIGINS}
    receipt_status = {origin: float(agent.s.node(event)["attrs"].get("resolution_receipt", 0.0))
                      for origin, event in origins.items()}
    common_grounds = [agent.s.node(n)["attrs"] for n in agent.s.nodes("CommonGround")]
    access_sets = []
    for index, name, active, reads, term_edges, writes, reads_any, writes_any in agent.inner.rule_access_sets():
        access_sets.append({"index": int(index), "name": name, "active": bool(active),
                            "reads": sorted(set(reads) | set(term_edges)),
                            "writes": sorted(writes), "reads_any": bool(reads_any),
                            "writes_any": bool(writes_any)})
    return {
        "arm": arm, "pid": os.getpid(), "frame_setup_ns": frame_setup_ns,
        "frame_nodes": [[i, nid(mt)] for i, mt in mt_by_frame.items()],
        "event_to_frame": [[node, frame] for node, frame in sorted(event_to_frame.items())],
        "checkpoints": checkpoints,
        "pre_recovery_graph_digest": digest(before_recovery_graph),
        "final_graph_digest": digest(final_graph), "final_graph": final_graph,
        "final_goals": final_goals, "final_origin_receipts": receipt_status,
        "final_common_grounds": common_grounds, "recovery": recovery,
        "sentinel_rule_index": sentinel_rule_index,
        "static_rule_access": access_sets,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps({"locked_inputs": lock_inputs()}, indent=2, sort_keys=True))
        return
    current = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != current:
        raise SystemExit("missing or stale lock")
    fixture = json.loads(FIXTURE.read_text())
    if len(sys.argv) == 2 and sys.argv[1].startswith("--worker="):
        arm = sys.argv[1].split("=", 1)[1]
        print(json.dumps(run_arm(arm, fixture), sort_keys=True, default=str))
        return
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    for arm in ARMS:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), f"--worker={arm}"],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    full, owner, omit = runs
    expected_state = full["checkpoints"]
    owner_equal = [a["graph_digest"] == b["graph_digest"]
                   for a, b in zip(expected_state, owner["checkpoints"])]
    omit_equal = [a["graph_digest"] == b["graph_digest"]
                  for a, b in zip(expected_state, omit["checkpoints"])]
    remote_notifications = []
    for cp in owner["checkpoints"]:
        for item in cp["settlement"].get("notifications", []):
            if item["source_frame"] != cp["event_frame"]:
                continue
            for target in item["native_owners"]:
                if target != item["source_frame"]:
                    remote_notifications.append({"event_index": cp["event_index"], **item,
                                                 "target_frame": target})
    omission_divergences = [i for i, equal in enumerate(omit_equal) if not equal]
    expected_receipts = {0: 1.0, 5: 1.0}
    checks = {
        "three_fresh_processes": len({r["pid"] for r in runs}) == 3,
        "full_task_oracle_and_fixed_points": all(cp["complete"] for cp in full["checkpoints"]),
        "owner_queue_complete_each_checkpoint": all(cp["complete"] for cp in owner["checkpoints"]),
        "owner_queue_exact_full_graph_each_checkpoint": all(owner_equal),
        "owner_queue_reaches_remote_origin_frames": any(
            n["target_frame"] == 0 and n["event_index"] in {1, 2, 3}
            for n in remote_notifications) and any(
            n["target_frame"] == 2 and n["event_index"] in {6, 7, 8}
            for n in remote_notifications),
        "task_goal_provenance_matches_full_oracle": owner["final_goals"] == full["final_goals"],
        "task_receipts_and_common_ground_match_full": owner["final_origin_receipts"] == {
            str(k): v for k, v in expected_receipts.items()}
            and owner["final_origin_receipts"] == full["final_origin_receipts"]
            and owner["final_common_grounds"] == full["final_common_grounds"],
        "omitted_owner_wakeup_becomes_stale": bool(omission_divergences)
            and any(omit["checkpoints"][i]["origin_resolution_receipts"] !=
                    full["checkpoints"][i]["origin_resolution_receipts"] for i in omission_divergences),
        "full_recovery_restores_exact_graph": omit["recovery"] is not None
            and omit["final_graph_digest"] == full["final_graph_digest"],
        "all_reports_have_no_deferred_effects_or_budget_exit": all(
            not report.get("deferred_effects_pending", False)
            and not report.get("hit_progress_budget", False)
            for run in [owner, omit] for cp in run["checkpoints"]
            for report in cp["settlement"].get("reports", [])),
        "native_notification_owner_ids_map_to_frames": all(
            not item.get("failure") for cp in owner["checkpoints"]
            for item in [cp["settlement"]]),
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-conversation-scoped-owner-wakeup-v1-20260926",
        "claim_boundary": (
            "Fresh diagnostic of the native Microtheory-scoped delta API on one authored ten-event task, "
            "with four caller-constructed event-phase frames and one downstream receipt sentinel rule. "
            "Owner queue matches full closure; caller-side frame construction/queue is not an engine scheduler. "
            "Omission/recovery results are bounded to this fixture."
        ),
        "locked_inputs": current, "lock_sha256": sha(LOCK),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "OZMA_NO_LLM": env["OZMA_NO_LLM"],
                        "OZMA_SEED_PERSIST_DISABLED": env["OZMA_SEED_PERSIST_DISABLED"]},
        "provenance": {"commit": current["commit"], "dirty_worktree": current["dirty_worktree"],
                       "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_conversation_scoped_owner_wakeup_v1.py",
                       "native_extension_sha256": current["native_extension_sha256"],
                       "native_build_manifest_sha256": current["native_build_manifest_sha256"],
                       "cargo_lock_sha256": current["cargo_lock_sha256"]},
        "checks": checks,
        "summary": {"worker_count": len(runs), "owner_queue_equal_checkpoints": sum(owner_equal),
                    "checkpoint_count": len(full["checkpoints"]),
                    "omitted_arm_equal_checkpoints": sum(omit_equal),
                    "omission_divergence_event_indices": omission_divergences,
                    "remote_owner_notifications": remote_notifications,
                    "frame_setup_ns": {r["arm"]: r["frame_setup_ns"] for r in runs},
                    "settlement_wall_ns": {r["arm"]: [cp["settlement"].get("wall_ns",
                        cp["settlement"].get("wall_ns")) for cp in r["checkpoints"]] for r in runs},
                    "peak_rss_kib": {r["arm"]: r["peak_rss_kib"] for r in runs}},
        "runs": runs,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": payload["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("scoped owner wakeup probe failed a registered gate; raw report preserved")


if __name__ == "__main__":
    main()
