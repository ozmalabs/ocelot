#!/usr/bin/env python3
"""Validate and summarize generated-pool scale captures."""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEM = "substrate_generated_pool_scale_v1_20261001"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
OUT = ROOT / f"evaluation/reports/{STEM}_analysis.json"
TASKS = ("triangular", "square", "euler")
MAX_SIZES = {"triangular": (5, 6, 7, 8), "square": (2, 3, 4, 5), "euler": (3, 4, 5, 6)}
PROBES = (0, 1, 3, 6, 10)
REPS = range(2)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not RAW.is_file():
        raise SystemExit(f"missing raw capture: {RAW}")
    capture = json.loads(RAW.read_text())
    lock = capture["lock"]
    stale = []
    for relative, expected in lock["sources"].items():
        path = ROOT / relative
        if not path.is_file() or digest(path) != expected:
            stale.append(relative)
    binary = Path(lock["native_extension"]["path"])
    binary_current = binary.is_file() and digest(binary) == lock["native_extension"]["sha256"]
    rows = capture.get("comparisons", [])
    keyed = {(r.get("task"), r.get("max_size"), r.get("probe_count"), r.get("replicate")): r
             for r in rows}
    expected = {(task, size, probes, rep) for task in TASKS
                for size in MAX_SIZES[task] for probes in PROBES for rep in REPS}
    coverage = set(keyed) == expected
    gates = {
        "schema": capture.get("schema") == "GeneratedPoolScaleV1",
        "sources_current": not stale,
        "native_binary_current": binary_current,
        "all_scheduled_rows_recorded": capture.get("capture_complete") is True,
        "expected_factorial_coverage": coverage,
    }
    outcome_rows = []
    cell_gate_failures = []
    for key in sorted(expected):
        task, size, probes, rep = key
        row = keyed.get(key)
        if row is None:
            continue
        if "worker_error" in row:
            if not all(k in row for k in ("worker_error", "parent_wall_s")):
                cell_gate_failures.append((key, "error_shape"))
            outcome_rows.append({"task": task, "max_size": size, "probe_count": probes,
                                 "replicate": rep, "worker_error": row.get("worker_error"),
                                 "parent_wall_s": row.get("parent_wall_s")})
            continue
        complete = row.get("pool_complete") is True
        if complete != (row.get("pool_halt_reason") == "max_size"):
            cell_gate_failures.append((key, "complete_reason_mismatch"))
        if row.get("target_supported") != (row.get("target_support_count", 0) > 0):
            cell_gate_failures.append((key, "target_support_count_mismatch"))
        if row.get("probe_count") != len(row.get("probe_names", [])):
            cell_gate_failures.append((key, "probe_count_mismatch"))
        outcome_rows.append({
            "task": task, "max_size": size, "probe_count": probes, "replicate": rep,
            "halt_reason": row.get("pool_halt_reason"), "complete": complete,
            "pool_size": row.get("pool_size"), "terms_explored": row.get("terms_explored"),
            "distinct_signatures": row.get("distinct_signatures"),
            "target_support_count": row.get("target_support_count"),
            "target_supported": row.get("target_supported"),
            "synthesis_wall_s": row.get("synthesis_wall_s"),
            "synthesis_cpu_s": row.get("synthesis_cpu_s"),
            "evaluation_wall_s": row.get("evaluation_wall_s"),
            "rss_high_water_before_kib": row.get("rss_high_water_before_kib"),
            "rss_high_water_after_kib": row.get("rss_high_water_after_kib"),
            "rss_high_water_delta_kib": row.get("rss_high_water_delta_kib"),
            "parent_wall_s": row.get("parent_wall_s"),
        })
    gates["cell_record_invariants"] = not cell_gate_failures

    grouped = defaultdict(list)
    for row in outcome_rows:
        grouped[(row["task"], row["max_size"], row["probe_count"])].append(row)
    cells = []
    for (task, size, probes), group in sorted(grouped.items()):
        valid = [row for row in group if "worker_error" not in row]
        complete = [row for row in valid if row["complete"]]
        def med(field):
            values = [row[field] for row in valid if isinstance(row.get(field), (int, float))]
            return statistics.median(values) if values else None
        cells.append({
            "task": task, "max_size": size, "probe_count": probes,
            "replicates_recorded": len(group), "worker_error_count": len(group) - len(valid),
            "complete_pool_count": len(complete),
            "target_supported_count": sum(bool(row.get("target_supported")) for row in valid),
            "median_pool_size_complete_or_partial": med("pool_size"),
            "median_terms_explored": med("terms_explored"),
            "median_synthesis_wall_s": med("synthesis_wall_s"),
            "median_synthesis_cpu_s": med("synthesis_cpu_s"),
            "median_rss_high_water_kib": med("rss_high_water_after_kib"),
            "median_rss_high_water_delta_kib": med("rss_high_water_delta_kib"),
            "halt_reasons": sorted({str(row.get("halt_reason")) for row in valid}),
        })
    analysis = {
        "schema": "GeneratedPoolScaleAnalysisV1",
        "capture": str(RAW.relative_to(ROOT)), "capture_sha256": digest(RAW),
        "check_count": len(gates), "checks_passed": sum(gates.values()),
        "all_checks_pass": all(gates.values()), "gates": gates,
        "stale_sources": stale, "cell_gate_failures": cell_gate_failures,
        "scheduled_rows": len(rows), "worker_error_count": sum("worker_error" in row for row in rows),
        "rows": outcome_rows, "cells": cells,
    }
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                      "all_checks_pass": analysis["all_checks_pass"],
                      "gates": gates, "worker_error_count": analysis["worker_error_count"],
                      "cells": len(cells)}, indent=2))
    if not analysis["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
