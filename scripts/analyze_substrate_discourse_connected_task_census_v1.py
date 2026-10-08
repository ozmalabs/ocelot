#!/usr/bin/env python3
"""Independent structural checks for the connected discourse task capture."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/discourse_connected_task_census_lock_20260926.json"
FIXTURE = ROOT / "tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json"
OUT = ROOT / "evaluation/reports/substrate_discourse_connected_task_census_v1_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_treewidth(vertices: list[int], edges: set[tuple[int, int]]) -> int:
    if not vertices:
        return 0
    best = len(vertices)
    for order in itertools.permutations(vertices):
        graph = {v: set() for v in vertices}
        for a, b in edges:
            if a != b:
                graph[a].add(b); graph[b].add(a)
        width = 0
        for v in order:
            neighbours = graph[v]
            width = max(width, len(neighbours))
            for a, b in itertools.combinations(neighbours, 2):
                graph[a].add(b); graph[b].add(a)
            for other in neighbours:
                graph[other].discard(v)
            graph[v].clear()
        best = min(best, width)
    return best


def main() -> None:
    raw = json.loads(RAW.read_text())
    fixture = json.loads(FIXTURE.read_text())
    plain, traced, repeated = raw["runs"]
    owner = {int(node): int(frame) for node, frame in plain["frame_owner"]}
    frame_ids = [int(x) for x in plain["frame_ids"]]
    event_to_frame: dict[int, int] = {}
    frame_cursor = -1
    next_frame = 0
    for row, event_id in zip(fixture["events"], plain["event_ids"]):
        if row["relation"] in {"origin", "unsolicited"}:
            frame_cursor = next_frame
            next_frame += 1
        event_to_frame[int(event_id)] = frame_cursor
    graph = plain["final_graph"]
    boundary_frames: dict[int, set[int]] = {}
    direct_cross = []
    interaction_edges: set[tuple[int, int]] = set()
    boundary_incidence = []
    edge_type_counts = {}
    for edge in graph["edges"]:
        src, tgt, et = int(edge["src"]), int(edge["tgt"]), edge["type"]
        edge_type_counts[et] = edge_type_counts.get(et, 0) + 1
        sf, tf = owner.get(src), owner.get(tgt)
        if sf is not None and tf is not None and sf != tf:
            direct_cross.append((src, et, tgt, sf, tf))
            interaction_edges.add(tuple(sorted((sf, tf))))
        elif (sf is None) != (tf is None):
            frame = sf if sf is not None else tf
            boundary_node = tgt if sf is not None else src
            boundary_frames.setdefault(boundary_node, set()).add(frame)
            boundary_incidence.append((src, et, tgt, frame, boundary_node))
    for touched in boundary_frames.values():
        interaction_edges.update(itertools.combinations(sorted(touched), 2))
    treewidth = exact_treewidth(frame_ids, interaction_edges)

    expected_transition_indices = {0: [1, 2, 3], 2: [6, 7, 8]}
    actual_transition_indices = {
        int(goal["frame"]): goal["transition_event_indices"] for goal in plain["final_goals"]
    }
    traced_rows = [event for cp in traced["checkpoints"] for event in cp["trace_events"]]
    dropped = sum(cp["trace_dropped"] for cp in traced["checkpoints"])
    runtime_cross = [row for row in traced_rows if row["node_frame"] is not None
                     and row["peer_frame"] is not None
                     and row["node_frame"] != row["peer_frame"]]
    rule_trace_counts = {}
    for row in traced_rows:
        rule_trace_counts[row["rule_name"]] = rule_trace_counts.get(row["rule_name"], 0) + row["count"]
    checks = {
        "runner_integrity_checks_all_pass": all(raw["checks"].values()),
        "three_processes_have_same_full_graph": len({r["final_graph_digest"] for r in raw["runs"]}) == 1,
        "all_ten_fixture_events_present": len(plain["event_ids"]) == len(fixture["events"]) == 10,
        "fixture_frame_assignment_recomputed": event_to_frame == {
            int(event): owner[int(event)] for event in plain["event_ids"]},
        "all_event_and_goal_nodes_owned_once": len(owner) == 12 and len(set(owner)) == 12,
        "direct_cross_edges_recompute": len(direct_cross) == len(plain["direct_cross_frame_edges"]) == 2,
        "boundary_incidence_recomputes": len(boundary_incidence) == len(plain["boundary_incidence_edges"]) == 40,
        "interaction_graph_treewidth_recomputes": treewidth == plain["exact_interaction_treewidth"] == 2,
        "cross_frame_goal_lifecycle_absent": actual_transition_indices == expected_transition_indices,
        "task_and_common_ground_oracles_pass": raw["checks"]["discourse_task_oracle_passes"]
            and raw["checks"]["common_ground_oracle_passes"],
        "runtime_trace_reconciles_without_drops": dropped == 0
            and sum(row["count"] for row in traced_rows) == raw["summary"]["total_trace_events"],
        "no_direct_cross_frame_trace_peer_rows": len(runtime_cross) == 0,
    }
    summary = {
        "event_count": len(plain["event_ids"]), "frame_count": len(frame_ids),
        "frame_sizes": plain["frame_sizes"], "full_graph_nodes": len(graph["nodes"]),
        "full_graph_edges": len(graph["edges"]),
        "frame_owned_nodes": len(owner),
        "direct_cross_frame_edge_count": len(direct_cross),
        "direct_cross_frame_edge_types": {
            et: sum(1 for _, typ, _, _, _ in direct_cross if typ == et)
            for et in sorted({row[1] for row in direct_cross})},
        "boundary_node_count": len(boundary_frames),
        "boundary_incidence_edge_count": len(boundary_incidence),
        "boundary_frames_by_node": {str(node): sorted(frames)
                                    for node, frames in sorted(boundary_frames.items())},
        "frame_interaction_edges": [list(edge) for edge in sorted(interaction_edges)],
        "exact_frame_interaction_treewidth": treewidth,
        "native_rule_progress_steps": [sum(cp["closure"]["progress_steps"]
                                            for cp in run["checkpoints"]) for run in raw["runs"]],
        "runtime_trace_event_count": sum(row["count"] for row in traced_rows),
        "runtime_trace_rule_counts": dict(sorted(rule_trace_counts.items())),
        "runtime_trace_cross_frame_peer_rows": len(runtime_cross),
        "static_rule_count": len(plain["static_rule_access"]),
        "static_wildcard_rule_count": sum(
            bool(rule["reads_any"] or rule["writes_any"]) for rule in plain["static_rule_access"]),
        "closure_wall_ns_plain": [cp["wall_ns"] for cp in plain["checkpoints"]],
        "closure_wall_ns_traced": [cp["wall_ns"] for cp in traced["checkpoints"]],
        "timing_claim": "single fresh-process trace arm and one plain arm; per-checkpoint durations are descriptive only",
        "goal_transition_indices": actual_transition_indices,
    }
    result = {
        "schema_version": 1,
        "run_id": "substrate-discourse-connected-task-census-v1-analysis-20260926",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "fixture_sha256": sha(FIXTURE), "checks": checks, "summary": summary,
        "claim_boundary": raw["claim_boundary"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent structural analysis found a mismatch")


if __name__ == "__main__":
    main()
