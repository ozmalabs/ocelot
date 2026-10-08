#!/usr/bin/env python3
"""Independent integrity and summary analysis for CAN grid width sweep."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/can_grid_boundary_width_scale_v1_2_20260929.json"
LOCK = ROOT / "evaluation/substrate_capability/can_grid_boundary_width_scale_v1_2_lock_20260929.json"
RUNNER = ROOT / "evaluation/substrate_capability/can_grid_boundary_width_scale_v1.py"
OUT = CAPTURE.with_name("can_grid_boundary_width_scale_v1_2_20260929_analysis.json")


def main() -> None:
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    spec = importlib.util.spec_from_file_location("grid_runner", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    live_lock = runner.input_lock()
    assert capture["input_lock"] == capture["post_run_input_lock"] == lock == live_lock
    rows = capture["runs"]
    assert len(rows) == 54
    assert all(capture["checks"].values())
    cells = []
    for q in runner.WIDTHS:
        for m in runner.LENGTHS:
            group = [row for row in rows if row["width"] == q and row["length"] == m]
            assert len(group) == runner.REPLICATES
            cells.append({"width": q, "length": m, "nodes": q*m,
                          "replicates": len(group),
                          "median_junction_tree_ns": int(__import__("statistics").median(
                              row["timing_ns"]["junction_tree_minfill"] for row in group)),
                          "median_fixed_order_junction_tree_ns": int(__import__("statistics").median(
                              row["timing_ns"]["junction_tree_fixed_order"] for row in group)),
                          "median_min_fill_ns": int(__import__("statistics").median(
                              row["timing_ns"]["min_fill_order"] for row in group)),
            "median_oracle_operations": int(__import__("statistics").median(
                              row["oracle_operations"] for row in group)),
                          "median_minfill_width": int(__import__("statistics").median(
                              row["reported_treewidth"] for row in group)),
                          "median_minfill_width_overhead": int(__import__("statistics").median(
                              row["reported_treewidth"] - q for row in group)),
                          "median_traced_peak_bytes": int(__import__("statistics").median(
                              row["traced_peak_bytes"]["minfill"] for row in group))})
    analysis = {"schema_version": 1,
                "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
                "lock_matches_live_inputs": True, "worker_count": len(rows),
                "correctness_gate_count": len(capture["checks"]),
                "all_correctness_gates_pass": all(capture["checks"].values()),
                "claim_boundary": capture["claim_boundary"], "cells": cells}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(),
                      "workers": len(rows), "gates": analysis["correctness_gate_count"],
                      "all_pass": analysis["all_correctness_gates_pass"]}, indent=2))


if __name__ == "__main__":
    main()
