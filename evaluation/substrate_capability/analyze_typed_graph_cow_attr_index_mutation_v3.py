#!/usr/bin/env python3
"""Independent summary of the attribute-index COW mutation capture."""
from __future__ import annotations
import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "evaluation/reports/typed_graph_cow_attr_index_mutation_v3_raw_20261006.json"
OUT = ROOT / "evaluation/reports/typed_graph_cow_attr_index_mutation_v3_analysis_20261006.json"

def main() -> int:
    raw = json.loads(RAW.read_text())
    rows = []
    for cell in raw["capture"]["cells"]:
        for case in cell["mutation_samples"]:
            shared_total = [f + w for f, w in zip(case["shared_fork_ns"], case["shared_write_ns"])]
            eager_total = [f + w for f, w in zip(case["eager_fork_ns"], case["eager_write_ns"])]
            shared_med, eager_med = statistics.median(shared_total), statistics.median(eager_total)
            rows.append({"nodes": cell["nodes"], "mutation": case["name"],
                         "replicates": len(shared_total),
                         "shared_fork_median_ns": statistics.median(case["shared_fork_ns"]),
                         "eager_fork_median_ns": statistics.median(case["eager_fork_ns"]),
                         "shared_write_median_ns": statistics.median(case["shared_write_ns"]),
                         "eager_write_median_ns": statistics.median(case["eager_write_ns"]),
                         "shared_fork_plus_write_median_ns": shared_med,
                         "eager_fork_plus_write_median_ns": eager_med,
                         "paired_total_reduction_pct": statistics.median(
                             [(1 - s / e) * 100 for s, e in zip(shared_total, eager_total)]),
                         "semantic_isolation_pass": all(case["shared_semantics"])
                             and all(case["eager_semantics"]),
                         "shared_total_samples_ns": shared_total,
                         "eager_total_samples_ns": eager_total})
    valid = (raw["source_stable"] and len(rows) == 12
             and all(r["semantic_isolation_pass"] for r in rows)
             and all(c["baseline_queries_exact"] for c in raw["capture"]["cells"]))
    payload = {"schema": "TypedGraphCowAttrIndexMutationV3Analysis", "integrity_pass": valid,
               "gates": {"source_stable": raw["source_stable"], "12_cells": len(rows) == 12,
                         "all_baseline_queries_exact": all(c["baseline_queries_exact"] for c in raw["capture"]["cells"]),
                         "all_branch_mutation_and_isolation_checks": all(r["semantic_isolation_pass"] for r in rows)},
               "rows": rows,
               "claim_boundary": "synthetic graph-level first-write panel; not whole-Substrate closure or natural-task prevalence"}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "integrity_pass": valid,
                      "rows": len(rows)}, indent=2))
    return 0 if valid else 1

if __name__ == "__main__": raise SystemExit(main())
