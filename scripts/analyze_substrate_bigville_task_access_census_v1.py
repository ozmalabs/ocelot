#!/usr/bin/env python3
"""Independent structural/access analysis for the Bigville diagnostic capture."""
from __future__ import annotations

import hashlib
import json
import itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_bigville_task_access_census_v1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/bigville_task_access_census_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_bigville_task_access_census_v1_analysis_20260926.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_treewidth(nodes: list[int], directed_edges: list[list[int]]) -> int:
    """Brute-force exact elimination width; the registered frames have 5 nodes."""
    best = len(nodes)
    for order in itertools.permutations(nodes):
        graph = {node: set() for node in nodes}
        for src, tgt in directed_edges:
            if src in graph and tgt in graph and src != tgt:
                graph[src].add(tgt)
                graph[tgt].add(src)
        width = 0
        for node in order:
            neighbours = graph[node]
            width = max(width, len(neighbours))
            for a, b in itertools.combinations(neighbours, 2):
                graph[a].add(b)
                graph[b].add(a)
            for peer in neighbours:
                graph[peer].discard(node)
            graph[node].clear()
        best = min(best, width)
    return best


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    full, event, traced = raw["runs"]
    frame_counts = [run["frame_count"] for run in raw["runs"]]
    all_frame_pairs = [[int(node), int(frame)] for node, frame in traced["runtime_node_frame"]]
    edge_frame_pairs = []
    ownership = {node: frame for node, frame in all_frame_pairs}
    for src, tgt in traced["runtime_dependency_edges"]:
        edge_frame_pairs.append((ownership[src], ownership[tgt]))
    representative_frame = [node for node, frame in all_frame_pairs if frame == 0]
    representative_edges = [[src, tgt] for src, tgt in traced["runtime_dependency_edges"]
                            if ownership[src] == 0 and ownership[tgt] == 0]
    frame_treewidth = exact_treewidth(representative_frame, representative_edges)
    event_counts = {}
    event_frame_set = set()
    for row in traced["runtime_access_events"]:
        key = row["kind"]
        event_counts[key] = event_counts.get(key, 0) + row["count"]
        if row["node_frame"] is not None:
            event_frame_set.add(row["node_frame"])
        if row["peer_frame"] is not None:
            event_frame_set.add(row["peer_frame"])
    observed_cross = [row for row in traced["runtime_access_events"]
                      if row["node_frame"] is not None and row["peer_frame"] is not None
                      and row["node_frame"] != row["peer_frame"]]
    c_full = int(full["settlement"]["audit"]["cand_enum"])
    c_event = int(event["settlement"]["audit"]["cand_enum"])
    t_full = int(full["settlement"]["audit"]["term_evals_total"])
    t_event = int(event["settlement"]["audit"]["term_evals_total"])
    full_ms = full["settlement_wall_ns"] / 1e6
    event_ms = event["settlement_wall_ns"] / 1e6
    static = traced["static_rule_access"]
    checks = {
        "raw_runner_checks_all_pass": all(raw["checks"].values()),
        "three_fresh_processes": len({row["pid"] for row in raw["runs"]}) == 3,
        "unique_ownership_for_500_nodes": len(all_frame_pairs) == 500 and len(ownership) == 500,
        "each_runtime_frame_has_five_nodes": all(
            sum(frame == f for frame in ownership.values()) == 5 for f in range(100)),
        "all_1000_dependency_edges_internal": len(edge_frame_pairs) == 1000 and
            all(src == tgt for src, tgt in edge_frame_pairs),
        "exact_component_treewidth_two": frame_treewidth == 2,
        "three_graph_states_equal": len({r["graph_digest"] for r in raw["runs"]}) == 1,
        "event_residual_zero": event["independent_residual_count"] == 0,
        "runtime_events_reach_only_mutated_frame": event_frame_set == {40},
        "observed_access_rows_reconcile": sum(event_counts.values()) == traced["runtime_event_count"],
        "trace_still_marks_read_wildcard": static["reads_any"] is True,
        "observed_runtime_cross_frame_accesses_zero": len(observed_cross) == 0,
    }
    result = {
        "schema_version": 1,
        "run_id": "substrate-bigville-task-access-census-v1-analysis-20260926",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "claim_boundary": raw["claim_boundary"],
        "checks": checks,
        "structure": {
            "runtime_frames": event["frame_count"], "nodes": len(ownership),
            "nodes_per_frame": 5, "runtime_dependency_edges": len(edge_frame_pairs),
            "cross_frame_dependency_edges": sum(a != b for a, b in edge_frame_pairs),
            "frame_hierarchy_depth": 1,
            "exact_treewidth_per_component": frame_treewidth,
            "partition_build_plus_graph_setup_ns_by_arm": [r["build_plus_runtime_partition_ns"] for r in raw["runs"]],
            "partition_map_materialization_ns_by_arm": [r["partition_map_materialization_ns"] for r in raw["runs"]],
        },
        "access": {
            "rule": static,
            "runtime_event_counts_by_kind": dict(sorted(event_counts.items())),
            "observed_frames": sorted(event_frame_set),
            "runtime_trace_is_partial": True,
            "static_reads_any": static["reads_any"],
            "unobserved_pairs_are_not_absence_evidence": True,
        },
        "operation_counts": {
            "full_candidates": c_full, "event_candidates": c_event,
            "candidate_reduction_fraction": (c_full - c_event) / c_full,
            "full_term_evaluations": t_full, "event_term_evaluations": t_event,
            "term_reduction_fraction": (t_full - t_event) / t_full,
        },
        "single_run_settlement_timing": {
            "full_wall_ms": full_ms, "event_wall_ms": event_ms,
            "event_over_full_ratio": event_ms / full_ms,
            "interpretation": "one fresh process per arm, one update each; descriptive only, no repeated timing interval",
        },
        "checks": checks,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks,
                      "candidate_reduction_fraction": result["operation_counts"]["candidate_reduction_fraction"],
                      "term_reduction_fraction": result["operation_counts"]["term_reduction_fraction"],
                      "event_over_full_wall_ratio": result["single_run_settlement_timing"]["event_over_full_ratio"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent analysis checks failed")


if __name__ == "__main__":
    main()
