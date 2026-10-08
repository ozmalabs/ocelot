#!/usr/bin/env python3
"""Independent structural analyzer for rooted frame proposal panel v1."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, deque
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/rooted_frame_proposal_panel_v1_1_20260928.json"
OUT = ROOT / "evaluation/reports/rooted_frame_proposal_panel_v1_1_analysis_20260928.json"
BASELINE = ROOT / "evaluation/reports/rooted_frame_proposal_panel_v1_20260928.json"


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def width_upper_bound(members: set[int], internal: list[list[Any]]) -> int:
    adj = {n: set() for n in members}
    for s, _, t in internal:
        s, t = int(s), int(t)
        if s in adj and t in adj and s != t:
            adj[s].add(t)
            adj[t].add(s)
    width = 0
    while adj:
        def score(node: int) -> tuple[int, int, int]:
            neighbors = sorted(adj[node])
            missing = sum(1 for i, x in enumerate(neighbors) for y in neighbors[i + 1:] if y not in adj[x])
            return missing, len(neighbors), node
        node = min(adj, key=score)
        neighbors = set(adj[node])
        width = max(width, len(neighbors))
        for neighbor in neighbors:
            adj[neighbor].update(neighbors - {neighbor})
            adj[neighbor].discard(node)
        del adj[node]
    return width


def recompute(snapshot: dict[str, Any], root: int, reference: set[int], radius: int) -> dict[str, Any]:
    nodes = {int(n["id"]): n for n in snapshot["nodes"]}
    adjacency = {node: set() for node in nodes}
    edges = [tuple(e) for e in snapshot["edges"]]
    for source, _, target in edges:
        adjacency[int(source)].add(int(target))
        adjacency[int(target)].add(int(source))
    members = {root}
    frontier = {root}
    for _ in range(radius):
        following = set().union(*(adjacency[n] for n in frontier)) - members if frontier else set()
        members.update(following)
        frontier = following
    internal = [e for e in edges if int(e[0]) in members and int(e[2]) in members]
    cut = [e for e in edges if (int(e[0]) in members) != (int(e[2]) in members)]
    external = {int(e[2]) if int(e[0]) in members else int(e[0]) for e in cut}
    external_types = Counter(nodes[n]["type"] for n in external)
    edge_types = Counter(str(e[1]) for e in cut)
    attr_keys = Counter()
    value_kinds: dict[str, set[str]] = {}
    for node_id in external:
        node = nodes[node_id]
        for key in node.get("attr_keys", []):
            label = f"{node['type']}.{key}"
            attr_keys[label] += 1
            value_kinds.setdefault(label, set()).add(node.get("attr_value_kinds", {}).get(key, "unknown"))
    overlap = members & reference
    union = members | reference
    return {
        "candidate_node_ids": sorted(members),
        "root_node_id": root,
        "algorithm": "undirected typed-edge BFS",
        "radius": radius,
        "member_count": len(members),
        "member_ids_sha256": digest(sorted(members)),
        "internal_edge_count": len(internal),
        "crossing_incidence_count": len(cut),
        "distinct_external_node_count": len(external),
        "external_node_type_counts": dict(sorted(external_types.items())),
        "crossing_edge_type_counts": dict(sorted(edge_types.items())),
        "owned_induced_width_upper_bound": width_upper_bound(members, internal),
        "reference_overlap_after_proposal": {
            "precision": len(overlap) / len(members) if members else 0.0,
            "recall": len(overlap) / len(reference) if reference else 0.0,
            "jaccard": len(overlap) / len(union) if union else 1.0,
            "missed_reference_nodes": len(reference - members),
        },
        "external_boundary_attribute_key_counts": dict(sorted(attr_keys.items())),
        "external_boundary_attribute_python_value_kinds": {k: sorted(v) for k, v in sorted(value_kinds.items())},
    }


def recompute_trace_touch(trace: dict[str, Any], members: set[int], reference: set[int]) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    by_kind: Counter[str] = Counter()
    by_rule: Counter[int] = Counter()
    for row in trace.get("event_rows", []):
        count = int(row["count"])
        ids = {int(x) for x in (row.get("node"), row.get("peer")) if x is not None}
        inside = ids & members
        if not ids:
            totals["events_without_concrete_node_ids"] += count
        if inside:
            totals["touches_candidate"] += count
            by_kind[str(row["kind"])] += count
            by_rule[int(row["rule_uid"])] += count
        if ids & reference:
            totals["touches_operational_reference"] += count
        if ids and ids <= members:
            totals["all_concrete_ids_inside_candidate"] += count
        elif ids and not inside:
            totals["all_concrete_ids_outside_candidate"] += count
        elif inside:
            totals["partially_inside_candidate"] += count
    for key in ("touches_candidate", "touches_operational_reference", "all_concrete_ids_inside_candidate",
                "all_concrete_ids_outside_candidate", "partially_inside_candidate", "events_without_concrete_node_ids"):
        totals[key] += 0
    weighted = int(trace.get("weighted_event_count", 0))
    totals["weighted_trace_events"] = weighted
    return {
        **dict(totals),
        "touch_fraction": totals["touches_candidate"] / weighted if weighted else None,
        "touches_by_kind": dict(sorted(by_kind.items())),
        "touching_rule_uid_count": len(by_rule),
        "event_rows": len(trace.get("event_rows", [])),
        "dropped": trace.get("dropped"),
    }


def main() -> None:
    raw = json.loads(RAW.read_text())
    baseline = json.loads(BASELINE.read_text())
    runs = raw.get("runs", [])
    checks: dict[str, bool] = {
        "three_distinct_workers": len(runs) == 3 and len({r.get("pid") for r in runs}) == 3,
        "source_lock_held_stable": bool(runs) and all(r.get("worker_started_inputs") == r.get("worker_finished_inputs") == raw.get("locked_inputs") for r in runs),
        "runner_checks_all_pass": bool(raw.get("checks")) and all(raw["checks"].values()),
        "control_checks_all_pass": bool(raw.get("control_checks")) and all(raw["control_checks"].values()),
        "accepted_v1_baseline_hash_locked": raw.get("locked_inputs", {}).get("source_sha256", {}).get("baseline_capture") == hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        "trace_rows_nonempty_zero_drops_and_weight_conserves": bool(runs) and all(
            all(t.get("access_trace", {}).get("weighted_event_count", 0) > 0
                and t["access_trace"].get("dropped") == 0
                and t["access_trace"]["weighted_event_count"] == sum(e["count"] for e in t["access_trace"].get("event_rows", []))
                for t in r.get("turns", [])) for r in runs),
    }
    snapshots = [r.get("structural_graph_snapshot") for r in runs]
    checks["structural_snapshots_present"] = all(isinstance(s, dict) and s.get("nodes") and s.get("edges") for s in snapshots)
    checks["structural_snapshot_reproduces"] = len({digest(s) for s in snapshots}) == 1 if checks["structural_snapshots_present"] else False
    comparisons = []
    for run in runs:
        snapshot = run["structural_graph_snapshot"]
        for turn_index in (0, 1):
            key = f"turn_{turn_index}"
            root = int(run["turns"][turn_index]["message_id"])
            reference = set(map(int, run["task_boundaries"][key]["owned_node_ids"]))
            observed = run["rooted_candidates"][key]
            for radius, row in enumerate(observed):
                expected = recompute(snapshot, root, reference, radius)
                trace_expected = recompute_trace_touch(run["turns"][turn_index]["access_trace"], set(expected["candidate_node_ids"]), reference)
                matches = all((row.get(k, {}).get("value") == v if k == "owned_induced_width_upper_bound" else row.get(k) == v)
                              for k, v in expected.items())
                trace_observed = row.get("access_trace_projection", {})
                counter_keys = {"touches_candidate", "touches_operational_reference", "all_concrete_ids_inside_candidate",
                                "all_concrete_ids_outside_candidate", "partially_inside_candidate", "events_without_concrete_node_ids",
                                "weighted_trace_events"}
                trace_match = all((trace_observed.get(k, 0) == v if k in counter_keys else trace_observed.get(k) == v)
                                  for k, v in trace_expected.items())
                matches = matches and trace_match
                expected["access_trace_projection"] = trace_expected
                comparisons.append({"replicate": run["replicate"], "turn": key, "radius": radius,
                                    "matches_independent_recomputation": matches,
                                    "expected": expected, "observed": {k: row.get(k) for k in expected}})
    checks["all_18_proposals_match_independent_recomputation"] = len(comparisons) == 18 and all(c["matches_independent_recomputation"] for c in comparisons)
    signature_groups: dict[str, list[str]] = {}
    for run in runs:
        for turn in ("turn_0", "turn_1"):
            signature = digest([{k: v for k, v in row.items() if k not in ("adjacency_build_ns_shared", "bfs_ns", "boundary_projection_ns")}
                                for row in run["rooted_candidates"][turn]])
            signature_groups.setdefault(turn, []).append(signature)
    checks["proposal_structure_repeats_across_workers"] = all(len(set(values)) == 1 for values in signature_groups.values())
    baseline_digests = {r.get("whole_graph_semantic_sha256") for r in baseline.get("runs", [])}
    checks["traced_semantics_match_accepted_v1_baseline"] = len(baseline_digests) == 1 and bool(baseline_digests) and all(r.get("whole_graph_semantic_sha256") in baseline_digests for r in runs)
    summary = {}
    for turn in ("turn_0", "turn_1"):
        summary[turn] = []
        for radius in range(3):
            rows = [r["rooted_candidates"][turn][radius] for r in runs]
            summary[turn].append({
                "radius": radius,
                "member_count": rows[0]["member_count"],
                "crossing_incidence_count": rows[0]["crossing_incidence_count"],
                "distinct_external_node_count": rows[0]["distinct_external_node_count"],
                "reference_precision": rows[0]["reference_overlap_after_proposal"]["precision"],
                "reference_recall": rows[0]["reference_overlap_after_proposal"]["recall"],
                "reference_jaccard": rows[0]["reference_overlap_after_proposal"]["jaccard"],
                "adjacency_build_ns_median": sorted(r["adjacency_build_ns_shared"] for r in rows)[len(rows)//2],
                "bfs_ns_median": sorted(r["bfs_ns"] for r in rows)[len(rows)//2],
                "projection_ns_median": sorted(r["boundary_projection_ns"] for r in rows)[len(rows)//2],
            })
    result = {
        "analysis_id": "rooted_frame_proposal_panel_v1_analysis_20260928",
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "baseline_v1_sha256": hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        "checks": checks,
        "summary": summary,
        "proposal_recomputations": comparisons,
        "claim_boundary": "Independent verification of fixed-radius graph proposals on one authored task pair. Agreement with protocol ownership measures label overlap only; no task correctness, learned frames, complete operation-dependency coverage, or prevalence claim follows.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent rooted-frame proposal analysis failed")


if __name__ == "__main__":
    main()
