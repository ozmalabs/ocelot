#!/usr/bin/env python3
"""Independently validate positive-join/topology closure measurements."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2:
    raise SystemExit("usage: analyze_substrate_finite_key_join_topology_v1.py RAW_JSON")
raw_path = Path(sys.argv[1])
raw = json.loads(raw_path.read_text())


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def topology_graph(topology: str, n: int) -> list[tuple[int, int]]:
    if topology == "path":
        return [(i, i+1) for i in range(n-1)]
    if topology == "cycle":
        return [(i, (i+1) % n) for i in range(n)]
    if topology == "layered":
        s = (n-2)//2
        sizes = [1, s, s, 1]
        offsets, cur = [], 0
        for count in sizes:
            offsets.append(cur)
            cur += count
        return [(offsets[level]+i, offsets[level+1]+j)
                for level in range(3) for i in range(sizes[level])
                for j in range(sizes[level+1])]
    raise ValueError(topology)


def oracle(topology: str, n: int, q: int) -> tuple[int, list[int], str, int]:
    edges = topology_graph(topology, n)
    adjacency = [[] for _ in range(n)]
    for src, tgt in edges:
        adjacency[src].append(tgt)
    count, terminal = 0, set()
    def visit(node, remaining):
        nonlocal count
        if remaining == 0:
            count += 1
            terminal.add(node)
            return
        for nxt in adjacency[node]:
            visit(nxt, remaining - 1)
    for start in range(n):
        visit(start, q)
    node_labels = [("Seed", (("idx", i),)) for i in range(n)]
    witness = ("Witness", (("tag", "w"),))
    nodes = sorted(node_labels + [witness])
    projected_edges = [
        (node_labels[src], "link", node_labels[tgt], ()) for src, tgt in edges
    ]
    projected_edges.extend((node_labels[tgt], "result", witness, ()) for tgt in terminal)
    projection = digest({"nodes": nodes, "edges": sorted(projected_edges)})
    return count, sorted(terminal), projection, len(edges)


groups = defaultdict(list)
checks = {
    "all_native_checks_pass": raw["all_checks_pass"],
    "expected_case_count": len(raw["cases"]) == raw["design"]["configuration_count"] * raw["design"]["repeats"],
    "case_ids_unique": len({x["case_id"] for x in raw["cases"]}) == len(raw["cases"]),
    "provenance_files_current": all(
        hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == value
        for name, value in raw["provenance"]["source_sha256"].items()),
    "native_artifact_current": hashlib.sha256(Path(raw["provenance"]["native_path"]).read_bytes()).hexdigest()
        == raw["provenance"]["native_sha256"],
}
for case in raw["cases"]:
    q = case["match_arity"]
    n = case["n_initial_nodes"]
    count, terminal, expected_hash, e0 = oracle(case["topology"], n, q)
    bound = 1 + 2 * (n + 1) ** 2 - e0
    local = {
        "oracle_match_count": case["enumerated_match_bindings"] == count,
        "oracle_terminal_count": case["distinct_terminal_nodes"] == len(terminal),
        "oracle_graph_hash": case["actual_graph_projection_sha256"] == expected_hash,
        "exact_nodes": case["actual_node_count"] == n + 1,
        "exact_edges": case["actual_edge_count"] == e0 + len(terminal),
        "bound_recomputed": case["progress_bound"] == bound,
        "fixed_point": case["native_report"]["status"] == "fixed_point",
        "progress_within_bound": case["native_report"]["progress_steps"] <= bound,
        "budget_not_exceeded": case["native_report"]["budget_overshoot"] == 0,
    }
    checks.update({f"{case['case_id']}:{name}": ok for name, ok in local.items()})
    groups[(case["topology"], n, q)].append(case)

summary = []
for (topology, n, q), rows in sorted(groups.items()):
    times = [x["closure_ns"]/1e6 for x in rows]
    setups = [x["setup_ns"]/1e6 for x in rows]
    summary.append({"topology": topology, "n": n, "q": q, "replicates": len(rows),
                    "input_edges": rows[0]["n_initial_edges"],
                    "match_bindings": rows[0]["enumerated_match_bindings"],
                    "terminal_nodes": rows[0]["distinct_terminal_nodes"],
                    "median_closure_ms": statistics.median(times),
                    "closure_range_ms": [min(times), max(times)],
                    "median_setup_ms": statistics.median(setups),
                    "median_passes": statistics.median(x["native_report"]["passes_completed"] for x in rows)})

result = {
    "schema": "substrate_finite_key_join_topology_analysis_v1",
    "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "check_count": len(checks), "checks": checks,
    "all_checks_pass": all(checks.values()),
    "summary": summary,
    "claim_boundary": "One finite-key add-node/add-edge rule schema across authored positive path joins and three topologies; no native candidate-counter or natural workload claim.",
}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
