#!/usr/bin/env python3
"""Analyze the locked production treewidth-gate relabelling panel."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/can_production_treewidth_gate_relabelling_v1_1_20260929.json"
LOCK = ROOT / "evaluation/substrate_capability/can_production_treewidth_gate_relabelling_v1_1_lock_20260929.json"
RUNNER = ROOT / "evaluation/substrate_capability/can_production_treewidth_gate_relabelling_v1.py"
OUT = ROOT / "evaluation/reports/can_production_treewidth_gate_relabelling_v1_20260929_analysis.json"


def main() -> None:
    cap = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    spec = importlib.util.spec_from_file_location("gate_runner", RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    assert cap["input_lock"] == cap["post_run_input_lock"] == lock == runner.input_lock()
    assert len(cap["runs"]) == 72 and all(cap["checks"].values())
    rows = cap["runs"]
    by_width = []
    for q in runner.WIDTHS:
        group = [r for r in rows if r["width"] == q]
        accepted = [r for r in group if r["attempted"]]
        by_width.append({"width": q, "replicates": len(group), "accepted": len(accepted),
                         "refused": len(group)-len(accepted),
                         "median_reported_treewidth": statistics.median(
                             r["reported_treewidth"] for r in group),
                         "median_wall_ms": statistics.median(r["wall_ns"] for r in group)/1e6,
                         "false_refusals_at_default_bound": sum(
                             not r["attempted"] for r in group if q <= runner.BOUND),
                         "unsafe_acceptances": sum(r["attempted"] for r in group if q > runner.BOUND)})
    analysis = {"schema_version": 1,
                "capture_sha256": hashlib.sha256(CAPTURE.read_bytes()).hexdigest(),
                "lock_matches_live_inputs": True, "worker_count": len(rows),
                "integrity_gates_pass": all(cap["checks"].values()),
                "false_refusals_within_default_bound": sum(
                    x["false_refusals_at_default_bound"] for x in by_width),
                "unsafe_acceptances_above_default_bound": sum(
                    x["unsafe_acceptances"] for x in by_width),
                "by_width": by_width,
                "claim_boundary": cap["claim_boundary"]}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": OUT.relative_to(ROOT).as_posix(),
                      "workers": len(rows), "false_refusals": analysis["false_refusals_within_default_bound"],
                      "unsafe_acceptances": analysis["unsafe_acceptances_above_default_bound"]}, indent=2))


if __name__ == "__main__":
    main()
