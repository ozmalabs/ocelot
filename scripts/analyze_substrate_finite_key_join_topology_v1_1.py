#!/usr/bin/env python3
"""Compare independent processes for join/topology closure semantics."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("usage: analyze_substrate_finite_key_join_topology_v1_1.py V1_RAW V1_1_RAW")
paths = [Path(x) for x in sys.argv[1:]]
raws = [json.loads(x.read_text()) for x in paths]


def semantic(raw):
    keys = ("topology", "n_initial_nodes", "n_initial_edges", "match_arity",
            "enumerated_match_bindings", "distinct_terminal_nodes", "progress_bound",
            "actual_node_count", "actual_edge_count", "actual_graph_projection_sha256",
            "checks", "all_checks_pass", "native_report")
    return {x["case_id"]: {k: x[k] for k in keys} for x in raw["cases"]}


def stable_sources(raw):
    source = raw["provenance"]["source_sha256"]
    want = ("scripts/analyze_mint_termination_fragment.py",
            "runners/dsl/src/rewrite.rs", "runners/dsl/src/graph.rs",
            "docs/research/engine_substrate/SUBSTRATE_FINITE_KEY_JOIN_TOPOLOGY_PREREG_20260926.md")
    return {k: source[k] for k in want}


a, b = raws
checks = {
    "case_sets_equal": set(semantic(a)) == set(semantic(b)),
    "exact_semantic_replication": semantic(a) == semantic(b),
    "both_raw_captures_pass": a["all_checks_pass"] and b["all_checks_pass"],
    "same_design": a["design"] == b["design"],
    "complete_case_count": len(a["cases"]) == len(b["cases"]) == 210,
    "same_native_artifact": a["provenance"]["native_sha256"] == b["provenance"]["native_sha256"],
    "same_runtime_sources": stable_sources(a) == stable_sources(b),
}
result = {
    "schema": "substrate_finite_key_join_topology_analysis_v1_1",
    "raw_sha256": {f"process_{i+1}:{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()
                   for i, path in enumerate(paths)},
    "checks": checks,
    "all_checks_pass": all(checks.values()),
    "process_ids": [x["run_id"] for x in raws],
    "per_process_check_counts": [len(x["cases"]) for x in raws],
    "claim_boundary": "Exact fresh-process semantics for one positive finite-key rule schema over the registered authored topologies.",
}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
