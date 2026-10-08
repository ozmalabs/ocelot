#!/usr/bin/env python3
"""Independent validation and work summary for correction-trace anchor capture."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_trace_anchor_v1.py"
CAPTURE = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_anchor_v1_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_correction_trace_anchor_v1_analysis_20261003.json"
SIZES = (1, 2, 4, 8)
ORDERS = ("ascending", "descending", "outside_in")
TARGET = "ground_definite_correction_from_scoped_action_target"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    raw = json.loads(CAPTURE.read_text())
    spec = importlib.util.spec_from_file_location("anchor_runner", RUNNER)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    current = module.locked_inputs()
    runs = raw.get("runs", [])
    cells = [cell for run in runs for cell in run.get("rows", [])]
    orders = {o: sum(run.get("scope_order") == o for run in runs) for o in ORDERS}
    per_cell = []
    for cell in cells:
        arms = cell["arms"]
        per_cell.append({
            "all_three_full_graphs_equal": len({arms[a]["canonical_graph_digest"] for a in arms}) == 1,
            "all_arms_grounded": all(arms[a]["all_grounded"] and arms[a]["all_expected_evidence"] for a in arms),
            "fallback_used_generic_multi_edge_match": arms["fallback"]["scale_counters"].get("scoped_full_fallback_rule_matches", 0) > 0,
            "anchor_path_used_for_target_rule": any(
                arms["anchor"]["target_rule_counters"].get(k, 0) > 0
                for k in ("scoped_declared_anchor", "scoped_path_declared_anchor")),
            "fallback_used_no_anchor_path": arms["fallback"]["scale_counters"].get("scoped_declared_anchor_rule_matches", 0) == 0,
        })
    checks = {
        "correct_capture_schema": raw.get("schema") == "ThoughtexperimentCorrectionTraceAnchorV1",
        "nine_fresh_processes": len({int(run["pid"]) for run in runs}) == 9,
        "three_replicates_per_order": orders == {o: 3 for o in ORDERS},
        "complete_36_cell_panel": len(cells) == 36 and sorted(int(c["n_tasks"]) for c in cells).count(1) == 9 and sorted(int(c["n_tasks"]) for c in cells).count(2) == 9 and sorted(int(c["n_tasks"]) for c in cells).count(4) == 9 and sorted(int(c["n_tasks"]) for c in cells).count(8) == 9,
        "source_lock_current": current == raw.get("locked_inputs") == raw.get("post_run_inputs"),
        "runner_hash_matches_lock": sha(RUNNER) == raw.get("locked_inputs", {}).get("evaluation/substrate_capability/thoughtexperiment_correction_trace_anchor_v1.py"),
        "all_three_arms_semantically_equal": all(row["all_three_full_graphs_equal"] and row["all_arms_grounded"] for row in per_cell),
        "fallback_and_anchor_paths_separated": all(row["fallback_used_generic_multi_edge_match"] and row["fallback_used_no_anchor_path"] and row["anchor_path_used_for_target_rule"] for row in per_cell),
        "all_runner_checks_pass": all(raw.get("checks", {}).values()),
    }
    summary = {}
    for n in SIZES:
        group = [cell for cell in cells if int(cell["n_tasks"]) == n]
        entry = {"cells": len(group), "canonical_state_parity_rate": sum(
            len({cell["arms"][arm]["canonical_graph_digest"] for arm in cell["arms"]}) == 1
            for cell in group) / len(group)}
        for arm in ("monolithic", "fallback", "anchor"):
            entry[f"{arm}_median_us"] = statistics.median(cell["arms"][arm]["elapsed_ns"] / 1000 for cell in group)
        for metric in ("cand_enum", "term_evals_total", "rule_enumerations"):
            fallback = statistics.median(cell["arms"]["fallback"]["scale_counters"].get(metric, 0) for cell in group)
            anchor = statistics.median(cell["arms"]["anchor"]["scale_counters"].get(metric, 0) for cell in group)
            entry[metric] = {"fallback_median": fallback, "anchor_median": anchor,
                             "anchor_over_fallback": anchor / fallback if fallback else None}
        summary[str(n)] = entry
    result = {"schema": "ThoughtexperimentCorrectionTraceAnchorAnalysisV1",
              "capture_sha256": sha(CAPTURE), "checks": checks,
              "cell_check_count": len(per_cell), "cell_checks": per_cell,
              "order_replicates": orders, "summary_by_task_count": summary}
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(),
        "checks": checks, "summary_by_task_count": summary}, indent=2))
    if not all(checks.values()):
        raise SystemExit("independent anchor analysis failed")


if __name__ == "__main__":
    main()
