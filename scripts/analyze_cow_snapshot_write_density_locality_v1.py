#!/usr/bin/env python3
"""Validate and summarize CoW write-density/locality measurements."""
import hashlib, json, statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/cow_snapshot_write_density_locality_v1.json"
OUT = ROOT / "evaluation/reports/cow_snapshot_write_density_locality_v1_analysis.json"

def med(xs):
    return statistics.median(xs)

def main():
    capture = json.loads(RAW.read_text())
    rows = capture["measurements"]
    assert len(rows) == 70, f"expected 70 workers, got {len(rows)}"
    assert len({r["worker_pid"] for r in rows}) == 70
    grouped = defaultdict(list)
    for row in rows:
        assert row["all_semantic_gates_pass"] and row["primary_unchanged"] and row["later_forks_see_captured_base"]
        assert row["fanout"] == 4
        active = row["active_edges"]
        assert 1 <= active <= row["size_nodes"]
        expected_order = (["cow_serial", "cow_concurrent", "eager_serial", "eager_concurrent"]
                          if row["repeat_index"] % 2 == 0 else
                          ["eager_concurrent", "eager_serial", "cow_concurrent", "cow_serial"])
        assert row["arm_order"] == expected_order
        assert len(row["arms"]) == 4
        for arm in row["arms"].values():
            assert len(arm["branch_fork_us"]) == 4 and len(arm["closure_us"]) == 4
        grouped[(row["size_nodes"], row["active_edges"], row["locality"])].append(row)
    cells = []
    for (size, active, locality), cell in sorted(grouped.items()):
        assert len(cell) == 5, f"incomplete cell {size}/{active}/{locality}: {len(cell)}"
        record = {"size_nodes": size, "active_edges": active, "density": active / size,
                  "locality": locality, "repeats": 5}
        for arm in ("cow_serial", "cow_concurrent", "eager_serial", "eager_concurrent"):
            record[arm + "_wall_us_median"] = med([r["arms"][arm]["wall_us"] for r in cell])
            record[arm + "_branch_fork_us_median"] = med(
                [value for r in cell for value in r["arms"][arm]["branch_fork_us"]])
            record[arm + "_branch_closure_us_median"] = med(
                [value for r in cell for value in r["arms"][arm]["closure_us"]])
        for kind in ("cow", "eager"):
            for moment in ("one_branch_live", "one_branch_dropped", "fanout_live", "fanout_dropped"):
                record[kind + "_" + moment + "_pss_delta_bytes_median"] = med(
                    [r["memory"][kind][moment + "_delta"]["Pss_bytes"] for r in cell])
        cells.append(record)
    assert len(cells) == 14
    expected_keys = set()
    for size in (10771, 50771):
        for density in (0.01, 0.10, 0.50):
            active = int(size * density)
            expected_keys.update(((size, active, "contiguous"), (size, active, "spread")))
        expected_keys.add((size, size, "contiguous"))
    assert set(grouped) == expected_keys, "measured cells do not match the preregistered factorial"
    interactions = []
    for size in (10771, 50771):
        for density in (0.01, 0.10, 0.50):
            # Compare matched sparse-count treatments' PSS to report placement sensitivity.
            contiguous = min((c for c in cells if c["size_nodes"] == size and c["locality"] == "contiguous"
                              and abs(c["density"] - density) < 0.005), key=lambda c: abs(c["density"] - density))
            spread = min((c for c in cells if c["size_nodes"] == size and c["locality"] == "spread"
                          and abs(c["density"] - density) < 0.005), key=lambda c: abs(c["density"] - density))
            interactions.append({"size_nodes": size, "density_target": density,
                "cow_fanout_live_pss_contiguous_minus_spread_bytes": contiguous["cow_fanout_live_pss_delta_bytes_median"] - spread["cow_fanout_live_pss_delta_bytes_median"],
                "eager_fanout_live_pss_contiguous_minus_spread_bytes": contiguous["eager_fanout_live_pss_delta_bytes_median"] - spread["eager_fanout_live_pss_delta_bytes_median"],
                "cow_concurrent_wall_contiguous_minus_spread_us": contiguous["cow_concurrent_wall_us_median"] - spread["cow_concurrent_wall_us_median"]})
    report = {"schema": "CowSnapshotWriteDensityLocalityAnalysisV1",
        "raw_sha256": "sha256:" + hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "gates": {"workers": len(rows), "unique_worker_pids": len({r["worker_pid"] for r in rows}),
                  "complete_cells": len(cells), "five_repeats_every_cell": all(c["repeats"] == 5 for c in cells),
                  "all_semantic_and_isolation_gates_pass": True},
        "locality_contrasts": interactions,
        "cells": cells,
        "limits": ["Synthetic ring graph and one additive rule on one host.",
                   "The active input edge type selects writes; contiguous/spread describes graph-index key locality, not measured allocator page placement.",
                   "The AddEdge rule is not batch_safe; this is outer branch concurrency only.",
                   "PSS is process-level proportional accounting and cannot identify heap ownership or guarantee reclamation.",
                   "No natural task frequency, shared-live-substrate mutation, or serving integration is measured."]}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"gates": report["gates"], "cells": len(cells), "analysis": str(OUT.relative_to(ROOT))}, indent=2))

if __name__ == "__main__":
    main()
