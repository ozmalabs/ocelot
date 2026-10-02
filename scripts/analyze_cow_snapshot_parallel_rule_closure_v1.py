#!/usr/bin/env python3
"""Validate and summarize the native CoW rule-closure panel."""
import json, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/cow_snapshot_parallel_rule_closure_v1.json"
OUT = ROOT / "evaluation/reports/cow_snapshot_parallel_rule_closure_v1_analysis.json"

def median(xs):
    return statistics.median(xs)

def main():
    capture = json.loads(RAW.read_text())
    rows = capture["measurements"]
    assert len(rows) == 45, f"expected 45 fresh-process rows, got {len(rows)}"
    assert len({r["worker_pid"] for r in rows}) == 45, "workers must be fresh processes"
    grouped = defaultdict(list)
    for r in rows:
        assert r["all_semantic_gates_pass"], "semantic/isolation gate failed"
        assert r["primary_unchanged"] and r["later_forks_see_captured_base"]
        assert sorted(r["arms"]) == ["cow_concurrent", "cow_serial", "eager_concurrent", "eager_serial"]
        assert len(r["arm_order"]) == 4 and len(set(r["arm_order"])) == 4
        for arm in r["arms"].values():
            assert len(arm["branch_fork_us"]) == r["fanout"]
            assert len(arm["closure_us"]) == r["fanout"]
        grouped[(r["size_nodes"], r["fanout"])].append(r)
    summaries = []
    for (size, fanout), cell in sorted(grouped.items()):
        assert len(cell) == 5
        metrics = {}
        for arm in ("cow_serial", "cow_concurrent", "eager_serial", "eager_concurrent"):
            metrics[arm + "_wall_us_median"] = median([x["arms"][arm]["wall_us"] for x in cell])
        for kind in ("cow", "eager"):
            metrics[kind + "_memory_live_pss_bytes_median"] = median(
                [x["memory"][kind]["fanout_live_delta"]["Pss_bytes"] for x in cell])
            metrics[kind + "_memory_dropped_pss_bytes_median"] = median(
                [x["memory"][kind]["fanout_dropped_delta"]["Pss_bytes"] for x in cell])
        summaries.append({"size_nodes": size, "fanout": fanout, "repeats": len(cell), **metrics})
    cow_parallel_wins = sum(s["cow_concurrent_wall_us_median"] < s["cow_serial_wall_us_median"] for s in summaries)
    eager_parallel_wins = sum(s["eager_concurrent_wall_us_median"] < s["eager_serial_wall_us_median"] for s in summaries)
    report = {
        "schema": "CowSnapshotParallelRuleClosureAnalysisV1",
        "raw_sha256": "sha256:" + __import__("hashlib").sha256(RAW.read_bytes()).hexdigest(),
        "gates": {"rows": len(rows), "fresh_worker_pids": len({r["worker_pid"] for r in rows}),
                  "cells": len(summaries), "all_semantic_gates_pass": True,
                  "all_cells_five_repeats": all(s["repeats"] == 5 for s in summaries)},
        "parallel_wall_median_wins_of_9_cells": {"cow": cow_parallel_wins, "eager": eager_parallel_wins},
        "cells": summaries,
        "interpretation_limits": [
            "Synthetic one-rule additive closure on a ring graph and one Linux host.",
            "Outer independent-branch concurrency only; the AddEdge rule is not batch_safe under the engine access analysis.",
            "PSS is process-level proportional accounting, not precise object ownership or proof of allocator reclamation.",
            "No serving API, vLLM-style scheduler, request batching, or open-ended experiment utility is measured.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"gates": report["gates"], "wins": report["parallel_wall_median_wins_of_9_cells"], "analysis": str(OUT.relative_to(ROOT))}, indent=2))

if __name__ == "__main__":
    main()
