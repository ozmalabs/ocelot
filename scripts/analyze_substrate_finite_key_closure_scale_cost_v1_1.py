#!/usr/bin/env python3
"""Compare two process captures of the finite-key closure scale-cost matrix."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: analyze_substrate_finite_key_closure_scale_cost_v1_1.py V1_RAW V1_1_RAW")
paths = [Path(x) for x in sys.argv[1:]]
raws = [json.loads(p.read_text()) for p in paths]


def semantic_rows(raw):
    return {x["case_id"]: {
        k: x[k] for k in ("analyzer_bound", "actual_node_count", "actual_edge_count",
                          "expected_edge_count", "actual_graph_projection_sha256", "checks",
                          "all_checks_pass", "native_report")
    } for x in raw["cases"]}


def summary(raw):
    cells = defaultdict(list)
    for row in raw["cases"]:
        cells[(row["n_initial_nodes"], row["m_mint_signatures"])].append(row)
    out = []
    for (n, m), rows in sorted(cells.items()):
        setup = [r["setup_ns"] / 1e6 for r in rows]
        closure = [r["closure_ns"] / 1e6 for r in rows]
        out.append({"n": n, "m": m, "replicates": len(rows),
                    "median_setup_ms": statistics.median(setup),
                    "setup_range_ms": [min(setup), max(setup)],
                    "median_closure_ms": statistics.median(closure),
                    "closure_range_ms": [min(closure), max(closure)],
                    "median_passes": statistics.median(r["native_report"]["passes_completed"] for r in rows),
                    "median_edges": statistics.median(r["actual_edge_count"] for r in rows)})
    return out


def runtime_sources(raw):
    sources = raw["provenance"]["source_sha256"]
    return {k: sources[k] for k in (
        "scripts/analyze_mint_termination_fragment.py",
        "runners/dsl/src/rewrite.rs",
        "runners/dsl/src/graph.rs")}


semantic_a, semantic_b = map(semantic_rows, raws)
checks = {
    "same_case_ids": set(semantic_a) == set(semantic_b),
    "exact_semantic_replication": semantic_a == semantic_b,
    "both_native_matrices_pass": all(r["all_checks_pass"] for r in raws),
    "same_design": raws[0]["design"] == raws[1]["design"],
    "same_runtime_sources": runtime_sources(raws[0]) == runtime_sources(raws[1]),
    "same_native_artifact": raws[0]["provenance"]["native_sha256"] == raws[1]["provenance"]["native_sha256"],
    "case_counts_complete": all(len(r["cases"]) == 147 for r in raws),
}
result = {
    "schema": "substrate_finite_key_closure_scale_cost_analysis_v1_1",
    "raw_sha256": {f"process_{i+1}:{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
                   for i, p in enumerate(paths)},
    "checks": checks,
    "all_checks_pass": all(checks.values()),
    "process_summaries": {raw["run_id"]: summary(raw) for raw in raws},
    "claim_boundary": "Fresh-process semantic replication and descriptive closure timing for one fixed recursive finite-key rule schema and cycle topology.",
}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
