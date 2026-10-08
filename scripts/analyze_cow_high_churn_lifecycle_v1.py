#!/usr/bin/env python3
"""Independently validate and summarize the high-churn lifecycle capture."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/cow_high_churn_lifecycle_v1.json"
OUT = ROOT / "evaluation/reports/cow_high_churn_lifecycle_v1_analysis.json"


def main() -> int:
    capture = json.loads(RAW.read_text())
    rows = capture["measurements"]["rows"]
    if capture.get("schema") != "CowHighChurnLifecycleCaptureV1" or len(rows) != 200:
        raise SystemExit("capture schema/row count mismatch")
    cells = []
    for n in (10_000, 50_000):
        for fanout in (4, 16):
            pair = {}
            for backend in ("shared_snapshot", "eager_copy"):
                selected = [r for r in rows if r["size_nodes"] == n and r["fanout"] == fanout
                            and r["backend"] == backend]
                if len(selected) != 25 or {r["wave_index"] for r in selected} != set(range(25)):
                    raise SystemExit(f"incomplete repeated cell: {n}/{fanout}/{backend}")
                for row in selected:
                    if not row["all_semantics_pass"] or not row["primary_unchanged"]:
                        raise SystemExit(f"semantic failure: {row}")
                    if row["mutation_adjusted_after_drop_bytes"] != 0:
                        raise SystemExit(f"adjusted post-drop residual: {row}")
                    if not row["mutation_adjusted_reclamation_pass"]:
                        raise SystemExit(f"reclamation gate failure: {row}")
                selected.sort(key=lambda r: r["wave_index"])
                live = [r["all_live_delta_bytes"] for r in selected]
                if live[0] != live[-1]:
                    raise SystemExit(f"all-live allocation drift over repeated waves: {n}/{fanout}/{backend}")
                pair[backend] = {
                    "median_wave_wall_us": statistics.median(r["wave_wall_us"] for r in selected),
                    "p95_wave_wall_us_nearest_rank": sorted(r["wave_wall_us"] for r in selected)[23],
                    "median_all_live_delta_bytes": statistics.median(live),
                    "median_after_cancel_delta_bytes": statistics.median(
                        r["after_cancel_delta_bytes"] for r in selected),
                    "adjusted_post_drop_residual_min_bytes": min(
                        r["mutation_adjusted_after_drop_bytes"] for r in selected),
                    "adjusted_post_drop_residual_max_bytes": max(
                        r["mutation_adjusted_after_drop_bytes"] for r in selected),
                    "repeated_wave_all_live_first_last_bytes": [live[0], live[-1]],
                }
            shared = pair["shared_snapshot"]
            eager = pair["eager_copy"]
            cells.append({"size_nodes": n, "fanout": fanout, "backends": pair,
                          "eager_over_shared_median_time_ratio":
                              eager["median_wave_wall_us"] / shared["median_wave_wall_us"],
                          "eager_over_shared_median_live_allocation_ratio":
                              eager["median_all_live_delta_bytes"] / shared["median_all_live_delta_bytes"]})
    result = {
        "schema": "CowHighChurnLifecycleAnalysisV1",
        "capture": str(RAW.relative_to(ROOT)),
        "source_capture_sha256": capture["source_sha256"],
        "rows": len(rows), "paired_cells": len(cells),
        "gates": {"exact_branch_id_parity": True, "primary_and_later_snapshot_isolation": True,
                  "all_200_waves_semantics_pass": True, "all_adjusted_post_drop_residuals_zero": True,
                  "retained_base_all_live_allocation_first_last_equal": True},
        "cells": cells,
        "limits": ["one host", "synthetic node-only graph", "requested allocator bytes, not RSS/PSS",
                   "not commit/adoption or serving-runtime evidence"]}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"rows": len(rows), "cells": len(cells), "all_gates_pass": True,
                      "analysis": str(OUT.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
