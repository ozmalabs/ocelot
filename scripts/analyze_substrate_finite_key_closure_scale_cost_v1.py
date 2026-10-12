#!/usr/bin/env python3
"""Independently validate finite-key closure scale-cost captures."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("usage: analyze_substrate_finite_key_closure_scale_cost_v1.py RAW_JSON")
raw_path = Path(sys.argv[1])
raw = json.loads(raw_path.read_text())


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def expected_projection_hash(n: int, m: int) -> str:
    nodes = [("Seed", (("idx", i),)) for i in range(n)]
    nodes += [("Witness", (("tag", f"w{i}"),)) for i in range(m)]
    node_labels = [("Seed", (("idx", i),)) for i in range(n)]
    node_labels += [("Witness", (("tag", f"w{i}"),)) for i in range(m)]
    edges = []
    for i in range(n):
        edges.append((node_labels[i], "link", node_labels[(i + 1) % n], ()))
    for source in node_labels:
        for i in range(m):
            target = node_labels[n + i]
            edges.append((source, "link", target, ()))
    return digest({"nodes": sorted(nodes), "edges": sorted(edges)})


sizes = raw["design"]["sizes"]
sig_counts = raw["design"]["mint_signature_counts"]
repeats = raw["design"]["repeats_per_cell"]
cases = raw["cases"]
checks = {
    "expected_matrix_size": len(cases) == len(sizes) * len(sig_counts) * repeats,
    "all_cells_unique": len({c["case_id"] for c in cases}) == len(cases),
    "all_native_checks_pass": all(c["all_checks_pass"] for c in cases),
    "all_fixed_points": all(c["native_report"]["status"] == "fixed_point" for c in cases),
    "no_budget_exits": all(c["native_report"]["budget_overshoot"] == 0 for c in cases),
    "bound_recomputed": all(c["analyzer_bound"] == c["m_mint_signatures"]
                             + (c["n_initial_nodes"] + c["m_mint_signatures"]) ** 2
                             - c["n_initial_nodes"] for c in cases),
    "progress_within_bound": all(c["native_report"]["progress_steps"] <= c["analyzer_bound"] for c in cases),
    "node_counts_exact": all(c["actual_node_count"] == c["n_initial_nodes"] + c["m_mint_signatures"] for c in cases),
    "edge_counts_exact": all(c["actual_edge_count"] == c["n_initial_nodes"]
                              + c["m_mint_signatures"] * (c["n_initial_nodes"] + c["m_mint_signatures"])
                              for c in cases),
    "projection_hashes_match_independent_oracle": all(
        c["actual_graph_projection_sha256"] == expected_projection_hash(
            c["n_initial_nodes"], c["m_mint_signatures"]) for c in cases),
}

grouped = defaultdict(list)
for c in cases:
    grouped[(c["n_initial_nodes"], c["m_mint_signatures"])].append(c)
summary = []
for (n, m), rows in sorted(grouped.items()):
    setup = [x["setup_ns"] / 1e6 for x in rows]
    closure = [x["closure_ns"] / 1e6 for x in rows]
    summary.append({
        "n": n, "m": m, "replicates": len(rows),
        "median_setup_ms": statistics.median(setup),
        "setup_range_ms": [min(setup), max(setup)],
        "median_closure_ms": statistics.median(closure),
        "closure_range_ms": [min(closure), max(closure)],
        "median_passes": statistics.median(x["native_report"]["passes_completed"] for x in rows),
        "median_progress_steps": statistics.median(x["native_report"]["progress_steps"] for x in rows),
        "median_final_edges": statistics.median(x["actual_edge_count"] for x in rows),
    })

growth = []
for m in sig_counts:
    points = [x for x in summary if x["m"] == m]
    for left, right in zip(points, points[1:]):
        growth.append({
            "m": m,
            "n_from": left["n"], "n_to": right["n"],
            "closure_time_ratio": (right["median_closure_ms"] / left["median_closure_ms"]
                                   if left["median_closure_ms"] else None),
            "edge_count_ratio": right["median_final_edges"] / left["median_final_edges"],
        })
result = {
    "schema": "substrate_finite_key_closure_scale_cost_analysis_v1",
    "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    "checks": checks,
    "all_checks_pass": all(checks.values()),
    "summary": summary,
    "adjacent_size_growth": growth,
    "claim_boundary": "Held-rule closure scaling on one finite-key recursive schema and cycle topology; no general polynomial timing law.",
}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
