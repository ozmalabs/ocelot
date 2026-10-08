#!/usr/bin/env python3
"""Fresh-process graph/access census for the connected ten-event discourse task."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from itertools import combinations, permutations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DISCOURSE_CONNECTED_TASK_CENSUS_V2_1_AMENDMENT_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/discourse_connected_task_census_v2_1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v2_1_20260926.json"
ANALYZER = ROOT / "scripts/analyze_substrate_discourse_connected_task_census_v2_1.py"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json"
RULE_SEED = ROOT / "seeds/conversation_discourse_state.json"
MATERIALIZER = ROOT / "domains/discourse_state.py"
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nid(x) -> int:
    return int(x.value if hasattr(x, "value") else x)


def graph_digest(graph: dict) -> str:
    packed = json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(packed).hexdigest()


def locked_inputs() -> dict:
    from substrate_rs import _native
    native = Path(_native.__file__).resolve()
    sources = ("graph.rs", "rewrite.rs", "substrate.rs", "term.rs", "access_trace.rs", "py.rs")
    return {
        "protocol_sha256": sha(PROTOCOL), "runner_sha256": sha(Path(__file__)),
        "analyzer_sha256": sha(ANALYZER),
        "fixture_sha256": sha(FIXTURE), "rule_seed_sha256": sha(RULE_SEED),
        "materializer_sha256": sha(MATERIALIZER), "native_extension_sha256": sha(native),
        "conversation_action_sha256": sha(ROOT / "domains/conversation_action.py"),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
        "native_extension_path": str(native),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"],
                                                        cwd=ROOT, text=True).strip()),
        "rust_sources_sha256": {name: sha(ROOT / "runners/dsl/src" / name) for name in sources},
    }


def materialize_fixture(agent, fixture: dict):
    from domains.discourse_state import (
        close_expectation, ensure_common_ground, ensure_discourse_state, open_goal, record_event,
    )
    people = agent.attach_chat_world("user")
    user = people["interlocutor"]
    state = ensure_discourse_state(agent, conversation_id="connected_task_census", addressee=user)
    ensure_common_ground(agent, state, addressee=user)
    event_frame: dict[int, int] = {}
    goal_nodes = []
    active_frame = -1
    frame_count = 0
    goals_by_origin: dict[int, int] = {}
    goals_by_frame: dict[int, Any] = {}
    inbound_by_goal: dict[int, Any] = {}

    for row in fixture["events"]:
        index, kind, relation = int(row["index"]), row["kind"], row["relation"]
        if relation in {"origin", "unsolicited"}:
            active_frame = frame_count
            frame_count += 1
        if active_frame < 0:
            raise RuntimeError("first event did not start a task/event frame")
        topic = "calendar" if index < 5 else "location"
        if kind in {"request", "question"}:
            expectation = row.get("expectation") or ("action" if kind == "request" else "answer")
            payload = {"common_ground_delta": "calendar_request"} if index == 0 else None
            event = record_event(agent, state, kind=kind, speaker=user, addressee=agent.agent,
                                 topic=topic, expectation=expectation, payload=payload)
            goal = open_goal(agent, state, kind="act_or_clarify", origin_event=event,
                             addressee=user)
            goals_by_origin[nid(event)] = nid(goal)
            goals_by_frame[active_frame] = goal
            goal_nodes.append(goal)
            inbound = agent.s.add_node("Message", {})
            agent.inner.set_attr(inbound, "discourse_state_id", state)
            agent.inner.set_attr(inbound, "discourse_event_id", event)
            agent.inner.add_edge_unchecked(inbound, "sent_by", user)
            inbound_by_goal[nid(goal)] = inbound
        elif kind in {"selection", "execution"}:
            event = None
        elif kind == "action_result":
            claim = "calendar_checked" if index == 3 else "location_shared"
            event = None
        elif kind == "assertion":
            event = record_event(agent, state, kind=kind, speaker=user, addressee=agent.agent,
                                 topic=topic, payload={"common_ground_delta": "calendar_shared"})
        elif kind == "epistemic_limit":
            event = record_event(agent, state, kind=kind, speaker=agent.agent, addressee=user,
                                 topic=topic)
            close_expectation(agent, state, event=event, disposition="deferred",
                              residual="location_unresolved")
        else:
            raise RuntimeError(f"unsupported fixture event kind {kind}")
        event_id = nid(event) if event is not None else None
        if event_id is not None:
            event_frame[event_id] = active_frame
            # Associate an origin goal with the same fixture-derived frame.
            if event_id in goals_by_origin:
                event_frame[goals_by_origin[event_id]] = active_frame
        producer_counters = None
        if kind in {"selection", "execution", "action_result"}:
            from domains.conversation_action import _record_live_goal_event
            goal = goals_by_frame[active_frame]
            audit = agent.inner
            audit.scale_audit_reset()
            audit.scale_audit_per_rule_reset()
            audit.scale_audit_set_enabled(True)
            audit.scale_audit_set_per_rule_enabled(True)
            try:
                event = _record_live_goal_event(agent, inbound_by_goal[nid(goal)], goal, kind,
                    payload={"fixture_census": "connected_task", "fixture_index": index,
                             **({"common_ground_delta": claim} if kind == "action_result" else {})})
                producer_counters = {
                    "scale": {str(k): int(v) for k, v in dict(audit.scale_audit_snapshot()).items()},
                    "per_rule": [[int(i), str(m), int(v)] for i, m, v in audit.scale_audit_per_rule_snapshot()],
                }
            finally:
                audit.scale_audit_set_per_rule_enabled(False)
                audit.scale_audit_set_enabled(False)
            if event is None:
                raise RuntimeError("production lifecycle event writer refused the fixture event")
            event_id = nid(event)
            event_frame[event_id] = active_frame
        yield event_id, active_frame, event_frame, goal_nodes, producer_counters


def exact_treewidth(frame_ids: list[int], edges: set[tuple[int, int]]) -> int:
    best = len(frame_ids)
    for order in permutations(frame_ids):
        graph = {f: set() for f in frame_ids}
        for a, b in edges:
            if a != b:
                graph[a].add(b); graph[b].add(a)
        width = 0
        for frame in order:
            neighbours = graph[frame]
            width = max(width, len(neighbours))
            for a, b in combinations(neighbours, 2):
                graph[a].add(b); graph[b].add(a)
            for other in neighbours:
                graph[other].discard(frame)
            graph[frame].clear()
        best = min(best, width)
    return best


def run_arm(arm: str) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_core import load_seeds_into
    fixture = json.loads(FIXTURE.read_text())
    agent = WorldAdapter(seeds=())
    load_seeds_into(agent.s, agent.agent, ["conversation_discourse_state"])
    events: list[int] = []
    frame_owner: dict[int, int] = {}
    goals = []
    traced = arm == "trace"
    agent.inner.runtime_access_trace_set_enabled(False)
    agent.inner.runtime_access_trace_reset()
    checkpoints = []
    event_index_by_id: dict[int, int] = {}
    for event_index, (event_id, frame_id, owner_snapshot, current_goals, producer_counters) in enumerate(
            materialize_fixture(agent, fixture)):
        events.append(event_id)
        frame_owner.update(owner_snapshot)
        goals = list(current_goals)
        event_index_by_id[event_id] = event_index
        agent.inner.runtime_access_trace_reset()
        agent.inner.runtime_access_trace_set_enabled(traced)
        agent.inner.scale_audit_reset()
        agent.inner.scale_audit_per_rule_reset()
        agent.inner.scale_audit_set_enabled(True)
        agent.inner.scale_audit_set_per_rule_enabled(True)
        wall_start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
        run_report = agent.inner.run_rules_report(CAP, False)
        wall_ns, cpu_ns = time.perf_counter_ns() - wall_start, time.process_time_ns() - cpu_start
        scale_counts = {str(k): int(v) for k, v in dict(agent.inner.scale_audit_snapshot()).items()}
        per_rule_counts = [[int(i), str(metric), int(count)]
                           for i, metric, count in agent.inner.scale_audit_per_rule_snapshot()]
        agent.inner.scale_audit_set_per_rule_enabled(False)
        agent.inner.scale_audit_set_enabled(False)
        agent.inner.runtime_access_trace_set_enabled(False)
        trace_rows, dropped = agent.inner.runtime_access_trace_snapshot()
        graph = agent.inner.graph_to_dict()
        checkpoint_goals = []
        for goal in goals:
            goal_id = nid(goal)
            transition_ids = [nid(e) for e in agent.inner.neighbours(goal, "transitioned_by")]
            checkpoint_goals.append({
                "node": goal_id, "frame": frame_owner[goal_id],
                "lifecycle_status": agent.s.node(goal)["attrs"].get("lifecycle_status"),
                "transition_event_indices": sorted(event_index_by_id[e] for e in transition_ids
                                                    if e in event_index_by_id),
            })
        checkpoints.append({
            "event_index": event_index, "event_id": event_id,
            "event_frame": frame_id, "closure": dict(run_report),
            "wall_ns": wall_ns, "cpu_ns": cpu_ns, "graph_digest": graph_digest(graph),
            "node_count": len(graph["nodes"]), "edge_count": len(graph["edges"]),
            "scale_audit_counters": scale_counts,
            "per_rule_scale_audit_counters": per_rule_counts,
            "producer_scale_audit_counters": producer_counters,
            "goal_snapshots": checkpoint_goals,
            "trace_dropped": int(dropped),
            "trace_events": [
                {"rule_uid": int(r[0]), "kind": r[1], "node": r[2],
                 "resource": r[3], "peer": r[4], "count": int(r[5])}
                for r in trace_rows
            ],
        })
    if len(events) != 10 or len(set(frame_owner[e] for e in events)) != 3:
        raise RuntimeError("fixture-derived event frame assignment is incomplete")
    agent.inner.runtime_access_trace_set_enabled(False)
    final_graph = agent.inner.graph_to_dict()
    frame_owner_full = {int(k): int(v) for k, v in frame_owner.items()}
    frame_ids = sorted(set(frame_owner_full.values()))
    boundary_frames: dict[int, set[int]] = {}
    direct_cross_edges = []
    boundary_incidence = []
    frame_interaction = set()
    for edge in final_graph["edges"]:
        src, tgt = int(edge["src"]), int(edge["tgt"])
        sf, tf = frame_owner_full.get(src), frame_owner_full.get(tgt)
        if sf is not None and tf is not None:
            if sf != tf:
                direct_cross_edges.append({"src": src, "type": edge["type"], "tgt": tgt,
                                           "src_frame": sf, "tgt_frame": tf})
                frame_interaction.add(tuple(sorted((sf, tf))))
        elif sf is not None or tf is not None:
            frame = sf if sf is not None else tf
            other = tgt if sf is not None else src
            boundary_frames.setdefault(other, set()).add(frame)
            boundary_incidence.append({"src": src, "type": edge["type"], "tgt": tgt,
                                       "frame": frame, "boundary_node": other})
    for touched in boundary_frames.values():
        frame_interaction.update(combinations(sorted(touched), 2))
    treewidth = exact_treewidth(frame_ids, frame_interaction)

    names_by_uid = {}
    access_sets = []
    for index, name, active, reads, term_edges, writes, reads_any, writes_any in agent.inner.rule_access_sets():
        meta = agent.inner.rule_metadata(index)
        uid = int(meta["rule_uid"])
        names_by_uid[uid] = name
        access_sets.append({"index": int(index), "uid": uid, "name": name,
                            "active": bool(active), "reads": sorted(set(reads) | set(term_edges)),
                            "writes": sorted(writes), "reads_any": bool(reads_any),
                            "writes_any": bool(writes_any)})
    for checkpoint in checkpoints:
        for row in checkpoint["trace_events"]:
            row["rule_name"] = names_by_uid.get(row["rule_uid"], "unknown")
            row["node_frame"] = frame_owner_full.get(row["node"]) if row["node"] is not None else None
            row["peer_frame"] = frame_owner_full.get(row["peer"]) if row["peer"] is not None else None
        checkpoint["per_rule_scale_audit_counters"] = [
            {"rule_index": index, "rule_name": next((r["name"] for r in access_sets
                                                      if r["index"] == index), "unknown"),
             "metric": metric, "count": count}
            for index, metric, count in checkpoint["per_rule_scale_audit_counters"]
        ]

    state = next(n for n in agent.s.nodes("DiscourseState")
                 if agent.s.node(n)["attrs"].get("conversation_id") == "connected_task_census")
    goals_out = [{"node": nid(goal), "attrs": agent.s.node(goal)["attrs"],
                  "frame": frame_owner_full[nid(goal)],
                  "transition_events": [nid(e) for e in agent.inner.neighbours(goal, "transitioned_by")],
                  "transition_event_indices": sorted(event_index_by_id[nid(e)] for e in
                      agent.inner.neighbours(goal, "transitioned_by") if nid(e) in event_index_by_id)}
                 for goal in goals]
    common_grounds = [{"node": nid(n), "attrs": agent.s.node(n)["attrs"]}
                      for n in agent.s.nodes("CommonGround")]
    return {
        "arm": arm, "pid": os.getpid(), "frame_count": len(frame_ids),
        "frame_owner": [[n, frame_owner_full[n]] for n in sorted(frame_owner_full)],
        "frame_ids": frame_ids,
        "event_ids": events,
        "frame_sizes": {str(f): sum(owner == f for owner in frame_owner_full.values())
                        for f in frame_ids},
        "checkpoints": checkpoints,
        "final_graph": final_graph,
        "final_graph_digest": graph_digest(final_graph),
        "final_state_attrs": agent.s.node(state)["attrs"],
        "final_goals": goals_out,
        "final_common_grounds": common_grounds,
        "direct_cross_frame_edges": direct_cross_edges,
        "boundary_incidence_edges": boundary_incidence,
        "boundary_nodes_by_frames": {str(n): sorted(fs) for n, fs in boundary_frames.items()},
        "frame_interaction_edges": [list(e) for e in sorted(frame_interaction)],
        "exact_interaction_treewidth": treewidth,
        "static_rule_access": access_sets,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps({"locked_inputs": locked_inputs()}, indent=2, sort_keys=True))
        return
    current = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != current:
        raise SystemExit("missing or stale lock; regenerate only before a fresh run")
    if len(sys.argv) == 2 and sys.argv[1].startswith("--worker="):
        arm = sys.argv[1].split("=", 1)[1]
        print(json.dumps(run_arm(arm), sort_keys=True, default=str))
        return
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    arms = ["plain", "trace", "repeat"]
    runs = []
    for arm in arms:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), f"--worker={arm}"],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    plain, traced, repeat = runs
    goal_statuses = [goal["attrs"].get("lifecycle_status") for goal in plain["final_goals"]]
    checks = {
        "three_fresh_processes": len({r["pid"] for r in runs}) == 3,
        "all_ten_fixture_events_materialized": all(len(r["event_ids"]) == 10 for r in runs),
        "three_fixture_derived_frames": all(r["frame_count"] == 3 for r in runs),
        "event_and_goal_ownership_complete": all(
            len(r["frame_owner"]) == 12 and all(v > 0 for v in r["frame_sizes"].values()) for r in runs),
        "native_goal_lifecycles_resolved": goal_statuses == ["resolved", "resolved"],
        "goal_transitions_stay_with_origin_frame": {
            int(g["frame"]): g["transition_event_indices"] for g in plain["final_goals"]
        } == {0: [1, 2, 3], 2: [6, 7, 8]},
        "discourse_task_oracle_passes": plain["final_state_attrs"].get("event_index") == 10
            and plain["final_state_attrs"].get("pending_expectation") is None
            and plain["final_state_attrs"].get("expectation_disposition") == "deferred"
            and "location_unresolved" in plain["final_state_attrs"].get("unresolved_residuals", []),
        "common_ground_oracle_passes": sorted(
            tuple(sorted(g["attrs"].get("claims", []))) for g in plain["final_common_grounds"]
        ) == sorted([("calendar_request", "calendar_shared"),
                     ("calendar_checked", "location_shared")]),
        "all_fresh_process_graphs_identical": len({r["final_graph_digest"] for r in runs}) == 1,
        "all_checkpoint_graphs_identical": len({
            tuple(cp["graph_digest"] for cp in r["checkpoints"]) for r in runs
        }) == 1,
        "all_process_counter_profiles_equal": len({
            json.dumps([cp["scale_audit_counters"] for cp in r["checkpoints"]], sort_keys=True)
            for r in runs
        }) == 1,
        "all_checkpoints_fixed_point": all(
            cp["closure"]["status"] == "fixed_point" for r in runs for cp in r["checkpoints"]),
        "tracing_preserves_graph_state": traced["final_graph_digest"] == plain["final_graph_digest"],
        "no_trace_events_dropped": all(cp["trace_dropped"] == 0 for cp in traced["checkpoints"]),
    }
    task_nodes = {n for n, _ in plain["frame_owner"]}
    task_edges = [e for e in plain["final_graph"]["edges"]
                  if int(e["src"]) in task_nodes or int(e["tgt"]) in task_nodes]
    type_counts = {}
    for node in plain["final_graph"]["nodes"]:
        typ = node["type"]
        type_counts[typ] = type_counts.get(typ, 0) + 1
    payload = {
        "schema_version": 1,
        "run_id": "substrate-discourse-connected-task-census-v2-1-20260926",
        "claim_boundary": (
            "Fresh native census of one authored ten-event mixed dialogue task. The source fixture is not a natural-task sample. "
            "Frames follow its origin/unsolicited markers; shared discourse/common-ground state forms explicit boundaries. "
            "This measures structure and partial runtime accesses, not partitioned execution or general locality."
        ),
        "locked_inputs": current, "lock_sha256": sha(LOCK),
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "OZMA_NO_LLM": env["OZMA_NO_LLM"],
                        "OZMA_SEED_PERSIST_DISABLED": env["OZMA_SEED_PERSIST_DISABLED"]},
        "provenance": {"commit": current["commit"],
                       "dirty_worktree": current["dirty_worktree"],
                       "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_discourse_connected_task_census_v2_1.py",
                       "native_extension_sha256": current["native_extension_sha256"],
                       "native_build_manifest_sha256": current["native_build_manifest_sha256"],
                       "cargo_lock_sha256": current["cargo_lock_sha256"]},
        "checks": checks,
        "summary": {
            "event_count": 10, "frame_count": 3,
            "frame_sizes": plain["frame_sizes"],
            "owned_event_goal_nodes": len(plain["frame_owner"]),
            "full_graph_nodes": len(plain["final_graph"]["nodes"]),
            "full_graph_edges": len(plain["final_graph"]["edges"]),
            "frame_incident_edge_count": len(task_edges),
            "direct_cross_frame_edges": len(plain["direct_cross_frame_edges"]),
            "unique_boundary_nodes": len(plain["boundary_nodes_by_frames"]),
            "boundary_incidence_edge_count": len(plain["boundary_incidence_edges"]),
            "frame_interaction_edges": plain["frame_interaction_edges"],
            "exact_interaction_treewidth": plain["exact_interaction_treewidth"],
            "node_type_counts": type_counts,
            "total_native_progress_steps": sum(cp["closure"]["progress_steps"] for cp in plain["checkpoints"]),
            "total_candidate_pairs": sum(cp["scale_audit_counters"].get("cand_enum", 0)
                                          for cp in plain["checkpoints"]),
            "total_term_evaluations": sum(cp["scale_audit_counters"].get("term_evals_total", 0)
                                          for cp in plain["checkpoints"]),
            "total_trace_events": sum(sum(e["count"] for e in cp["trace_events"])
                                       for cp in traced["checkpoints"]),
            "runtime_cross_frame_trace_rows": sum(
                1 for cp in traced["checkpoints"] for e in cp["trace_events"]
                if e["node_frame"] is not None and e["peer_frame"] is not None
                and e["node_frame"] != e["peer_frame"]),
            "static_rules_with_any_access": sum(
                bool(r["reads_any"] or r["writes_any"]) for r in plain["static_rule_access"]),
            "plain_wall_ns_by_checkpoint": [cp["wall_ns"] for cp in plain["checkpoints"]],
            "trace_wall_ns_by_checkpoint": [cp["wall_ns"] for cp in traced["checkpoints"]],
            "peak_rss_kib_by_arm": [r["peak_rss_kib"] for r in runs],
        },
        "runs": runs,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": payload["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("connected task census checks failed; raw capture preserved")


if __name__ == "__main__":
    main()
