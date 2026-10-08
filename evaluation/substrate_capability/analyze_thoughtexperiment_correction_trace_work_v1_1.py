#!/usr/bin/env python3
"""Descriptive work-count analysis of the locked correction trace capture."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_partition_v1_1_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_work_v1_1_20261003.json"
SIZES = (1, 2, 4, 8)
METRICS = ("cand_enum", "term_evals_total", "rule_enumerations",
           "where_evals", "rule_effect_attr_set_attempts")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(CAPTURE.read_text())
    cells = [cell for run in raw["runs"] for cell in run["rows"]]
    checks = {
        "capture_source_stable": raw["locked_inputs"] == raw["post_run_inputs"],
        "capture_integrity_gates_pass": all(raw["checks"].values()),
        "all_36_cells_present": len(cells) == 36,
        "all_scoped_graphs_match_monolithic": all(
            cell["paired"]["canonical_full_graph_equal"] for cell in cells),
    }
    summary = {}
    for n in SIZES:
        group = [cell for cell in cells if int(cell["n_tasks"]) == n]
        metrics = {}
        for metric in METRICS:
            mono = [int(cell["monolithic"]["scale_counters"].get(metric, 0)) for cell in group]
            scoped = [int(cell["scoped"]["scale_counters"].get(metric, 0)) for cell in group]
            m, s = statistics.median(mono), statistics.median(scoped)
            metrics[metric] = {"monolithic_median": m, "scoped_median": s,
                               "scoped_over_monolithic": (s / m if m else None)}
        summary[str(n)] = {"cells": len(group), "frames": 2 * n,
                           "median_nodes": statistics.median(cell["scoped"]["node_count"] for cell in group),
                           "median_scoped_calls": statistics.median(cell["scoped"]["scope_calls"] for cell in group),
                           "metrics": metrics}
    result = {"schema": "ThoughtexperimentCorrectionTraceWorkAnalysisV1",
              "capture_sha256": sha(CAPTURE), "checks": checks,
              "claim_boundary": "Descriptive medians recomputed from the source-locked capture. Candidate and Term counts show repeated full-graph work under frame-by-frame scoped sweeps; they do not establish asymptotic complexity or natural-task prevalence.",
              "summary_by_task_count": summary}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(),
                      "checks": checks, "summary_by_task_count": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("work-count analysis failed")


if __name__ == "__main__":
    main()
