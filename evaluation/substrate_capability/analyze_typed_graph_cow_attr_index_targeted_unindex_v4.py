#!/usr/bin/env python3
"""Independently summarize the targeted-unindex mutation capture."""
from __future__ import annotations
import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/typed_graph_cow_attr_index_targeted_unindex_v4_raw_20261006.json"
OUT = ROOT / "evaluation/reports/typed_graph_cow_attr_index_targeted_unindex_v4_analysis_20261006.json"
BASELINE = ROOT / "evaluation/reports/typed_graph_cow_attr_index_mutation_v3_analysis_20261006.json"

def main() -> int:
    raw = json.loads(RAW.read_text())
    base = json.loads(BASELINE.read_text())
    rows = []
    for cell in raw["capture"]["cells"]:
        for case in cell["mutation_samples"]:
            shared = [f + w for f, w in zip(case["shared_fork_ns"], case["shared_write_ns"])]
            eager = [f + w for f, w in zip(case["eager_fork_ns"], case["eager_write_ns"])]
            prior = next(r for r in base["rows"] if r["nodes"] == cell["nodes"] and r["mutation"] == case["name"])
            rows.append({"nodes": cell["nodes"], "mutation": case["name"], "replicates": len(shared),
                         "shared_fork_median_ns": statistics.median(case["shared_fork_ns"]),
                         "eager_fork_median_ns": statistics.median(case["eager_fork_ns"]),
                         "shared_write_median_ns": statistics.median(case["shared_write_ns"]),
                         "eager_write_median_ns": statistics.median(case["eager_write_ns"]),
                         "shared_fork_plus_write_median_ns": statistics.median(shared),
                         "eager_fork_plus_write_median_ns": statistics.median(eager),
                         "paired_total_reduction_pct": statistics.median([(1-s/e)*100 for s,e in zip(shared,eager)]),
                         "v3_shared_write_median_ns": prior["shared_write_median_ns"],
                         "v3_to_v4_shared_write_reduction_pct": (1-statistics.median(case["shared_write_ns"])
                              /prior["shared_write_median_ns"])*100 if prior["shared_write_median_ns"] else None,
                         "semantic_isolation_pass": all(case["shared_semantics"])
                              and all(case["eager_semantics"]),
                         "shared_total_samples_ns": shared, "eager_total_samples_ns": eager})
    gates = {"source_stable": raw["source_stable"], "12_cells": len(rows) == 12,
             "baseline_queries_exact": all(c["baseline_queries_exact"] for c in raw["capture"]["cells"]),
             "all_branch_mutation_and_isolation_checks": all(r["semantic_isolation_pass"] for r in rows),
             "v3_baseline_analysis_pass": base["integrity_pass"]}
    valid = all(gates.values())
    payload = {"schema": "TypedGraphCowAttrIndexTargetedUnindexV4Analysis", "integrity_pass": valid,
               "gates": gates, "rows": rows,
               "claim_boundary": "source-locked synthetic graph mutation comparison; not whole-Substrate closure or natural-task prevalence"}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "integrity_pass": valid, "rows": len(rows)}, indent=2))
    return 0 if valid else 1

if __name__ == "__main__": raise SystemExit(main())
