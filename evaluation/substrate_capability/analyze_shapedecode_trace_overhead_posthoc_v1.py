#!/usr/bin/env python3
"""Post-hoc paired trace-overhead summary for the locked ShapeDecode panel.

This does not replace a preregistered instrumentation-cost experiment. It
reuses the existing five traced/untraced process pairs per cell and preserves
the small-n, one-workload boundary.
"""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/shapedecode_name_aperture_cache_v1_20261005.json"
ANALYSIS = ROOT / "evaluation/reports/shapedecode_name_aperture_cache_v1_analysis_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_cache_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_trace_overhead_posthoc_v1_20261005.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values):
    return statistics.median(values)


def main() -> int:
    capture = json.loads(CAPTURE.read_text())
    analysis = json.loads(ANALYSIS.read_text())
    lock = json.loads(LOCK.read_text())
    if analysis.get("capture_sha256") != sha(CAPTURE):
        raise SystemExit("analysis does not identify the current capture")
    if capture.get("lock_sha256") != sha(LOCK):
        raise SystemExit("capture does not identify the current source lock")

    cells: dict[tuple[int, int, str], dict[bool, dict]] = defaultdict(dict)
    pids = set()
    for row in capture["rows"]:
        case = row["case"]
        key = (int(case["size"]), int(case["replicate"]), str(case["cache_mode"]))
        traced = bool(case["trace"])
        if traced in cells[key]:
            raise SystemExit(f"duplicate arm for {key} trace={traced}")
        cells[key][traced] = row
        pids.add(int(row["pid"]))

    checks = {
        "capture_matches_independent_analysis": bool(analysis.get("passed")),
        "capture_matches_source_lock": True,
        "all_80_workers_use_distinct_pids": len(pids) == len(capture["rows"]) == 80,
        "all_40_pairs_complete": len(cells) == 40 and all(set(arms) == {False, True} for arms in cells.values()),
        "all_source_manifests_stable": all(row.get("source_stable") for row in capture["rows"]),
        "all_traces_complete": all(row["result"]["runtime_work_trace"].get("dropped", 0) == 0 for row in capture["rows"] if row["case"]["trace"]),
        "paired_outputs_and_work_match": True,
    }
    by_cell = []
    for mode in ("scan", "cached"):
        for size in sorted({key[0] for key in cells}):
            pairs = []
            for (n, rep, m), arms in sorted(cells.items()):
                if n != size or m != mode:
                    continue
                untraced, traced = arms[False]["result"], arms[True]["result"]
                # Tags encode the trace condition in this pre-existing panel;
                # compare the graph-produced semantic fields after dropping it.
                untraced_readback = {k: v for k, v in untraced["readback"].items() if k != "tag"}
                traced_readback = {k: v for k, v in traced["readback"].items() if k != "tag"}
                parity = (untraced["closure_work"] == traced["closure_work"]
                          and untraced_readback == traced_readback)
                checks["paired_outputs_and_work_match"] &= parity
                wall_ratio = traced["closure_wall_ns"] / max(1, untraced["closure_wall_ns"])
                cpu_ratio = traced["closure_cpu_ns"] / max(1, untraced["closure_cpu_ns"])
                pairs.append({
                    "replicate": rep,
                    "untraced_wall_ns": untraced["closure_wall_ns"],
                    "traced_wall_ns": traced["closure_wall_ns"],
                    "wall_ratio_trace_over_untraced": wall_ratio,
                    "wall_delta_ns": traced["closure_wall_ns"] - untraced["closure_wall_ns"],
                    "cpu_ratio_trace_over_untraced": cpu_ratio,
                    "cpu_delta_ns": traced["closure_cpu_ns"] - untraced["closure_cpu_ns"],
                    "output_and_work_equal": parity,
                })
            wall_ratios = [p["wall_ratio_trace_over_untraced"] for p in pairs]
            cpu_ratios = [p["cpu_ratio_trace_over_untraced"] for p in pairs]
            by_cell.append({
                "mode": mode,
                "effective_population": size,
                "pair_count": len(pairs),
                "median_wall_ratio_trace_over_untraced": median(wall_ratios),
                "wall_ratio_min_max": [min(wall_ratios), max(wall_ratios)],
                "median_cpu_ratio_trace_over_untraced": median(cpu_ratios),
                "cpu_ratio_min_max": [min(cpu_ratios), max(cpu_ratios)],
                "pairs": pairs,
            })

    result = {
        "schema": "ShapeDecodeTraceOverheadPosthocV1",
        "run_id": "shapedecode-trace-overhead-posthoc-v1-20261005",
        "inputs": {
            "capture_path": str(CAPTURE.relative_to(ROOT)), "capture_sha256": sha(CAPTURE),
            "analysis_path": str(ANALYSIS.relative_to(ROOT)), "analysis_sha256": sha(ANALYSIS),
            "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
            "locked_case_count": len(lock.get("cases", [])),
        },
        "checks": checks,
        "cells": by_cell,
        "interpretation": "Observed paired timing ratios for runtime-work tracing enabled versus disabled in the existing authored ShapeDecode cache workload. Five process pairs per mode/population cell are too few to estimate a stable instrumentation tax; scheduler and host noise can dominate small differences. Use this as a warning screen only, not as a corrected performance estimate.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "all_checks_pass": all(checks.values()),
                      "cell_medians": [{k: c[k] for k in ("mode", "effective_population", "pair_count", "median_wall_ratio_trace_over_untraced", "median_cpu_ratio_trace_over_untraced")} for c in by_cell]}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
