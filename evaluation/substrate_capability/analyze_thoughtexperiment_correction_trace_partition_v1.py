#!/usr/bin/env python3
"""Independent integrity and semantic audit of the correction-trace capture."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_trace_partition_v1.py"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_partition_v1_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_partition_v1_analysis_20261003.json"
SIZES = (1, 2, 4, 8)
ORDERS = ("ascending", "descending", "outside_in")
EVIDENCE = "CommunicationInterpretation -> discourse-scoped DiscourseState -> prior grounded DiscourseEvent -> matching action-target head"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(CAPTURE.read_text())
    spec = importlib.util.spec_from_file_location("correction_trace_runner", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    current = module.locked_inputs()
    runs = raw.get("runs", [])
    flattened = [(run, cell) for run in runs for cell in run.get("rows", [])]
    pids = {int(run["pid"]) for run in runs}
    order_counts = {order: sum(run.get("scope_order") == order for run in runs) for order in ORDERS}
    all_cases = len(flattened) == len(SIZES) * len(ORDERS) * 3
    cell_checks = []
    for run, cell in flattened:
        n = int(cell["n_tasks"])
        mono, scoped = cell["monolithic"], cell["scoped"]
        cell_checks.append({
            "worker_size_matches": n in SIZES,
            "task_count_matches_both_arms": mono["n_tasks"] == scoped["n_tasks"] == n,
            "canonical_full_graph_equal": mono["graph_digest"] == scoped["graph_digest"],
            "every_expected_correction_grounded": (
                mono["all_grounded"] and scoped["all_grounded"]
                and len(mono["grounding_statuses"]) == n
                and len(scoped["grounding_statuses"]) == n
                and all(x == "candidate_grounded" for x in mono["grounding_statuses"] + scoped["grounding_statuses"])),
            "evidence_paths_exact": (mono["all_expected_evidence"] and scoped["all_expected_evidence"]
                                     and all(x == EVIDENCE for x in mono["evidence_paths"] + scoped["evidence_paths"])),
            "scope_ownership_count": scoped["frame_count"] == 2 * n and scoped["owned_nodes_per_frame"] == 4,
            "scope_queue_quiescent": (len(scoped["quiescence"]) == 2 * n
                                       and all(q["progress_steps"] == 0 and not q["deferred_effects_pending"] for q in scoped["quiescence"])),
        })
    checks = {
        "capture_schema": raw.get("schema") == "ThoughtexperimentCorrectionTracePartitionV1",
        "nine_unique_processes": len(pids) == 9,
        "three_replicates_per_sweep_order": order_counts == {o: 3 for o in ORDERS},
        "complete_36_cell_panel": all_cases and sorted(int(c["n_tasks"]) for _, c in flattened).count(1) == 9
            and sorted(int(c["n_tasks"]) for _, c in flattened).count(2) == 9
            and sorted(int(c["n_tasks"]) for _, c in flattened).count(4) == 9
            and sorted(int(c["n_tasks"]) for _, c in flattened).count(8) == 9,
        "source_locks_current": current == raw.get("locked_inputs") == raw.get("post_run_inputs"),
        "runner_matches_locked_hash": sha(RUNNER) == raw.get("locked_inputs", {}).get("evaluation/substrate_capability/thoughtexperiment_correction_trace_partition_v1.py"),
        "all_cell_checks": all(all(row.values()) for row in cell_checks),
        "all_runner_gates_pass": all(raw.get("checks", {}).values()),
    }
    summaries = {}
    for n in SIZES:
        group = [cell for _, cell in flattened if int(cell["n_tasks"]) == n]
        mt = [cell["monolithic"]["elapsed_ns"] / 1000 for cell in group]
        st = [cell["scoped"]["elapsed_ns"] / 1000 for cell in group]
        summaries[str(n)] = {
            "cells": len(group),
            "canonical_graph_parity_rate": sum(cell["monolithic"]["graph_digest"] == cell["scoped"]["graph_digest"] for cell in group) / len(group),
            "valid_semantics_rate": sum(cell["paired"]["expected_results"] for cell in group) / len(group),
            "median_monolithic_us": statistics.median(mt),
            "median_scoped_us": statistics.median(st),
            "median_scoped_monolithic_ratio": statistics.median(st) / statistics.median(mt),
        }
    result = {"schema": "ThoughtexperimentCorrectionTracePartitionAnalysisV1",
              "capture_sha256": sha(CAPTURE), "checks": checks,
              "cell_check_count": len(cell_checks), "cell_checks": cell_checks,
              "order_replicates": order_counts, "summary_by_task_count": summaries}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(),
                      "checks": checks, "summary_by_task_count": summaries}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent analysis failed")


if __name__ == "__main__":
    main()
